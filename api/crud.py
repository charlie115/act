from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
import models
import schemas
import database
import uuid

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_info(user_uuid: str, db: Session = Depends(get_db)):
    user_info = db.query(models.UserInfo).filter(models.UserInfo.user_uuid == user_uuid).first()
    if user_info is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user_info

def create_user_info(user_info: schemas.UserInfoCreate, db: Session = Depends(get_db)):
    user_uuid = uuid.uuid4().hex
    db_user_info = models.UserInfo(user_uuid=user_uuid, **user_info.dict())
    db.add(db_user_info)
    db.commit()
    db.refresh(db_user_info)
    return db_user_info

def update_user_info(user_uuid: str, user_info: schemas.UserInfoUpdate, db: Session = Depends(get_db)):
    db_user_info = db.query(models.UserInfo).filter(models.UserInfo.user_uuid == user_uuid).first()
    if db_user_info is None:
        raise HTTPException(status_code=404, detail="User not found")
    for var, value in vars(user_info).items():
        if value is not None:
            setattr(db_user_info, var, value)
    db.commit()
    db.refresh(db_user_info)
    return db_user_info

def get_exchange_config(user_uuid: str, target_market_code: str, origin_market_code: str, db: Session = Depends(get_db)):
    exchange_config = db.query(models.ExchangeConfig).filter(models.ExchangeConfig.user_uuid == user_uuid, models.ExchangeConfig.target_market_code == target_market_code, models.ExchangeConfig.origin_market_code == origin_market_code).first()
    if exchange_config is None:
        raise HTTPException(status_code=404, detail="Exchange config not found")
    return exchange_config

def create_exchange_config(exchange_config: schemas.ExchangeConfigCreate, db: Session = Depends(get_db)):
    db_exchange_config = models.ExchangeConfig(**exchange_config.dict())
    db.add(db_exchange_config)
    db.commit()
    db.refresh(db_exchange_config)
    return db_exchange_config

def update_exchange_config(user_uuid: str, target_market_code: str, origin_market_code: str, exchange_config: schemas.ExchangeConfigUpdate, db: Session = Depends(get_db)):
    db_exchange_config = db.query(models.ExchangeConfig).filter(models.ExchangeConfig.user_uuid == user_uuid, models.ExchangeConfig.target_market_code == target_market_code, models.ExchangeConfig.origin_market_code == origin_market_code).first()
    if db_exchange_config is None:
        raise HTTPException(status_code=404, detail="Exchange config not found")
    for var, value in vars(exchange_config).items():
        if value is not None:
            setattr(db_exchange_config, var, value)
    db.commit()
    db.refresh(db_exchange_config)
    return db_exchange_config

def get_trade(user_uuid: str, uuid: str, db: Session = Depends(get_db)):
    trade = db.query(models.Trade).filter(models.Trade.user_uuid == user_uuid, models.Trade.uuid == uuid).first()
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade

def get_all_trade(user_uuid: str, db: Session = Depends(get_db)):
    trade = db.query(models.Trade).filter(models.Trade.user_uuid == user_uuid).all()
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade

def create_trade(trade: schemas.TradeCreate, db: Session = Depends(get_db)):
    uuid = uuid.uuid4().hex
    db_trade = models.Trade(uuid=uuid, **trade.dict())
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade

def delete_trade(user_uuid: str, uuid: str, db: Session = Depends(get_db)):
    trade = db.query(models.Trade).filter(models.Trade.user_uuid == user_uuid, models.Trade.uuid == uuid).first()
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    db.delete(trade)
    db.commit()
    return trade

def delete_all_trade(user_uuid: str, db: Session = Depends(get_db)):
    trade = db.query(models.Trade).filter(models.Trade.user_uuid == user_uuid).all()
    if trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    db.delete(trade)
    db.commit()
    return trade

def update_trade(user_uuid: str, uuid: str, trade: schemas.TradeUpdate, db: Session = Depends(get_db)):
    db_trade = db.query(models.Trade).filter(models.Trade.user_uuid == user_uuid, models.Trade.uuid == uuid).first()
    if db_trade is None:
        raise HTTPException(status_code=404, detail="Trade not found")
    for var, value in vars(trade).items():
        if value is not None:
            setattr(db_trade, var, value)
    db.commit()
    db.refresh(db_trade)
    return db_trade
