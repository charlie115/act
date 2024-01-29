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
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import schemas
import crud

app = FastAPI()

@app.post("/users/", response_model=schemas.UserInfoSchema)
async def create_user(user: schemas.UserInfoCreate, db: AsyncSession = Depends(crud.get_db)):
    return await crud.create_user_info(user, db)

@app.get("/users/", response_model=List[schemas.UserInfoSchema])
async def read_user(db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_all_user_info(db)

@app.get("/users/{user_uuid}", response_model=schemas.UserInfoSchema)
async def read_user(user_uuid: str, db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_user_info(user_uuid, db)

@app.put("/users/{user_uuid}", response_model=schemas.UserInfoSchema)
async def update_user(user_uuid: str, user: schemas.UserInfoSchema, db: AsyncSession = Depends(crud.get_db)):
    return await crud.update_user_info(user_uuid, user, db)

@app.delete("/users/{user_uuid}")
async def remove_user(user_uuid: str, db: AsyncSession = Depends(crud.get_db)):
    return await crud.delete_user_info(user_uuid, db)

@app.post("/exchange-config/", response_model=schemas.ExchangeConfigSchema)
async def create_exchange_config(config: schemas.ExchangeConfigCreate, db: AsyncSession = Depends(crud.get_db)):
    return await crud.create_exchange_config(config, db)

@app.get("/exchange-config/", response_model=List[schemas.ExchangeConfigSchema])
async def read_exchange_config(user_uuid: Optional[str] = None, target_market_code: Optional[str] = None, origin_market_code: Optional[str] = None, db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_exchange_configs(user_uuid, target_market_code, origin_market_code, db)

@app.get("/exchange-config/{id}", response_model=schemas.ExchangeConfigSchema)
async def read_exchange_config(id: int, db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_exchange_config(id, db)

@app.put("/exchange-config/{id}", response_model=schemas.ExchangeConfigSchema)
async def update_exchange_config(id: int, config: schemas.ExchangeConfigSchema, db: AsyncSession = Depends(crud.get_db)):
    return await crud.update_exchange_config(id, config, db)

@app.delete("/exchange-config/{id}")
async def remove_exchange_config(id: int, db: AsyncSession = Depends(crud.get_db)):
    return await crud.delete_exchange_config(id, db)

@app.get("/trades/", response_model=List[schemas.TradeSchema])
async def read_trades(user_uuid: Optional[str] = None, db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_all_trade(user_uuid, db)

@app.get("/trades/{uuid}", response_model=schemas.TradeSchema)
async def read_trade(uuid: str, db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_trade(uuid, db)

@app.post("/trades/", response_model=schemas.TradeSchema)
async def create_trade(trade: schemas.TradeCreate, db: AsyncSession = Depends(crud.get_db)):
    return await crud.create_trade(trade, db)

@app.put("/trades/{uuid}", response_model=schemas.TradeSchema)
async def update_trade(uuid: str, trade: schemas.TradeSchema, db: AsyncSession = Depends(crud.get_db)):
    return await crud.update_trade(uuid, trade, db)

@app.delete("/trades/{uuid}")
async def remove_trade(uuid: str, db: AsyncSession = Depends(crud.get_db)):
    return await crud.delete_trade(uuid, db)

@app.delete("/trades/{user_uuid}/all")
async def remove_all_trades(user_uuid: str, db: AsyncSession = Depends(crud.get_db)):
    return await crud.delete_all_trade(user_uuid, db)

# Additional endpoints can be added as needed