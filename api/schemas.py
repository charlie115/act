from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class TradeConfigBase(BaseModel):
    uuid: UUID
    acw_user_uuid: UUID
    telegram_id: int
    send_times: int
    send_term: int
    registered_datetime: datetime
    service_datetime_end: Optional[datetime] = None
    target_market_code: str
    origin_market_code: str
    target_market_uid: Optional[str] = None
    origin_market_uid: Optional[str] = None
    target_market_referral_use: Optional[bool] = None
    origin_market_referral_use: Optional[bool] = None
    target_market_cross: Optional[bool] = None
    target_market_leverage: Optional[int] = None
    origin_market_cross: Optional[bool] = None
    origin_market_leverage: Optional[int] = None
    target_market_margin_call: Optional[int] = None
    origin_market_margin_call: Optional[int] = None
    target_market_safe_reverse: Optional[bool] = None
    origin_market_safe_reverse: Optional[bool] = None
    target_market_risk_threshold_p: Optional[Decimal] = None
    origin_market_risk_threshold_p: Optional[Decimal] = None
    repeat_limit_p: Optional[Decimal] = None
    repeat_limit_direction: Optional[str] = None
    repeat_num_limit: Optional[int] = None
    on_off: Optional[bool] = None
    remark: Optional[str] = None

class TradeConfigCreate(TradeConfigBase):
    uuid: Optional[UUID] = None
    send_times: Optional[int] = 1
    send_term: Optional[int] = 1
    registered_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)
    service_datetime_end: Optional[datetime] = Field(default_factory=datetime.utcnow)
    on_off: Optional[bool] = True

class TradeConfigUpdate(TradeConfigBase):
    uuid: Optional[UUID] = None
    acw_user_uuid: Optional[UUID] = None
    telegram_id: Optional[int] = None
    send_times: Optional[int] = None
    send_term: Optional[int] = None
    registered_datetime: Optional[datetime] = None
    target_market_code: Optional[str] = None
    origin_market_code: Optional[str] = None

class TradeConfig(TradeConfigBase):
    id: int

    class Config:
        orm_mode = True

class TradeBase(BaseModel):
    uuid: UUID
    trade_config_uuid: UUID
    registered_datetime: datetime
    last_updated_datetime: datetime
    base_asset: str
    usdt_conversion: bool
    low: Decimal
    high: Decimal
    trigger_switch: Optional[int] = None
    trade_switch: Optional[int] = None
    trade_capital: Optional[Decimal] = None
    enter_target_market_order_id: Optional[str] = None
    enter_origin_market_order_id: Optional[str] = None
    exit_target_market_order_id: Optional[str] = None
    exit_origin_market_order_id: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None

class TradeCreate(TradeBase):
    uuid: Optional[UUID] = None
    trade_config_uuid: UUID
    registered_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_updated_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)

class TradeUpdate(TradeBase):
    uuid: Optional[UUID] = None
    trade_config_uuid: Optional[UUID] = None
    registered_datetime: Optional[datetime] = None
    last_updated_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)
    base_asset: Optional[str] = None
    usdt_conversion: Optional[bool] = None
    low: Optional[Decimal] = None
    high: Optional[Decimal] = None

class Trade(TradeBase):
    id: int

    class Config:
        orm_mode = True

class RepeatTradeBase(BaseModel):
    uuid: UUID
    trade_uuid: UUID
    registered_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_update_datetime: Optional[datetime] = None
    pauto_num: Optional[Decimal] = None
    switch: Optional[int] = None
    auto_trade_switch: Optional[int] = None
    enter_target_market_order_id: Optional[str] = None
    enter_origin_market_order_id: Optional[str] = None
    exit_target_market_order_id: Optional[str] = None
    exit_origin_market_order_id: Optional[str] = None
    status: str
    remark: Optional[str] = None

class RepeatTradeCreate(RepeatTradeBase):
    uuid: Optional[UUID] = None
    registered_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_update_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)

class RepeatTrade(RepeatTradeBase):
    id: int

    class Config:
        orm_mode = True