from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import schemas
import crud

app = FastAPI()

@app.post("/users/", response_model=schemas.UserInfoSchema)
async def create_user(user: schemas.UserInfoCreate, db: AsyncSession = Depends(crud.get_db)):
    return await crud.create_user_info(user, db)

@app.get("/users/{user_uuid}", response_model=schemas.UserInfoSchema)
async def read_user(user_uuid: str, db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_user_info(user_uuid, db)

@app.put("/users/{user_uuid}", response_model=schemas.UserInfoSchema)
async def update_user(user_uuid: str, user: schemas.UserInfoSchema, db: AsyncSession = Depends(crud.get_db)):
    return await crud.update_user_info(user_uuid, user, db)

@app.delete("/users/{user_uuid}")
async def remove_user(user_uuid: str, db: AsyncSession = Depends(crud.get_db)):
    await crud.delete_user_info(user_uuid, db)
    return {"detail": "User deleted"}

@app.get("/exchange-config/", response_model=schemas.ExchangeConfigSchema)
async def read_exchange_config(user_uuid: str, target_market_code: str, origin_market_code: str, db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_exchange_config(user_uuid, target_market_code, origin_market_code, db)

@app.post("/exchange-config/", response_model=schemas.ExchangeConfigSchema)
async def create_exchange_config(config: schemas.ExchangeConfigCreate, db: AsyncSession = Depends(crud.get_db)):
    return await crud.create_exchange_config(config, db)

@app.put("/exchange-config/", response_model=schemas.ExchangeConfigSchema)
async def update_exchange_config(user_uuid: str, target_market_code: str, origin_market_code: str, config: schemas.ExchangeConfigSchema, db: AsyncSession = Depends(crud.get_db)):
    return await crud.update_exchange_config(user_uuid, target_market_code, origin_market_code, config, db)

@app.delete("/exchange-config/")
async def remove_exchange_config(user_uuid: str, target_market_code: str, origin_market_code: str, db: AsyncSession = Depends(crud.get_db)):
    await crud.delete_exchange_config(user_uuid, target_market_code, origin_market_code, db)
    return {"detail": "Exchange config deleted"}

@app.get("/trades/{uuid}", response_model=schemas.TradeSchema)
async def read_trade(user_uuid: str, uuid: str, db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_trade(user_uuid, uuid, db)

@app.get("/trades/all/", response_model=list[schemas.TradeSchema])
async def read_all_trades(user_uuid: str, db: AsyncSession = Depends(crud.get_db)):
    return await crud.get_all_trade(user_uuid, db)

@app.post("/trades/", response_model=schemas.TradeSchema)
async def create_trade(trade: schemas.TradeCreate, db: AsyncSession = Depends(crud.get_db)):
    return await crud.create_trade(trade, db)

@app.delete("/trades/{uuid}")
async def remove_trade(user_uuid: str, uuid: str, db: AsyncSession = Depends(crud.get_db)):
    await crud.delete_trade(user_uuid, uuid, db)
    return {"detail": "Trade deleted"}

@app.delete("/trades/all/{user_uuid}")
async def remove_all_trades(user_uuid: str, db: AsyncSession = Depends(crud.get_db)):
    await crud.delete_all_trade(user_uuid, db)
    return {"detail": "All trades for the user have been deleted"}

# Additional endpoints can be added as needed