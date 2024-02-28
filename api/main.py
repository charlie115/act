import random
from fastapi import FastAPI
from fastapi import status
from fastapi.responses import Response
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
from typing import Optional
from typing import List
from uuid import UUID
import sys, os
upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from api import schemas
from api import crud

app = FastAPI()


@app.post("/trade-config/", response_model=schemas.TradeConfig, status_code=status.HTTP_201_CREATED)
async def create_trade_config(trade_config: schemas.TradeConfigCreate, db: AsyncSession = Depends(crud.get_db)):
    return await crud.create_trade_config(trade_config, db)

@app.get("/trade-config/", response_model=List[schemas.TradeConfig])
async def read_all_trade_config(user: Optional[UUID] = None, target_market_code: Optional[str] = None, origin_market_code: Optional[str] = None, db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_all_trade_configs(user, target_market_code, origin_market_code, db)

@app.get("/trade-config/{uuid}", response_model=schemas.TradeConfig)
async def read_trade_config(uuid: UUID, db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_trade_config(uuid, db)

@app.put("/trade-config/{uuid}", response_model=schemas.TradeConfig)
async def update_trade_config(uuid: UUID, trade_config: schemas.TradeConfigUpdate, db: AsyncSession = Depends(crud.get_db)):
    return await crud.update_trade_config(uuid, trade_config, db)

@app.delete("/trade-config/{uuid}")
async def remove_trade_config(uuid: UUID, db: AsyncSession = Depends(crud.get_db)):
    return await crud.delete_trade_config(uuid, db)

@app.delete("/trade-config/")
async def remove_trade_config(user: UUID, db: AsyncSession = Depends(crud.get_db)):
    return await crud.delete_all_trade_configs(user, db)

@app.get("/trades/", response_model=List[schemas.Trade])
async def read_trades(trade_config_uuid: Optional[UUID] = None, db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_all_trade(trade_config_uuid, db)

@app.get("/trades/{uuid}", response_model=schemas.Trade)
async def read_trade(uuid: UUID, db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_trade(uuid, db)

@app.post("/trades/", response_model=schemas.Trade, status_code=status.HTTP_201_CREATED)
async def create_trade(trade: schemas.TradeCreate, db: AsyncSession = Depends(crud.get_db)):
    return await crud.create_trade(trade, db)

@app.put("/trades/{uuid}", response_model=schemas.Trade)
async def update_trade(uuid: UUID, trade: schemas.TradeUpdate, db: AsyncSession = Depends(crud.get_db)):
    return await crud.update_trade(uuid, trade, db)

@app.delete("/trades/{uuid}")
async def remove_trade(uuid: UUID, db: AsyncSession = Depends(crud.get_db)):
    return await crud.delete_trade(uuid, db)

@app.delete("/trades/")
async def remove_all_trades(trade_config_uuid: UUID, db: AsyncSession = Depends(crud.get_db)):
    return await crud.delete_all_trade(trade_config_uuid, db)

@app.get("/exchange-api-key/", response_model=List[schemas.ExchangeApiKey])
async def read_exchange_api_keys(trade_config_uuid: Optional[UUID] = None, db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_all_exchange_api_keys(trade_config_uuid, db)

@app.get("/exchange-api-key/{uuid}", response_model=schemas.ExchangeApiKey)
async def read_exchange_api_key(uuid: UUID, db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_exchange_api_key(uuid, db)

@app.post("/exchange-api-key/", response_model=schemas.ExchangeApiKey, status_code=status.HTTP_201_CREATED)
async def create_exchange_api_key(exchange_api_key: schemas.ExchangeApiKeyCreate, db: AsyncSession = Depends(crud.get_db)):
    return await crud.create_exchange_api_key(exchange_api_key, db)

@app.put("/exchange-api-key/{uuid}", response_model=schemas.ExchangeApiKey)
async def update_exchange_api_key(uuid: UUID, exchange_api_key: schemas.ExchangeApiKeyUpdate, db: AsyncSession = Depends(crud.get_db)):
    return await crud.update_exchange_api_key(uuid, exchange_api_key, db)

@app.delete("/exchange-api-key/{uuid}")
async def remove_exchange_api_key(uuid: UUID, db: AsyncSession = Depends(crud.get_db)):
    return await crud.delete_exchange_api_key(uuid, db)



############ API endpoints for communication with exchanges ####################################
@app.get("/spot-position/{user}", response_model=List[schemas.SpotPosition])
async def read_spot_position(user: UUID, market_code: str, db: AsyncSession = Depends(crud.get_db)):
    return await crud.fetch_spot_position(user, market_code, db)

@app.get("/futures-position/{user}", response_model=List[schemas.USDMPosition])
async def read_futures_position(user: UUID, market_code: str, db: AsyncSession = Depends(crud.get_db)):
    return await crud.fetch_futures_position(user, market_code, db)

@app.get("/capital/{user}", response_model=schemas.Capital)
async def read_capital(user: UUID, market_code: str, db: AsyncSession = Depends(crud.get_db)):
    return await crud.fetch_capital(user, market_code, db)