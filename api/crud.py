import random
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
from utils import encrypt_data, decrypt_data
from decorators import handle_db_exceptions
from database import engine
import datetime
from exchange_plugin.binance_plug import UserBinanceAdaptor
from exchange_plugin.upbit_plug import UserUpbitAdaptor

# Dependency to get the async database session
async def get_db():
    async with AsyncSession(engine) as session:
        yield session

async def get_all_trade_configs(acw_user_uuid: UUID, target_market_code: str, origin_market_code: str, db: AsyncSession):
    if acw_user_uuid:
        query = select(models.TradeConfig).filter(models.TradeConfig.acw_user_uuid == acw_user_uuid)
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
        models.TradeConfig.acw_user_uuid == trade_config.acw_user_uuid,
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

async def delete_all_trade_configs(acw_user_uuid: UUID, db: AsyncSession):
    # Query to find all trade configs for the user
    result = await db.execute(select(models.TradeConfig).filter(models.TradeConfig.acw_user_uuid == acw_user_uuid))
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

    # Encrypt the access key and secret key before storing in the database
    exchange_api_key.access_key = encrypt_data(exchange_api_key.access_key)
    exchange_api_key.secret_key = encrypt_data(exchange_api_key.secret_key)

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





# #################### API for communication with exchanges ####################################
# # initialize exchange adaptors
# user_binance_adaptor = UserBinanceAdaptor()
# user_upbit_adaptor = UserUpbitAdaptor()

# async def fetch_balance(acw_user_uuid: UUID, market_code: str, db: AsyncSession):
#     available_exchange_list = ["BINANCE", "UPBIT"]
#     market = market_code.split('/')[0].upper()
#     temp_list = market.split("_")
#     exchange = temp_list[0]
#     market_type = '_'.join(temp_list[1:])

#     if exchange not in available_exchange_list:
#         # return error response with the available exchange list
#         return Response(status_code=status.HTTP_400_BAD_REQUEST, content=f"Exchange: {exchange} not supported. Available exchanges: {available_exchange_list}")
    
#     # First fetch all trade_config that has the given acw_user_uuid
#     trade_configs = await db.execute(select(models.TradeConfig).filter(models.TradeConfig.acw_user_uuid == acw_user_uuid))
#     trade_configs = trade_configs.scalars().all()
#     # Fetch the list API keys whose trade_config_uuid is in the trade_configs    
#     api_key_list = []
#     for trade_config in trade_configs:
#         api_keys = await db.execute(select(models.ExchangeApiKey).filter(models.ExchangeApiKey.trade_config_uuid == trade_config.uuid))
#         api_keys = api_keys.scalars().all()
#         api_keys = [api_key for api_key in api_keys if api_key.market_code == market_code]
#         api_key_list.extend(api_keys)

#     # Pick one of the api key in the api key list by random
#     api_key_obj = random.choice(api_key_list)
#     access_key = decrypt_data(api_key_obj.access_key).decode("utf-8")
#     secret_key = decrypt_data(api_key_obj.secret_key).decode("utf-8")

#     if exchange.upper() == "BINANCE":
#         try:
#             balance_df = user_binance_adaptor.get_balance(access_key, secret_key, market_type)
#         except Exception as e:
#             return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e))
#     elif exchange.upper() == "UPBIT":
#         try:
#             balance_df = user_upbit_adaptor.get_balance(access_key, secret_key)
#         except Exception as e:
#             return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e))
#     else:
#         raise ValueError(f"Exchange: {exchange} not supported.")
    
#     return balance_df.to_dict(orient="records")