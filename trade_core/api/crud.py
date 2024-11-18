import random
import json
import traceback
from fastapi import HTTPException
from fastapi import status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Depends
from sqlalchemy.exc import IntegrityError
from uuid import UUID
import uuid
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import models, schemas
from utils import encrypt_data, decrypt_data, find_api_keys
from decorators import handle_db_exceptions
from database import engine
import datetime
from exchange_plugin.integrated_plug import UserExchangeAdaptor
from standalone_func.data_process import get_pboundary
from etc.db_handler.mongodb_client import InitDBClient
from etc.acw_api import AcwApi
from dotenv import load_dotenv
from config import logging_dir, PROD, NODE, ADMIN_TELEGRAM_ID, USER_UUID_FOR_WALLET, ACW_API_URL, mongo_db_dict


acw_api = AcwApi(ACW_API_URL, NODE, PROD)

# initialize exchange adaptors
user_exchange_adaptor = UserExchangeAdaptor(admin_id=ADMIN_TELEGRAM_ID, acw_api=acw_api, logging_dir=logging_dir)

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

# Automatically add trade to the trade_log table too
@handle_db_exceptions
async def create_trade(trade: schemas.TradeCreate, db: AsyncSession):
    if trade.low >= trade.high:
        raise HTTPException(status_code=400, detail="Low must be less than high")
    # Change margin mode and leverage if the trigger is trading trigger.
    if trade.trade_capital is not None and trade.trade_capital > 0:
        # Read trade config data
        result = await db.execute(select(models.TradeConfig).filter(
            models.TradeConfig.uuid == trade.trade_config_uuid
        ))
        trade_config = result.scalar_one_or_none()
        if trade_config is None:
            raise HTTPException(status_code=404, detail="Trade config not found")
        target_market_code = trade_config.target_market_code
        target_exchange = target_market_code.split('_')[0]
        target_market_type = target_market_code.split('/')[0].replace(target_exchange + '_', '')
        if target_market_type != "SPOT":
            # Fetch api keys
            access_key, secret_key, passphrase = await find_api_keys(trade_config.user, target_exchange,
                                                                    True if target_market_type == 'SPOT' else False, True if target_market_type != 'SPOT' else False, db)
            try:
                user_exchange_adaptor.change_margin_type(target_exchange, access_key, secret_key, target_market_type, trade_config.target_market_cross, user_exchange_adaptor.symbol_converter(target_market_code, trade.base_asset), passphrase)
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
            try:
                user_exchange_adaptor.change_leverage(target_exchange, access_key, secret_key, target_market_type, trade_config.target_market_leverage, user_exchange_adaptor.symbol_converter(target_market_code, trade.base_asset), passphrase)
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
            title = f"{target_market_code} {user_exchange_adaptor.symbol_converter(target_market_code, trade.base_asset)} 마진타입 및 레버리지 변경"
            content = f"{user_exchange_adaptor.symbol_converter(target_market_code, trade.base_asset)}의 마진타입이 {'교차' if trade_config.target_market_cross else '격리'}로 설정되었습니다.\n레버리지가 {trade_config.target_market_leverage}배로 설정되었습니다."
            full_content = title + '\n' + content
            acw_api.create_message_thread(trade_config.telegram_id, title, full_content, 'INFO')
        origin_market_code = trade_config.origin_market_code
        origin_exchange = origin_market_code.split('_')[0]
        origin_market_type = origin_market_code.split('/')[0].replace(origin_exchange + '_', '')
        if origin_market_type != "SPOT":
            # Fetch api keys
            access_key, secret_key, passphrase = await find_api_keys(trade_config.user, origin_exchange,
                                                                    True if origin_market_type == 'SPOT' else False, True if origin_market_type != 'SPOT' else False, db)
            try:
                user_exchange_adaptor.change_margin_type(origin_exchange, access_key, secret_key, origin_market_type, trade_config.origin_market_cross, user_exchange_adaptor.symbol_converter(origin_market_code, trade.base_asset), passphrase)
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
            try:
                user_exchange_adaptor.change_leverage(origin_exchange, access_key, secret_key, origin_market_type, trade_config.origin_market_leverage, user_exchange_adaptor.symbol_converter(origin_market_code, trade.base_asset), passphrase)
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
            title = f"{origin_market_code} {user_exchange_adaptor.symbol_converter(origin_market_code, trade.base_asset)} 마진타입 및 레버리지 변경"
            content = f"{user_exchange_adaptor.symbol_converter(origin_market_code, trade.base_asset)}의 마진타입이 {'교차' if trade_config.origin_market_cross else '격리'}로 설정되었습니다.\n레버리지가 {trade_config.origin_market_leverage}배로 설정되었습니다."
            full_content = title + '\n' + content
            acw_api.create_message_thread(trade_config.telegram_id, title, full_content, 'INFO')
    
    new_uuid = uuid.uuid4()
    db_trade = models.Trade(**{**trade.dict(), "uuid": new_uuid})
    db.add(db_trade)

    # Add trade to the trade_log table
    # trade_log = models.TradeLog(
    #     trade_uuid=db_trade.uuid,
    #     trade_config_uuid=db_trade.trade_config_uuid,
    #     base_asset=db_trade.base_asset,
    #     usdt_conversion=db_trade.usdt_conversion,
    #     low=db_trade.low,
    #     high=db_trade.high,
    #     trade_capital=db_trade.trade_capital,
    #     status=db_trade.status,
    #     remark=db_trade.remark
    # )
    # create trade_log with the same uuid as trade
    trade_log_schema = schemas.TradeLogCreate(
        trade_uuid=db_trade.uuid,
        trade_config_uuid=db_trade.trade_config_uuid,
        base_asset=db_trade.base_asset,
        usdt_conversion=db_trade.usdt_conversion,
        low=db_trade.low,
        high=db_trade.high,
        trade_capital=db_trade.trade_capital,
        status=db_trade.status,
        remark=db_trade.remark
    )
    trade_log = models.TradeLog(**trade_log_schema.dict())
    db.add(trade_log)
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
    # Change deleted flag to True from trade_log table
    result = await db.execute(select(models.TradeLog).filter(
        models.TradeLog.trade_uuid == uuid
    ))
    trade_log = result.scalar_one_or_none()
    if trade_log is None:
        raise HTTPException(status_code=404, detail="Trade log not found")
    trade_log.deleted = True
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
    # UPDATE trade_log as well if the trade has a deleted=False flag
    result = await db.execute(select(models.TradeLog).filter(
        models.TradeLog.trade_uuid == uuid
    ))
    trade_log = result.scalar_one_or_none()
    if trade_log is None:
        raise HTTPException(status_code=404, detail="Trade log not found")
    if trade.trade_config_uuid is not None:
        trade_log.trade_config_uuid = trade.trade_config_uuid
    if trade.usdt_conversion is not None:
        trade_log.usdt_conversion = trade.usdt_conversion
    if trade.low is not None:
        trade_log.low = trade.low
    if trade.high is not None:
        trade_log.high = trade.high
    if trade.trade_capital is not None:
        trade_log.trade_capital = trade.trade_capital
    if trade.status is not None:
        trade_log.status = trade.status
    if trade.remark is not None:
        trade_log.remark = trade.remark
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
    
    # Change deleted flag to True from trade_log table
    result = await db.execute(select(models.TradeLog).filter(
        models.TradeLog.trade_config_uuid == trade_config_uuid
    ))
    trade_logs = result.scalars().all()
    for trade_log in trade_logs:
        trade_log.deleted = True
    
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

