from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Depends
import uuid
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import models, schemas
from database import engine

# Dependency to get the async database session
async def get_db():
    async with AsyncSession(engine) as session:
        yield session

async def get_user_info(user_uuid: str, db: AsyncSession):
    result = await db.execute(select(models.UserInfo).filter(models.UserInfo.user_uuid == user_uuid))
    user_info = result.scalar_one_or_none()
    if user_info is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user_info

async def create_user_info(user_info: schemas.UserInfoCreate, db: AsyncSession):
    db_user_info = models.UserInfo(**user_info.dict())
    db.add(db_user_info)
    await db.commit()
    await db.refresh(db_user_info)
    return db_user_info

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
    return {"detail": "User deleted"}

async def get_exchange_config(user_uuid: str, target_market_code: str, origin_market_code: str, db: AsyncSession):
    result = await db.execute(select(models.ExchangeConfig).filter(
        models.ExchangeConfig.user_uuid == user_uuid,
        models.ExchangeConfig.target_market_code == target_market_code,
        models.ExchangeConfig.origin_market_code == origin_market_code
    ))
    exchange_config = result.scalar_one_or_none()
    if exchange_config is None:
        raise HTTPException(status_code=404, detail="Exchange config not found")
    return exchange_config

async def create_exchange_config(exchange_config: schemas.ExchangeConfigCreate, db: AsyncSession):
    db_exchange_config = models.ExchangeConfig(**exchange_config.dict())
    db.add(db_exchange_config)
    await db.commit()
    await db.refresh(db_exchange_config)
    return db_exchange_config

async def update_exchange_config(user_uuid: str, target_market_code: str, origin_market_code: str, exchange_config: schemas.ExchangeConfigSchema, db: AsyncSession):
    result = await db.execute(select(models.ExchangeConfig).filter(
        models.ExchangeConfig.user_uuid == user_uuid,
        models.ExchangeConfig.target_market_code == target_market_code,
        models.ExchangeConfig.origin_market_code == origin_market_code
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

async def delete_exchange_config(user_uuid: str, target_market_code: str, origin_market_code: str, db: AsyncSession):
    result = await db.execute(select(models.ExchangeConfig).filter(
        models.ExchangeConfig.user_uuid == user_uuid,
        models.ExchangeConfig.target_market_code == target_market_code,
        models.ExchangeConfig.origin_market_code == origin_market_code
    ))
    exchange_config = result.scalar_one_or_none()
    if exchange_config is None:
        raise HTTPException(status_code=404, detail="Exchange config not found")
    await db.delete(exchange_config)
    await db.commit()
    return {"detail": "Exchange config deleted"}

async def get_trade(user_uuid: str, uuid: str, db: AsyncSession):
    result = await db.execute(select(models.Trade).filter(
        models.Trade.user_uuid == user_uuid,
        models.Trade.uuid == uuid
    ))
    trade = result.scalar_one_or_none()
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade

async def get_all_trade(user_uuid: str, db: AsyncSession):
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

async def delete_trade(user_uuid: str, uuid: str, db: AsyncSession):
    result = await db.execute(select(models.Trade).filter(
        models.Trade.user_uuid == user_uuid,
        models.Trade.uuid == uuid
    ))
    trade = result.scalar_one_or_none()
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    await db.delete(trade)
    await db.commit()
    return {"detail": "Trade deleted"}

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
    return {"detail": "All trades for the user have been deleted"}