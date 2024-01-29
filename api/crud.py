from fastapi import HTTPException
from fastapi import status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Depends
from sqlalchemy.exc import IntegrityError
import uuid
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import models, schemas
from database import engine
import datetime

# Dependency to get the async database session
async def get_db():
    async with AsyncSession(engine) as session:
        yield session

async def get_all_user_info(db: AsyncSession):
    result = await db.execute(select(models.UserInfo))
    user_info_list = result.scalars().all()
    return user_info_list

async def get_user_info(user_uuid: str, db: AsyncSession):
    result = await db.execute(select(models.UserInfo).filter(models.UserInfo.user_uuid == user_uuid))
    user_info = result.scalar_one_or_none()
    if user_info is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user_info

async def create_user_info(user_info: schemas.UserInfoCreate, db: AsyncSession):
    try:
        db_user_info = models.UserInfo(**{"registered_datetime": datetime.datetime.utcnow(), **user_info.dict()})
        db.add(db_user_info)
        await db.commit()
        await db.refresh(db_user_info)
        return db_user_info
    except IntegrityError as e:
        print(str(e))
        if 'already exists' in str(e):
            raise HTTPException(status_code=409, detail="User already exists")
        else:
            raise 

async def update_user_info(user_uuid: str, user_info: schemas.UserInfoSchema, db: AsyncSession):
    result = await db.execute(select(models.UserInfo).filter(models.UserInfo.user_uuid == user_uuid))
    db_user_info = result.scalar_one_or_none()
    if db_user_info is None:
        raise HTTPException(status_code=404, detail="User not found")
    for var, value in vars(user_info).items():
        if value is not None:
            setattr(db_user_info, var, value)
    await db.commit()
    await db.refresh(db_user_info)
    return db_user_info

async def delete_user_info(user_uuid: str, db: AsyncSession):
    result = await db.execute(select(models.UserInfo).filter(models.UserInfo.user_uuid == user_uuid))
    user_info = result.scalar_one_or_none()
    if user_info is None:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user_info)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

async def get_exchange_configs(user_uuid: str, target_market_code: str, origin_market_code: str, db: AsyncSession):
    if user_uuid:
        query = select(models.ExchangeConfig).filter(models.ExchangeConfig.user_uuid == user_uuid)
    else:
        query = select(models.ExchangeConfig)
    if target_market_code:
        query = query.filter(models.ExchangeConfig.target_market_code == target_market_code)
    if origin_market_code:
        query = query.filter(models.ExchangeConfig.origin_market_code == origin_market_code)

    result = await db.execute(query)
    exchange_configs = result.scalars().all()

    if not exchange_configs:
        raise HTTPException(status_code=404, detail="Exchange config not found")
    return exchange_configs

async def get_exchange_config(id: int, db: AsyncSession):
    result = await db.execute(select(models.ExchangeConfig).filter(
        models.ExchangeConfig.id == id
    ))
    exchange_config = result.scalar_one_or_none()
    if not exchange_config:
        raise HTTPException(status_code=404, detail="Exchange config not found")
    return exchange_config

async def create_exchange_config(exchange_config: schemas.ExchangeConfigCreate, db: AsyncSession):
    try:
        db_exchange_config = models.ExchangeConfig(**exchange_config.dict())
        db.add(db_exchange_config)
        await db.commit()
        await db.refresh(db_exchange_config)
        return db_exchange_config
    except IntegrityError as e:
        if 'not-null' in str(e) and 'market_code' in str(e):
            raise HTTPException(status_code=400, detail="target_market_code and origin_market_code cannot be null")

async def update_exchange_config(id: int, exchange_config: schemas.ExchangeConfigSchema, db: AsyncSession):
    result = await db.execute(select(models.ExchangeConfig).filter(
        models.ExchangeConfig.id == id
    ))
    db_exchange_config = result.scalar_one_or_none()
    if db_exchange_config is None:
        raise HTTPException(status_code=404, detail="Exchange config not found")
    for var, value in vars(exchange_config).items():
        if value is not None:
            setattr(db_exchange_config, var, value)
    await db.commit()
    await db.refresh(db_exchange_config)
    return db_exchange_config

async def delete_exchange_config(id: int, db: AsyncSession):
    result = await db.execute(select(models.ExchangeConfig).filter(
        models.ExchangeConfig.id == id
    ))
    exchange_config = result.scalar_one_or_none()
    if exchange_config is None:
        raise HTTPException(status_code=404, detail="Exchange config not found")
    await db.delete(exchange_config)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

async def get_trade(uuid: str, db: AsyncSession):
    result = await db.execute(select(models.Trade).filter(
        models.Trade.uuid == uuid
    ))
    trade = result.scalar_one_or_none()
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade

async def get_all_trade(user_uuid: str, db: AsyncSession):
    if user_uuid is None:
        # Query to find all trades
        result = await db.execute(select(models.Trade))
    else:
        result = await db.execute(select(models.Trade).filter(models.Trade.user_uuid == user_uuid))
    trade_list = result.scalars().all()
    return trade_list

async def create_trade(trade: schemas.TradeCreate, db: AsyncSession):
    trade_uuid = uuid.uuid4().hex
    db_trade = models.Trade(uuid=trade_uuid, **trade.dict())
    db.add(db_trade)
    await db.commit()
    await db.refresh(db_trade)
    return db_trade

async def delete_trade(uuid: str, db: AsyncSession):
    result = await db.execute(select(models.Trade).filter(
        models.Trade.uuid == uuid
    ))
    trade = result.scalar_one_or_none()
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    await db.delete(trade)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

async def update_trade(uuid: str, trade: schemas.TradeSchema, db: AsyncSession):
    result = await db.execute(select(models.Trade).filter(
        models.Trade.uuid == uuid
    ))
    db_trade = result.scalar_one_or_none()
    if db_trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    for var, value in vars(trade).items():
        if value is not None:
            setattr(db_trade, var, value)
    await db.commit()
    await db.refresh(db_trade)
    return db_trade

async def delete_all_trade(user_uuid: str, db: AsyncSession):
    # Query to find all trades for the user
    result = await db.execute(select(models.Trade).filter(models.Trade.user_uuid == user_uuid))
    trades = result.scalars().all()

    # Check if any trades are found
    if not trades:
        raise HTTPException(status_code=404, detail="No trades found for the user")

    # Delete all trades
    for trade in trades:
        await db.delete(trade)
    
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)