async def get_all_trade_logs(trade_config_uuid: UUID, db: AsyncSession):
    if trade_config_uuid is None:
        # Query to find all trades
        result = await db.execute(select(models.TradeLog))
    else:
        result = await db.execute(select(models.TradeLog).filter(models.TradeLog.trade_config_uuid == trade_config_uuid))
    trade_logs = result.scalars().all()
    if not trade_logs:
        raise HTTPException(status_code=404, detail="No trade logs found")
    return trade_logs

async def get_trade_log(uuid: UUID, db: AsyncSession):
    result = await db.execute(select(models.TradeLog).filter(
        models.TradeLog.uuid == uuid
    ))
    trade_log = result.scalar_one_or_none()
    if trade_log is None:
        raise HTTPException(status_code=404, detail="Trade log not found")
    return trade_log

async def get_all_repeat_trades(trade_config_uuid: UUID, db: AsyncSession):
    if trade_config_uuid is None:
        # Query to find all repeat trades
        result = await db.execute(select(models.RepeatTrade))
    else:
        # First filter by trade_config_uuid from the trade table
        trades = await db.execute(select(models.Trade).filter(models.Trade.trade_config_uuid == trade_config_uuid))
        # Then find repeat trades whose trade_uuid is in the list of trade_uuids
        trade_uuids = [trade.uuid for trade in trades.scalars().all()]
        result = await db.execute(select(models.RepeatTrade).filter(models.RepeatTrade.trade_uuid.in_(trade_uuids)))
    repeat_trades = result.scalars().all()
    if not repeat_trades:
        raise HTTPException(status_code=404, detail="No repeat trades found")
    return repeat_trades

