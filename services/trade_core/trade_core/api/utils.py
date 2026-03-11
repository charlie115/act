from cryptography.fernet import Fernet
import os
import sys
import json
import random
from fastapi import HTTPException
from fastapi import status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
# append current dir
import models
from config import ENCRYPTION_KEY

# Initialize Fernet with your key
# In a real application, load this key from a secure location
fernet = Fernet(ENCRYPTION_KEY)

def encrypt_data(data: bytes) -> bytes:
    """Encrypt data."""
    return fernet.encrypt(data)

def decrypt_data(encrypted_data: bytes) -> bytes:
    """Decrypt data."""
    return fernet.decrypt(encrypted_data)

async def find_api_keys(user: UUID, exchange: str, spot: bool, futures: bool, db: AsyncSession):
    # First fetch all trade_config that has the given user
    trade_configs = await db.execute(select(models.TradeConfig).filter(models.TradeConfig.user == user))
    trade_configs = trade_configs.scalars().all()
    # Fetch the list API keys whose trade_config_uuid is in the trade_configs    
    api_key_list = []
    for trade_config in trade_configs:
        api_keys = await db.execute(select(models.ExchangeApiKey).filter(models.ExchangeApiKey.trade_config_uuid == trade_config.uuid))
        api_keys = api_keys.scalars().all()
        api_keys = [api_key for api_key in api_keys if (api_key.exchange == exchange and api_key.spot == spot) or (api_key.exchange == exchange and api_key.futures == futures)]
        api_key_list.extend(api_keys)
    if api_key_list == []:
        raise HTTPException(status_code=404, detail="No API keys found for the user")
    # Pick one of the api key in the api key list by random
    api_key_obj = random.choice(api_key_list)
    access_key = decrypt_data(api_key_obj.access_key).decode("utf-8")
    secret_key = decrypt_data(api_key_obj.secret_key).decode("utf-8")
    if api_key_obj.passphrase is not None:
        passphrase = decrypt_data(api_key_obj.passphrase).decode("utf-8")
    else:
        passphrase = None
    return access_key, secret_key, passphrase


class MyException(Exception):
    def __init__(self, message, error_code):
        """
        1: No Api Key found
        
        """
        super().__init__(message)
        self.error_code = error_code
