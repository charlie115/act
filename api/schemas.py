from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

# User Info Schema
class UserInfoSchema(BaseModel):
    id: Optional[int] = None
    user_uuid: str
    email: Optional[str] = None
    telegram_id: Optional[int] = None
    telegram_name: Optional[str] = None
    registered_datetime: Optional[datetime] = None
    status: Optional[str] = None
    alarm_num: Optional[int] = None
    alarm_period: Optional[int] = None
    remark: Optional[str] = None

    class Config:
        orm_mode = True

class UserInfoCreate(BaseModel):
    user_uuid: str
    email: str
    telegram_id: int
    telegram_name: Optional[str] = None
    status: Optional[str] = None
    alarm_num: 1
    alarm_period: 1
    remark: Optional[str] = None

# Exchange Config Schema
class ExchangeConfigSchema(BaseModel):
    id: Optional[int] = None
    user_uuid: str
    registered_datetime: Optional[datetime] = None
    service_datetime_end: Optional[datetime] = None
    target_market_code: Optional[str] = None
    origin_market_code: Optional[str] = None
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
    target_market_risk_threshold_p: Optional[float] = None
    origin_market_risk_threshold_p: Optional[float] = None
    repeat_limit_p: Optional[float] = None
    repeat_limit_direction: Optional[str] = None
    repeat_num_limit: Optional[int] = None
    on_off: Optional[bool] = None
    remark: Optional[str] = None

    class Config:
        orm_mode = True

class ExchangeConfigCreate(BaseModel):
    user_uuid: str
    service_datetime_end: Optional[datetime] = None
    target_market_code: Optional[str] = None
    origin_market_code: Optional[str] = None
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
    target_market_risk_threshold_p: Optional[float] = None
    origin_market_risk_threshold_p: Optional[float] = None
    repeat_limit_p: Optional[float] = None
    repeat_limit_direction: Optional[str] = None
    repeat_num_limit: Optional[int] = None
    on_off: Optional[bool] = None
    remark: Optional[str] = None

# Repeat Trade Schema
class RepeatTradeSchema(BaseModel):
    id: Optional[int] = None
    user_uuid: str
    last_update_datetime: Optional[datetime] = None
    uuid: str
    base_asset: str
    usdt_conversion: bool
    auto_low: Optional[float] = None
    auto_high: Optional[float] = None
    pauto_num: Optional[float] = None
    switch: Optional[int] = None
    repeat_switch: Optional[int] = None
    repeat_capital: Optional[float] = None
    repeat_num: Optional[int] = None
    status: str
    remark: Optional[str] = None

    class Config:
        orm_mode = True

class RepeatTradeCreate(BaseModel):
    user_uuid: str
    uuid: str
    base_asset: str
    usdt_conversion: bool
    auto_low: Optional[float] = None
    auto_high: Optional[float] = None
    pauto_num: Optional[float] = None
    switch: Optional[int] = None
    repeat_switch: Optional[int] = None
    repeat_capital: Optional[float] = None
    repeat_num: Optional[int] = None
    status: str
    remark: Optional[str] = None

# Trade Schema
class TradeSchema(BaseModel):
    id: Optional[int] = None
    user_uuid: str
    registered_datetime: Optional[datetime] = None
    last_updated_datetime: Optional[datetime] = None
    uuid: str
    connected_repeat_uuid: Optional[str] = None
    base_asset: str
    usdt_conversion: bool
    target_market_code: str
    origin_market_code: str
    low: float
    high: float
    trigger_switch: Optional[int] = None
    trade_switch: Optional[int] = None
    trade_capital: Optional[float] = None
    enter_target_market_order_id: Optional[str] = None
    enter_origin_market_order_id: Optional[str] = None
    exit_target_market_order_id: Optional[str] = None
    exit_origin_market_order_id: Optional[str] = None
    status: Optional[str] = None
    remark: Optional[str] = None

    class Config:
        orm_mode = True

class TradeCreate(BaseModel):
    user_uuid: str
    uuid: str
    connected_repeat_uuid: Optional[str] = None
    base_asset: str
    usdt_conversion: bool
    target_market_code: str
    origin_market_code: str
    low: float
    high: float
    trigger_switch: Optional[int] = None
    trade_switch: Optional[int] = None
    trade_capital: Optional[float] = None
    enter_target_market_order_id: Optional[str] = None
    enter_origin_market_order_id: Optional[str] = None
    exit_target_market_order_id: Optional[str] = None
    exit_origin_market_order_id: Optional[str] = None
    status: str
    remark: Optional[str] = None