async def get_repeat_trade(uuid: UUID, db: AsyncSession):
    result = await db.execute(select(models.RepeatTrade).filter(
        models.RepeatTrade.uuid == uuid
    ))
    repeat_trade = result.scalar_one_or_none()
    if repeat_trade is None:
        raise HTTPException(status_code=404, detail="Repeat trade not found")
    return repeat_trade

async def create_repeat_trade(repeat_trade: schemas.RepeatTradeCreate, db: AsyncSession):
    new_uuid = uuid.uuid4()
    db_repeat_trade = models.RepeatTrade(**{**repeat_trade.dict(), "uuid": new_uuid})
    db.add(db_repeat_trade)
    await db.commit()
    await db.refresh(db_repeat_trade)
    return db_repeat_trade

async def update_repeat_trade(uuid: UUID, repeat_trade: schemas.RepeatTradeUpdate, db: AsyncSession):
    result = await db.execute(select(models.RepeatTrade).filter(
        models.RepeatTrade.uuid == uuid
    ))
    db_repeat_trade = result.scalar_one_or_none()
    if db_repeat_trade is None:
        raise HTTPException(status_code=404, detail="Repeat trade not found")
    for var, value in vars(repeat_trade).items():
        if value is not None:
            setattr(db_repeat_trade, var, value)
    await db.commit()
    await db.refresh(db_repeat_trade)
    return db_repeat_trade

async def delete_repeat_trade(uuid: UUID, db: AsyncSession):
    result = await db.execute(select(models.RepeatTrade).filter(
        models.RepeatTrade.uuid == uuid
    ))
    repeat_trade = result.scalar_one_or_none()
    if repeat_trade is None:
        raise HTTPException(status_code=404, detail="Repeat trade not found")
    await db.delete(repeat_trade)
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

async def get_all_order_history(trade_config_uuid: UUID, trade_uuid: UUID, db: AsyncSession):
    if trade_config_uuid is None and trade_uuid is None:
        # Query to find all order history
        result = await db.execute(select(models.OrderHistory))
    else:
        query = select(models.OrderHistory)
        if trade_config_uuid:
            query = query.filter(models.OrderHistory.trade_config_uuid == trade_config_uuid)
        if trade_uuid:
            query = query.filter(models.OrderHistory.trade_uuid == trade_uuid)
        result = await db.execute(query)
    order_histories = result.scalars().all()
    if not order_histories:
        raise HTTPException(status_code=404, detail="No order history found")
    return order_histories

