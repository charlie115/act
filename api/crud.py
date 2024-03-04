import random
import json
from fastapi import HTTPException
from fastapi import status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from uuid import UUID
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import models, schemas
from utils import encrypt_data, decrypt_data, find_api_keys
from decorators import handle_db_exceptions
from database import engine
import datetime
from exchange_plugin.integrated_plug import UserExchangeAdaptor

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logging_dir = f"{upper_dir}/loggers/logs/"
# Read config
config_dir = f"{upper_dir}/trade_core_config.json"
with open(config_dir) as f:
    config = json.load(f)
if not os.path.exists(logging_dir):
    os.mkdir(logging_dir)
# if node not in config['node_settings'].keys():
#     raise Exception(f"Node name should be the one of {list(config['node_settings'].keys())}")
node = config['node']
monitor_bot_name = config['monitor_setting']['monitor_bot']
monitor_bot_token = config['telegram_bot_setting'][monitor_bot_name]
monitor_bot_api_url = config['monitor_setting']['monitor_bot_api_url']
admin_telegram_id = config['telegram_admin_id']['charlie1155']

# initialize exchange adaptors
user_exchange_adaptor = UserExchangeAdaptor(admin_telegram_id=admin_telegram_id, logging_dir=upper_dir+logging_dir)

# Dependency to get the async database session
async def get_db():
    async with AsyncSession(engine) as session:
        yield session

async def get_all_trade_configs(user: UUID, target_market_code: str, origin_market_code: str, db: AsyncSession):
    if user:
        query = select(models.TradeConfig).filter(models.TradeConfig.user == user)
    else:
        query = select(models.TradeConfig)
    if target_market_code:
        query = query.filter(models.TradeConfig.target_market_code == target_market_code)
    if origin_market_code:
        query = query.filter(models.TradeConfig.origin_market_code == origin_market_code)

    result = await db.execute(query)
    trade_configs = result.scalars().all()

    # if not trade_configs:
    #     raise HTTPException(status_code=404, detail="Exchange config not found")
    return trade_configs

async def get_trade_config(uuid: UUID, db: AsyncSession):
    result = await db.execute(select(models.TradeConfig).filter(
        models.TradeConfig.uuid == uuid
    ))
    trade_config = result.scalar_one_or_none()
    if not trade_config:
        raise HTTPException(status_code=404, detail="Exchange config not found")
    return trade_config

async def create_trade_config(trade_config: schemas.TradeConfigCreate, db: AsyncSession):
    # Check first if the user already has a trade config for the same exchange
    result = await db.execute(select(models.TradeConfig).filter(
        models.TradeConfig.user == trade_config.user,
        models.TradeConfig.target_market_code == trade_config.target_market_code,
        models.TradeConfig.origin_market_code == trade_config.origin_market_code
    ))
    db_trade_config = result.scalar_one_or_none()
    if db_trade_config is not None:
        raise HTTPException(status_code=409, detail="Exchange config already exists")
    db_trade_config = models.TradeConfig(**trade_config.dict())
    db.add(db_trade_config)
    await db.commit()
    await db.refresh(db_trade_config)
    return db_trade_config

async def update_trade_config(uuid: UUID, trade_config: schemas.TradeConfigUpdate, db: AsyncSession):
    result = await db.execute(select(models.TradeConfig).filter(
        models.TradeConfig.uuid == uuid
    ))
    db_trade_config = result.scalar_one_or_none()
    if db_trade_config is None:
        raise HTTPException(status_code=404, detail="Exchange config not found")
    for var, value in vars(trade_config).items():
        if value is not None:
            setattr(db_trade_config, var, value)
    await db.commit()
    await db.refresh(db_trade_config)
    return db_trade_config

async def delete_trade_config(uuid: UUID, db: AsyncSession):
    result = await db.execute(select(models.TradeConfig).filter(
        models.TradeConfig.uuid == uuid
    ))
    trade_config = result.scalar_one_or_none()
    if trade_config is None:
        raise HTTPException(status_code=404, detail="Exchange config not found")
    await db.delete(trade_config)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

async def delete_all_trade_configs(user: UUID, db: AsyncSession):
    # Query to find all trade configs for the user
    result = await db.execute(select(models.TradeConfig).filter(models.TradeConfig.user == user))
    trade_configs = result.scalars().all()

    # Check if any trade configs are found
    if not trade_configs:
        raise HTTPException(status_code=404, detail="No exchange configs found for the user")

    # Delete all trade configs
    for trade_config in trade_configs:
        await db.delete(trade_config)
    
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

