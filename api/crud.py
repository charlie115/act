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
from decorators import handle_db_exceptions
from database import engine
import datetime

# Dependency to get the async database session
async def get_db():
    async with AsyncSession(engine) as session:
        yield session

async def get_all_trade_configs(acw_user_uuid: UUID, target_market_code: str, origin_market_code: str, db: AsyncSession):
    # TEST
    print(f"acw_user_uuid: {acw_user_uuid}")
    print(f"type: {type(acw_user_uuid)}")
    # TEST
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