import os
import sys
import hmac
from fastapi import FastAPI, Depends, Header, HTTPException, Body
from hdwallet import HDWallet
from hdwallet.entropies import BIP39Entropy, BIP39_ENTROPY_STRENGTHS
from hdwallet.mnemonics import (
    BIP39Mnemonic, BIP39_MNEMONIC_LANGUAGES
)
from hdwallet.cryptocurrencies import Tron as Cryptocurrency
from hdwallet.hds import BIP32HD
from hdwallet.derivations import BIP44Derivation
from hdwallet.const import PUBLIC_KEY_TYPES
from hdwallet.seeds import BIP39Seed
import tronpy
from tronpy import Tron
from tronpy.exceptions import AddressNotFound
from tronpy.keys import PrivateKey
from tronpy.providers import HTTPProvider
from tronpy.keys import is_base58check_address, to_base58check_address
import datetime
import httpx
from decimal import Decimal
import asyncio
from collections import defaultdict

app = FastAPI()

# Per-user locks to prevent TOCTOU race conditions on balance check-then-transfer.
# WARNING: asyncio.Lock only works within a single process. This service MUST be
# deployed with a single worker (e.g., uvicorn --workers 1). If multi-worker
# deployment is needed, replace with a Redis distributed lock (redis.lock.Lock).
_user_locks: dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