async def get_all_trade(trade_config_uuid: UUID, db: AsyncSession):
    if trade_config_uuid is None:
        # Query to find all trades
        result = await db.execute(select(models.Trade))
    else:
        result = await db.execute(select(models.Trade).filter(models.Trade.trade_config_uuid == trade_config_uuid))
    trade_list = result.scalars().all()
    # if not trade_list:
    #     raise HTTPException(status_code=404, detail="No trades found")
    return trade_list

async def get_trade(uuid: UUID, db: AsyncSession):
    result = await db.execute(select(models.Trade).filter(
        models.Trade.uuid == uuid
    ))
    trade = result.scalar_one_or_none()
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade

@handle_db_exceptions
async def create_trade(trade: schemas.TradeCreate, db: AsyncSession):
    if trade.low >= trade.high:
        raise HTTPException(status_code=400, detail="Low must be less than high")
    db_trade = models.Trade(**trade.dict())
    db.add(db_trade)
    await db.commit()
    await db.refresh(db_trade)
    return db_trade

async def delete_trade(uuid: UUID, db: AsyncSession):

    result = await db.execute(select(models.Trade).filter(
        models.Trade.uuid == uuid
    ))
    trade = result.scalar_one_or_none()
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    await db.delete(trade)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

async def update_trade(uuid: UUID, trade: schemas.TradeUpdate, db: AsyncSession):
    result = await db.execute(select(models.Trade).filter(
        models.Trade.uuid == uuid
    ))
    db_trade = result.scalar_one_or_none()
    if db_trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    if trade.low is not None:
        low_to_apply = trade.low
    else:
        low_to_apply = db_trade.low
    if trade.high is not None:
        high_to_apply = trade.high
    else:
        high_to_apply = db_trade.high
    if low_to_apply >= high_to_apply:
        raise HTTPException(status_code=400, detail="Low must be less than high")
    for var, value in vars(trade).items():
        if value is not None:
            setattr(db_trade, var, value)
    await db.commit()
    await db.refresh(db_trade)
    return db_trade

async def delete_all_trade(trade_config_uuid: UUID, db: AsyncSession):
    # Query to find all trades for the user
    result = await db.execute(select(models.Trade).filter(models.Trade.trade_config_uuid == trade_config_uuid))
    trades = result.scalars().all()

    # Check if any trades are found
    if not trades:
        raise HTTPException(status_code=404, detail="No trades found for the user")

    # Delete all trades
    for trade in trades:
        await db.delete(trade)
    
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

async def get_all_exchange_api_keys(trade_config_uuid: UUID, db: AsyncSession):
    if trade_config_uuid is None:
        # Query to find all exchange api keys
        result = await db.execute(select(models.ExchangeApiKey))
    else:
        result = await db.execute(select(models.ExchangeApiKey).filter(models.ExchangeApiKey.trade_config_uuid == trade_config_uuid))
    exchange_api_keys = result.scalars().all()
    if len(exchange_api_keys) != 0:
        for exchange_api_key in exchange_api_keys:
            # display only first 6 character of the access key and change the rest to *
            access_key = decrypt_data(exchange_api_key.access_key)
            access_key = access_key[:6] + b'*' * (len(access_key) - 6)
            exchange_api_key.access_key = access_key
    return exchange_api_keys

async def get_exchange_api_key(uuid: UUID, db: AsyncSession):
    result = await db.execute(select(models.ExchangeApiKey).filter(
        models.ExchangeApiKey.uuid == uuid
    ))
    exchange_api_key = result.scalar_one_or_none()
    if exchange_api_key is None:
        raise HTTPException(status_code=404, detail="Exchange api key not found")
    # display only first 6 character of the access key and change the rest to *
    access_key = decrypt_data(exchange_api_key.access_key)
    access_key = access_key[:6] + b'*' * (len(access_key) - 6)
    exchange_api_key.access_key = access_key
    return exchange_api_key