async def get_order_history(order_id: str, db: AsyncSession):
    result = await db.execute(select(models.OrderHistory).filter(
        models.OrderHistory.order_id == order_id
    ))
    order_history = result.scalar_one_or_none()
    if order_history is None:
        raise HTTPException(status_code=404, detail="Order history not found")
    return order_history

async def get_all_trade_history(trade_config_uuid: UUID, trade_uuid: UUID, db: AsyncSession):
    if trade_config_uuid is None and trade_uuid is None:
        # Query to find all trade history
        result = await db.execute(select(models.TradeHistory))
    else:
        query = select(models.TradeHistory)
        if trade_config_uuid:
            query = query.filter(models.TradeHistory.trade_config_uuid == trade_config_uuid)
        if trade_uuid:
            query = query.filter(models.TradeHistory.trade_uuid == trade_uuid)
        result = await db.execute(query)
    trade_histories = result.scalars().all()
    if not trade_histories:
        raise HTTPException(status_code=404, detail="No trade history found")
    return trade_histories

async def get_trade_history(uuid: UUID, db: AsyncSession):
    result = await db.execute(select(models.TradeHistory).filter(
        models.TradeHistory.uuid == uuid
    ))
    trade_history = result.scalar_one_or_none()
    if trade_history is None:
        raise HTTPException(status_code=404, detail="Trade history not found")
    return trade_history

async def get_all_pnl_history(trade_config_uuid: UUID, trade_uuid: UUID, db: AsyncSession):
    if trade_config_uuid is None and trade_uuid is None:
        # Query to find all pnl history
        result = await db.execute(select(models.PnlHistory))
    else:
        query = select(models.PnlHistory)
        if trade_config_uuid:
            query = query.filter(models.PnlHistory.trade_config_uuid == trade_config_uuid)
        if trade_uuid:
            query = query.filter(models.PnlHistory.trade_uuid == trade_uuid)
        result = await db.execute(query)
    pnl_histories = result.scalars().all()
    if not pnl_histories:
        raise HTTPException(status_code=404, detail="No pnl history found")
    return pnl_histories

async def get_pnl_history(uuid: UUID, db: AsyncSession):
    result = await db.execute(select(models.PnlHistory).filter(
        models.PnlHistory.uuid == uuid
    ))
    pnl_history = result.scalar_one_or_none()
    if pnl_history is None:
        raise HTTPException(status_code=404, detail="Pnl history not found")
    return pnl_history

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
        print(traceback.format_exc())
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

#################### API for data processing ####################################

async def fetch_pboundary(market_code_combination: str, base_asset: str, usdt_conversion: bool, percent_gap: float, interval: str, kline_num: int, draw_plot: bool, return_dict):
    try:
        output_dict = get_pboundary(mongo_db_dict, market_code_combination, base_asset, usdt_conversion, interval, kline_num, percent_gap, logging_dir, draw_plot, return_dict)
    except Exception as e:
        # Check whether the error is ValueError
        if isinstance(e, ValueError):
            return Response(status_code=status.HTTP_400_BAD_REQUEST, content=str(e))
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e))
    return output_dict


#################### API for wallet deposit ####################################

async def fetch_deposit_address(db: AsyncSession):
    try:
        exchange = 'BINANCE'
        access_key, secret_key, passphrase = await find_api_keys(USER_UUID_FOR_WALLET, exchange, True, False, db)
        output_dict = user_exchange_adaptor.get_deposit_address(exchange, access_key, secret_key, passphrase)
        return output_dict
    except Exception as e:
        print(traceback.format_exc())
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e))
    
async def fetch_deposit_amount(txid: str, db: AsyncSession):
    try:
        exchange = 'BINANCE'
        access_key, secret_key, passphrase = await find_api_keys(USER_UUID_FOR_WALLET, exchange, True, False, db)
        output_dict = user_exchange_adaptor.get_deposit_amount(exchange, access_key, secret_key, passphrase, txid, asset='USDT')
        return output_dict
    except Exception as e:
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=str(e))
    