# Load secrets
WALLET_API_KEY_FILE = os.environ.get('WALLET_API_KEY_FILE', None)
MNEMONIC_FILE = os.environ.get('MNEMONIC_FILE', None)
TRON_GRID_API_KEY = os.environ.get('TRON_GRID_API_KEY', '')
USDT_CONTRACT_ADDRESS = os.environ.get('USDT_CONTRACT_ADDRESS', 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t')
DUST_THRESHOLD = float(os.environ.get('DUST_THRESHOLD', '0.1'))
TRONGRID_TX_LIMIT = int(os.environ.get('TRONGRID_TX_LIMIT', '200'))

# Validate required environment variables at startup
_missing_vars = []
if not WALLET_API_KEY_FILE:
    _missing_vars.append('WALLET_API_KEY_FILE')
if not MNEMONIC_FILE:
    _missing_vars.append('MNEMONIC_FILE')
if _missing_vars:
    print(f"ERROR: Required environment variables are not set: {', '.join(_missing_vars)}", file=sys.stderr)
    sys.exit(1)

# For Deploy
with open(WALLET_API_KEY_FILE, 'r') as f:
    WALLET_API_KEY = f.read().strip()

with open(MNEMONIC_FILE, 'r') as f:
    MNEMONIC_PHRASE = f.read().strip()


# # For Testing
# WALLET_API_KEY = 'test'
# MNEMONIC_PHRASE = ''


# Initialize tron client
tron = Tron(HTTPProvider(api_key=TRON_GRID_API_KEY))

async def get_datetime(timestamp):
        try:
            return datetime.datetime.utcfromtimestamp(timestamp/1000)
        except Exception as e:
            # print("Future timestamp means transaction is malicious", e)
            return None

async def get_hd_wallet():
    # Initialize master HDWallet inside the function to prevent HDWallet object from being shared between requests
    hd_wallet = HDWallet(
            cryptocurrency=Cryptocurrency,
            hd=BIP32HD,
            network=Cryptocurrency.NETWORKS.MAINNET,
            language=BIP39_MNEMONIC_LANGUAGES.ENGLISH,
            passphrase=None,
            public_key_type=PUBLIC_KEY_TYPES.COMPRESSED,
        ).from_mnemonic(
        mnemonic=BIP39Mnemonic(
            mnemonic=MNEMONIC_PHRASE
        )
    )
    return hd_wallet

async def get_private_key_from_user_id(user_id: int):
    hd_wallet = await get_hd_wallet()
    user_wallet = hd_wallet.from_derivation(
        derivation=BIP44Derivation(
            coin_type=195,  # Tron coin type as per SLIP-0044
            account=0,
            change=0,
            address=user_id
        )
    )
    return user_wallet.private_key()
    
async def get_address_from_user_id(user_id: int):
    # Initialize master HDWallet inside the function to prevent HDWallet object from being shared between requests
    hd_wallet = await get_hd_wallet()
    # Derive child wallet for the user
    user_wallet = hd_wallet.from_derivation(
        derivation=BIP44Derivation(
            coin_type=195,  # Tron coin type as per SLIP-0044
            account=0,
            change=0,
            address=user_id
        )
    )
    return user_wallet.address()

async def get_user_trx_balance(user_id: int):
    address = await get_address_from_user_id(user_id)
    try:
        balance = await asyncio.to_thread(tron.get_account_balance, address)
        return balance
    except AddressNotFound:
        return 0

async def get_user_usdt_balance(user_id: int):
    address = await get_address_from_user_id(user_id)

    def _fetch_usdt_balance():
        usdt_contract = tron.get_contract(USDT_CONTRACT_ADDRESS)
        return float(usdt_contract.functions.balanceOf(address) / tronpy.TRX)

    usdt_balance = await asyncio.to_thread(_fetch_usdt_balance)
    return usdt_balance

async def transact_tron_network(user_id: int, asset: str, amount: float, to_address: str):
    # Verify if the asset is valid
    if asset not in ["TRX", "USDT"]:
        raise HTTPException(status_code=400, detail="Invalid asset")

    # Verify if the to_address is valid
    if not is_base58check_address(to_address):
        raise HTTPException(status_code=400, detail="Invalid address")

    # Verify if the amount is valid
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    # Acquire per-user lock to prevent TOCTOU race between balance check and transfer
    async with _user_locks[user_id]:
        return await _execute_transfer(user_id, asset, amount, to_address)


async def _execute_transfer(user_id: int, asset: str, amount: float, to_address: str):
    # Verify if the user has enough balance
    if asset == "TRX":
        user_balance = await get_user_trx_balance(user_id)
    else:
        user_balance = await get_user_usdt_balance(user_id)

    if user_balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")

    private_key = PrivateKey(bytes.fromhex(await get_private_key_from_user_id(user_id)))
    user_address = await get_address_from_user_id(user_id)

    # Send the transaction
    # Use Decimal for precise financial arithmetic
    amount_decimal = Decimal(str(amount))
    amount_sun = int(amount_decimal * Decimal('1000000'))

    def _build_and_broadcast():
        if asset == "TRX":
            txn = (
                tron.trx.transfer(
                user_address,
                to_address,
                amount_sun
            ).build()
            .sign(private_key)
            )
        else:
            usdt_contract = tron.get_contract(USDT_CONTRACT_ADDRESS)
            txn = (
                usdt_contract.functions.transfer(
                to_address,
                amount_sun
            ).with_owner(user_address)
            .fee_limit(50_000_000)
            .build()
            .sign(private_key)
            )
        return tron.broadcast(txn)

    try:
        response = await asyncio.to_thread(_build_and_broadcast)
        if response["result"]:
            response["user_address"] = user_address
            response["to_address"] = to_address
            return response
        else:
            raise HTTPException(status_code=500, detail="Transaction broadcast failed")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Transaction failed due to an internal error")
    
async def fetch_parse_trx_data(address, deposit_only=False):
    """Interpret the transaction data and extract required fields asynchronously."""
    transactions = []
    params = {
        "only_to": deposit_only,
        "limit": TRONGRID_TX_LIMIT,
    }

    # Use httpx for asynchronous HTTP requests
    trongrid_headers = {"TRON-PRO-API-KEY": TRON_GRID_API_KEY} if TRON_GRID_API_KEY else {}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.trongrid.io/v1/accounts/{address}/transactions", params=params, headers=trongrid_headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

    transaction_data_to_parse = data.get('data', [])
    for txn in transaction_data_to_parse:
        txid = txn["txID"]
        # Get the raw data of the transaction
        raw_data = txn['raw_data']

        # The transaction may have multiple contracts; we assume one here
        contract = raw_data['contract'][0]
        timestamp = raw_data.get('timestamp')

        if contract['type'] == 'TransferContract':  # TRX
            # Get the sender address
            from_address = to_base58check_address(contract['parameter']['value']['owner_address'])

            # Get the recipient address
            to_address = to_base58check_address(contract['parameter']['value']['to_address'])

            # Get the amount
            amount = contract['parameter']['value']['amount'] / 1_000_000  # TRX has 6 decimals
            asset = "TRX"
        else:
            continue

        txn_datetime = await get_datetime(timestamp)
        if txn_datetime is None:
            continue
        if asset == "TRX" and amount < DUST_THRESHOLD:
            # Consider it's a dust attack
            continue

        # Append parsed transaction
        transactions.append({
            "from_address": from_address,
            "to_address": to_address,
            "asset": asset,
            "amount": amount,
            "txid": txid,
            "datetime": txn_datetime
        })

    return transactions

async def fetch_parse_usdt_data(address, deposit_only=False):
    """Interpret the transaction data and extract required fields asynchronously."""
    transactions = []
    
    params = {
        "only_to": deposit_only,
        "limit": TRONGRID_TX_LIMIT,
    }

    # Use httpx for asynchronous HTTP requests
    trongrid_headers = {"TRON-PRO-API-KEY": TRON_GRID_API_KEY} if TRON_GRID_API_KEY else {}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.trongrid.io/v1/accounts/{address}/transactions/trc20", params=params, headers=trongrid_headers)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

    transaction_data_to_parse = data.get('data', [])
    for txn in transaction_data_to_parse:
        if txn['type'] != "Transfer":
            continue
        txid = txn["transaction_id"]
        to_address = txn["to"]
        asset = txn['token_info']['symbol']
        if asset != "USDT":
            continue
        from_address = txn["from"]
        block_datetime = await get_datetime(txn["block_timestamp"])
        if block_datetime is None:
            continue
        amount = float(txn["value"]) / 1_000_000
        
        if amount < DUST_THRESHOLD:
            # Consider it's a dust attack
            continue
        
        transactions.append({
            "owner_address": address,
            "from_address": from_address,
            "to_address": to_address,
            "asset": asset,
            "amount": amount,
            "txid": txid,
            "datetime": block_datetime
        })
    return transactions

# Authentication dependency
async def verify_api_key(x_api_key: str = Header(...)):
    if not hmac.compare_digest(x_api_key, WALLET_API_KEY):
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/user_wallet/{user_id}")
async def generate_wallet(user_id: int, api_key: str = Depends(verify_api_key)):
    address = await get_address_from_user_id(user_id)
    data = {"address": address}
    return data

@app.get("/user_wallet/balance/{user_id}")
async def get_balance(user_id: int, asset: str, api_key: str = Depends(verify_api_key)):
    if asset not in ["USDT", "TRX"]:
        raise HTTPException(status_code=400, detail="Invalid asset")
    if asset == "USDT":
        balance = await get_user_usdt_balance(user_id)
    else:
        balance = await get_user_trx_balance(user_id)
        
    balance_dict = {"asset": asset, "balance": balance}
    return balance_dict
    
@app.post("/user_wallet/transfer")
async def transfer_asset(user_id: int = Body(...),
                         to_address: str = Body(...),
                         asset: str = Body(...),
                         amount: float = Body(...),
                         api_key: str = Depends(verify_api_key)):
    response = await transact_tron_network(user_id, asset, amount, to_address)
    return response

@app.get("/user_wallet/transactions/{user_id}")
async def get_user_transactions(user_id: int,
                                asset: str,
                                deposit_only: bool = True,
                                api_key: str = Depends(verify_api_key)):
    try:
        if asset == "USDT":
            transactions = await fetch_parse_usdt_data(await get_address_from_user_id(user_id), deposit_only)
        elif asset == "TRX":
            transactions = await fetch_parse_trx_data(await get_address_from_user_id(user_id), deposit_only)
        else:
            raise HTTPException(status_code=400, detail="Invalid asset")
        
        # # For Testing
        # # Dummy transactions
        # owner_address = await get_address_from_user_id(user_id)
        # transactions = [
        #     {
        #         "owner_address": owner_address,
        #         "from_address": "test_from1",
        #         "to_address": owner_address,
        #         "asset": "USDT",
        #         "amount": 11,
        #         "txid": "test_txid1",
        #         "datetime": datetime.datetime.now()
        #     },
        # ]
        
        
        return transactions
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to fetch transactions due to an internal error")