@handle_db_exceptions
async def create_exchange_api_key(exchange_api_key: schemas.ExchangeApiKeyCreate, db: AsyncSession):
    # Check first if the user already has an exchange api key for the same trade config uuid and api keys
    result = await db.execute(select(models.ExchangeApiKey).filter(
        models.ExchangeApiKey.trade_config_uuid == exchange_api_key.trade_config_uuid
    ))
    db_exchange_api_keys = result.scalars().all()
    if len(db_exchange_api_keys) != 0:
        for db_exchange_api_key in db_exchange_api_keys:
            if decrypt_data(db_exchange_api_key.access_key) == exchange_api_key.access_key:
                raise HTTPException(status_code=409, detail="Exchange api key already exists")
    
    exchange_api_key.market_code = exchange_api_key.market_code.upper()
    exchange_api_key.exchange = exchange_api_key.market_code.split('_')[0]
    # Check whether passphrase is none if the exchange is OKX
    if exchange_api_key.exchange == "OKX" and exchange_api_key.passphrase is None:
        raise HTTPException(status_code=400, detail="Passphrase is required for OKX exchange")
    exchange_api_key.spot = True if 'SPOT' in exchange_api_key.market_code else False
    exchange_api_key.futures = True if 'SPOT' not in exchange_api_key.market_code else False

    access_key_to_check = exchange_api_key.access_key.decode()
    secret_key_to_check = exchange_api_key.secret_key.decode()
    if exchange_api_key.passphrase is not None:
        passphrase_to_check = exchange_api_key.passphrase.decode()
    else:
        passphrase_to_check = None

    # Validation of API key
    try:
        validated_flag, error_str = user_exchange_adaptor.check_api_key(
            exchange_api_key.exchange, access_key_to_check, secret_key_to_check, passphrase_to_check, exchange_api_key.futures
        )
    except Exception as e:
        validated_flag = False
        error_str = str(e)
    if not validated_flag:
        raise HTTPException(status_code=400, detail=error_str)

    # Encrypt the access key and secret key before storing in the database
    exchange_api_key.access_key = encrypt_data(exchange_api_key.access_key)
    exchange_api_key.secret_key = encrypt_data(exchange_api_key.secret_key)
    if exchange_api_key.passphrase is not None:
        exchange_api_key.passphrase = encrypt_data(exchange_api_key.passphrase)

    db_exchange_api_key = models.ExchangeApiKey(**exchange_api_key.dict())
    db.add(db_exchange_api_key)
    await db.commit()
    await db.refresh(db_exchange_api_key)
    return db_exchange_api_key

async def delete_exchange_api_key(uuid: UUID, db: AsyncSession):
    result = await db.execute(select(models.ExchangeApiKey).filter(
        models.ExchangeApiKey.uuid == uuid
    ))
    exchange_api_key = result.scalar_one_or_none()
    if exchange_api_key is None:
        raise HTTPException(status_code=404, detail="Exchange api key not found")
    await db.delete(exchange_api_key)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)





#################### API for communication with exchanges ####################################
async def fetch_spot_position(user: UUID, market_code: str, db: AsyncSession):
    market = market_code.split('/')[0].upper()
    # quote_asset = market_code.split('/')[1].upper()
    temp_list = market.split("_")
    exchange = temp_list[0]
    market_type = '_'.join(temp_list[1:])
    if market_type != 'SPOT':
        raise HTTPException(status_code=400, detail="Invalid market type. Only SPOT market is supported.")

    access_key, secret_key, passphrase = await find_api_keys(user, exchange, True, False, db)
    try:
        position_df = user_exchange_adaptor.get_position(exchange, access_key, secret_key, market_type, passphrase=passphrase)
    except Exception as e:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e))
    return position_df.to_dict(orient="records")

async def fetch_futures_position(user: UUID, market_code: str, db: AsyncSession):
    market = market_code.split('/')[0].upper()
    # quote_asset = market_code.split('/')[1].upper()
    temp_list = market.split("_")
    exchange = temp_list[0]
    market_type = '_'.join(temp_list[1:])
    if market_type == "SPOT":
        raise HTTPException(status_code=400, detail="Invalid market type. Only FUTURES market is supported.")
    
    access_key, secret_key, passphrase = await find_api_keys(user, exchange, False, True, db)
    try:
        position_df = user_exchange_adaptor.get_position(exchange, access_key, secret_key, market_type, passphrase=passphrase)
    except Exception as e:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e))
    return position_df.to_dict(orient="records")

async def fetch_capital(user: UUID, market_code: str, db: AsyncSession):
    market = market_code.split('/')[0].upper()
    # quote_asset = market_code.split('/')[1].upper()
    temp_list = market.split("_")
    exchange = temp_list[0]
    market_type = '_'.join(temp_list[1:])
    if market_type == "SPOT":
        spot = True
        futures = False
    else:
        spot = False
        futures = True
    
    access_key, secret_key, passphrase = await find_api_keys(user, exchange, spot, futures, db)
    try:
        position_df = user_exchange_adaptor.get_capital(exchange, access_key, secret_key, market_type, passphrase=passphrase)
    except Exception as e:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e))
    return position_df.to_dict()

