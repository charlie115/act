from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal

class TradeConfigBase(BaseModel):
    uuid: UUID
    user: UUID
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
    safe_reverse: Optional[bool] = None
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
    user: Optional[UUID] = None
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
    last_trade_history_uuid: Optional[UUID] = None
    status: Optional[str] = None
    remark: Optional[str] = None

class TradeCreate(TradeBase):
    uuid: Optional[UUID] = None
    # uuid: UUID
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

class TradeLogBase(BaseModel):
    trade_uuid: UUID
    trade_config_uuid: UUID
    registered_datetime: datetime
    last_updated_datetime: datetime
    base_asset: str
    usdt_conversion: bool
    low: Decimal
    high: Decimal
    trade_capital: Optional[Decimal] = None
    deleted: Optional[bool] = False
    status: Optional[str] = None
    remark: Optional[str] = None
    
class TradeLogCreate(TradeLogBase):
    registered_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_updated_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
class TradeLogUpdate(TradeLogBase):
    trade_uuid: Optional[UUID] = None
    trade_config_uuid: Optional[UUID] = None
    registered_datetime: Optional[datetime] = None
    last_updated_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)
    base_asset: Optional[str] = None
    usdt_conversion: Optional[bool] = None
    low: Optional[Decimal] = None
    high: Optional[Decimal] = None
    
class TradeLog(TradeLogBase):
    id: int

    class Config:
        orm_mode = True

class RepeatTradeBase(BaseModel):
    uuid: UUID
    trade_uuid: UUID
    registered_datetime: datetime
    last_updated_datetime: datetime
    kline_interval: Optional[str] = None
    kline_num: Optional[int] = None
    pauto_num: Optional[Decimal] = None
    auto_repeat_switch: int
    auto_repeat_num: int
    status: Optional[str] = None
    remark: Optional[str] = None

class RepeatTradeCreate(RepeatTradeBase):
    uuid: Optional[UUID] = None
    registered_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_updated_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)
    
class RepeatTradeUpdate(RepeatTradeBase):
    uuid: Optional[UUID] = None
    trade_uuid: Optional[UUID] = None
    registered_datetime: Optional[datetime] = None
    last_updated_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)
    kline_interval: Optional[str] = None
    kline_num: Optional[int] = None
    pauto_num: Optional[Decimal] = None
    auto_repeat_switch: Optional[int] = None
    auto_repeat_num: Optional[int] = None
    status: Optional[str] = None
    remark: Optional[str] = None

class RepeatTrade(RepeatTradeBase):
    id: int

    class Config:
        orm_mode = True

class ExchangeApiKeyBase(BaseModel):
    uuid: UUID
    trade_config_uuid: UUID
    registered_datetime: datetime
    last_updated_datetime: datetime
    market_code: str
    exchange: str
    spot: bool
    futures: bool
    access_key: bytes  # Consider handling this differently if sensitive
    remark: Optional[str] = None

# Schema for request on user API key creation
class ExchangeApiKeyCreate(ExchangeApiKeyBase):
    uuid: Optional[UUID] = None
    trade_config_uuid: UUID
    registered_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)
    last_updated_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)
    market_code: str
    exchange: Optional[str] = None
    spot: Optional[bool] = None
    futures: Optional[bool] = None
    access_key: bytes
    secret_key: bytes
    passphrase: Optional[bytes] = None
    
# Schema for request on user API key update
class ExchangeApiKeyUpdate(ExchangeApiKeyBase):
    uuid: Optional[UUID] = None
    trade_config_uuid: Optional[UUID] = None
    registered_datetime: Optional[datetime] = None
    last_updated_datetime: Optional[datetime] = Field(default_factory=datetime.utcnow)
    market_code: Optional[str] = None
    exchange: Optional[str] = None
    spot: Optional[bool] = None
    futures: Optional[bool] = None
    access_key: Optional[bytes] = None
    secret_key: Optional[bytes] = None
    passphrase: Optional[bytes] = None
    remark: Optional[str] = None

# Schema for response model
class ExchangeApiKey(ExchangeApiKeyBase):
    id: int

    class Config:
        orm_mode = True
        
class OrderHistoryBase(BaseModel):
    order_id: str
    trade_config_uuid: UUID
    trade_uuid: UUID
    registered_datetime: datetime
    order_type: str
    market_code: str
    symbol: str
    quote_asset: str
    side: str
    price: Decimal
    qty: Decimal
    fee: Decimal
    remark: Optional[str] = None
    
class OrderHistory(OrderHistoryBase):
    id: int
    
    class Config:
        orm_mode = True
        
class TradeHistoryBase(BaseModel):
    uuid: UUID
    trade_config_uuid: UUID
    trade_uuid: UUID
    registered_datetime: datetime
    trade_side: str
    base_asset: str
    target_order_id: str
    origin_order_id: str
    target_premium_value: Decimal
    executed_premium_value: Decimal
    slippage_p: Decimal
    dollar: Decimal
    remark: Optional[str] = None
    
class TradeHistory(TradeHistoryBase):
    id: int
    
    class Config:
        orm_mode = True
        
class PnlHistoryBase(BaseModel):
    uuid: UUID
    trade_config_uuid: UUID
    trade_uuid: UUID
    registered_datetime: datetime
    market_code_combination: str
    enter_trade_history_uuid: UUID
    exit_trade_history_uuid: UUID
    realized_premium_gap_p: Decimal
    target_currency: str
    target_pnl: Decimal
    target_total_fee: Decimal
    target_pnl_after_fee: Decimal
    origin_currency: str
    origin_pnl: Decimal
    origin_total_fee: Decimal
    origin_pnl_after_fee: Decimal
    total_currency: str
    total_pnl: Decimal
    total_pnl_after_fee: Decimal
    total_pnl_after_fee_kimp: Optional[Decimal] = None # Temporary
    remark: Optional[str] = None
    
class PnlHistory(PnlHistoryBase):
    id: int
    
    class Config:
        orm_mode = True
        
######################## Schema without database #######################################
class SpotPosition(BaseModel):
    asset: str
    free: Decimal
    locked: Decimal

class USDMPosition(BaseModel):
    symbol: str
    base_asset: str
    entry_price: Decimal
    leverage: int
    qty: Decimal
    margin_type: str
    liquidation_price: Optional[Decimal] = None
    ROI: Optional[Decimal] = None

class COINMPosition(BaseModel):
    symbol: str
    base_asset: str
    entry_price: Decimal
    leverage: int
    qty: Decimal
    margin_type: str
    liquidation_price: Optional[Decimal] = None
    ROI: Optional[Decimal] = None

class Capital(BaseModel):
    currency: str
    free: Decimal
    locked: Decimal
    before_pnl: Decimal
    pnl: Decimal
    after_pnl: Decimal


# schemas for pboundary regression data processing
class RegressionLine(BaseModel):
    x: list
    y: list

class PredictedPoints(BaseModel):
    x: list
    y: list

class Pboundary(BaseModel):
   regression_line: RegressionLine
   predicted_points: PredictedPoints
   
# schemas for wallet deposit system
class DepositAddress(BaseModel):
    asset: str
    address: str
    tag: Optional[str] = None

class DepositHistory(BaseModel):
    status: str
    deposited: bool
    amount: Decimal
    
# schemas for executing EXIT trades
class ExitTrade(BaseModel):
    trade_uuid: UUID
    trade_config_uuid: UUID
    base_asset: str
    usdt_conversion: bool
    low: Decimal
    high: Decimal
    trade_capital: Decimal
    last_trade_history_uuid: UUID
    status: str
    remark: Optional[str] = None