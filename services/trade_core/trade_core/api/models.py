from sqlalchemy import BigInteger, Boolean, Column, DateTime, Numeric, ForeignKey, Integer, SmallInteger, Text, text
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from database import Base

class TradeConfig(Base):
    __tablename__ = 'trade_config'

    id = Column(Integer, primary_key=True, server_default=text("nextval('trade_config_id_seq'::regclass)"))
    uuid = Column(UUID(as_uuid=True), unique=True, server_default=text("gen_random_uuid()"))
    user = Column(UUID(as_uuid=True), nullable=False)
    telegram_id = Column(BigInteger, nullable=False)
    send_times = Column(Integer)
    send_term = Column(Integer)
    registered_datetime = Column(DateTime)
    service_datetime_end = Column(DateTime)
    target_market_code = Column(Text, nullable=False)
    origin_market_code = Column(Text, nullable=False)
    target_market_uid = Column(Text)
    origin_market_uid = Column(Text)
    target_market_referral_use = Column(Boolean)
    origin_market_referral_use = Column(Boolean)
    target_market_cross = Column(Boolean)
    target_market_leverage = Column(Integer)
    origin_market_cross = Column(Boolean)
    origin_market_leverage = Column(Integer)
    target_market_margin_call = Column(SmallInteger)
    origin_market_margin_call = Column(SmallInteger)
    safe_reverse = Column(Boolean)
    target_market_risk_threshold_p = Column(Numeric(6, 3))
    origin_market_risk_threshold_p = Column(Numeric(6, 3))
    repeat_limit_p = Column(Numeric(6, 3))
    repeat_limit_direction = Column(Text)
    repeat_num_limit = Column(Integer)
    on_off = Column(Boolean)
    remark = Column(Text)


class Trade(Base):
    __tablename__ = 'trade'

    id = Column(Integer, primary_key=True, server_default=text("nextval('trade_id_seq'::regclass)"))
    # uuid = Column(UUID(as_uuid=True), unique=True, server_default=text("gen_random_uuid()"))
    uuid = Column(UUID(as_uuid=True), unique=True, nullable=False)
    trade_config_uuid = Column(ForeignKey('trade_config.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    registered_datetime = Column(DateTime)
    last_updated_datetime = Column(DateTime)
    base_asset = Column(Text, nullable=False)
    usdt_conversion = Column(Boolean, nullable=False)
    low = Column(Numeric(8, 3), nullable=False)
    high = Column(Numeric(8, 3), nullable=False)
    trigger_switch = Column(SmallInteger)
    trade_switch = Column(SmallInteger)
    trade_capital = Column(Integer)
    last_trade_history_uuid = Column(ForeignKey('trade_history.uuid', ondelete='SET NULL', onupdate='CASCADE'))
    trigger_scanner_uuid = Column(ForeignKey('trigger_scanner.uuid', ondelete='SET NULL', onupdate='CASCADE'))
    status = Column(Text)
    remark = Column(Text)

    trade_config = relationship('TradeConfig')
    
class TradeLog(Base):
    __tablename__ = 'trade_log'

    id = Column(Integer, primary_key=True, server_default=text("nextval('trade_id_seq'::regclass)"))
    trade_uuid = Column(UUID(as_uuid=True), nullable=False)
    trade_config_uuid = Column(ForeignKey('trade_config.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    registered_datetime = Column(DateTime)
    last_updated_datetime = Column(DateTime)
    base_asset = Column(Text, nullable=False)
    usdt_conversion = Column(Boolean, nullable=False)
    low = Column(Numeric(8, 3), nullable=False)
    high = Column(Numeric(8, 3), nullable=False)
    trade_capital = Column(Integer)
    deleted = Column(Boolean)
    status = Column(Text)
    remark = Column(Text)

    trade_config = relationship('TradeConfig')

class RepeatTrade(Base):
    __tablename__ = 'repeat_trade'

    id = Column(Integer, primary_key=True, server_default=text("nextval('repeat_trade_id_seq'::regclass)"))
    uuid = Column(UUID(as_uuid=True), unique=True, server_default=text("gen_random_uuid()"))
    trade_uuid = Column(ForeignKey('trade.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    registered_datetime = Column(DateTime)
    last_updated_datetime = Column(DateTime)
    kline_interval = Column(Text)
    kline_num = Column(Integer)
    pauto_num = Column(Numeric(6, 3))
    auto_repeat_switch = Column(SmallInteger)
    auto_repeat_num = Column(Integer)
    status = Column(Text, nullable=False)
    remark = Column(Text)

    trade = relationship('Trade')

class ExchangeApiKey(Base):
    __tablename__ = 'exchange_api_key'

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), unique=True, server_default=text("gen_random_uuid()"))
    trade_config_uuid = Column(ForeignKey('trade_config.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    registered_datetime = Column(DateTime)
    last_updated_datetime = Column(DateTime)
    market_code = Column(Text, nullable=False)
    exchange = Column(Text, nullable=False)
    spot = Column(Boolean, nullable=False)
    futures = Column(Boolean, nullable=False)
    access_key = Column(BYTEA, nullable=False)
    secret_key = Column(BYTEA, nullable=False)
    passphrase = Column(BYTEA)
    remark = Column(Text)

    trade_config = relationship('TradeConfig')
    
class OrderHistory(Base):
    __tablename__ = 'order_history'
    
    id = Column(Integer, primary_key=True, server_default=text("nextval('order_history_id_seq'::regclass)"))
    order_id = Column(Text, unique=True, nullable=False)
    trade_config_uuid = Column(ForeignKey('trade_config.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    trade_uuid = Column(ForeignKey('trade_log.trade_uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    registered_datetime = Column(DateTime)
    order_type = Column(Text, nullable=False)
    market_code = Column(Text, nullable=False)
    symbol = Column(Text, nullable=False)
    quote_asset = Column(Text, nullable=False)
    side = Column(Text, nullable=False)
    price = Column(Numeric(21, 11), nullable=False)
    qty = Column(Numeric(22, 9), nullable=False)
    fee = Column(Numeric(15, 9))
    remark = Column(Text)

    trade_config = relationship('TradeConfig')
    trade_log = relationship('TradeLog')

class TradeHistory(Base):
    __tablename__ = "trade_history"

    id = Column(Integer, primary_key=True, server_default=text("nextval('trade_history_id_seq'::regclass)"))
    uuid = Column(UUID(as_uuid=True), unique=True, server_default=text("gen_random_uuid()"))
    trade_config_uuid = Column(ForeignKey('trade_config.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    trade_uuid = Column(ForeignKey('trade_log.trade_uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    registered_datetime = Column(DateTime)
    trade_side = Column(Text, nullable=False)
    base_asset = Column(Text, nullable=False)
    target_order_id = Column(ForeignKey('order_history.order_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    origin_order_id = Column(ForeignKey('order_history.order_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    target_premium_value = Column(Numeric(8, 3), nullable=False)
    executed_premium_value = Column(Numeric(8, 3), nullable=False)
    slippage_p = Column(Numeric(6, 3), nullable=False)
    dollar = Column(Numeric(5, 1), nullable=False)
    remark = Column(Text)

    # Relationships (optional, for ORM use)
    origin_order = relationship('OrderHistory', primaryjoin='TradeHistory.origin_order_id == OrderHistory.order_id')
    target_order = relationship('OrderHistory', primaryjoin='TradeHistory.target_order_id == OrderHistory.order_id')
    trade_config = relationship('TradeConfig')
    trade_log = relationship('TradeLog')
    
class PnlHistory(Base):
    __tablename__ = 'pnl_history'

    id = Column(Integer, primary_key=True, server_default=text("nextval('pnl_history_id_seq'::regclass)"))
    uuid = Column(UUID(as_uuid=True), unique=True, server_default=text("gen_random_uuid()"))
    trade_config_uuid = Column(ForeignKey('trade_config.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    trade_uuid = Column(ForeignKey('trade_log.trade_uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    registered_datetime = Column(DateTime)
    market_code_combination = Column(Text, nullable=False)
    enter_trade_history_uuid = Column(ForeignKey('trade_history.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    exit_trade_history_uuid = Column(ForeignKey('trade_history.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    realized_premium_gap_p = Column(Numeric(6, 3), nullable=False)
    target_currency = Column(Text, nullable=False)
    target_pnl = Column(Numeric(13, 6), nullable=False)
    target_total_fee = Column(Numeric(13, 6), nullable=False)
    target_pnl_after_fee = Column(Numeric(13, 6), nullable=False)
    origin_currency = Column(Text, nullable=False)
    origin_pnl = Column(Numeric(13, 6), nullable=False)
    origin_total_fee = Column(Numeric(13, 6), nullable=False)
    origin_pnl_after_fee = Column(Numeric(13, 6), nullable=False)
    total_currency = Column(Text, nullable=False)
    total_pnl = Column(Numeric(13, 6), nullable=False)
    total_pnl_after_fee = Column(Numeric(13, 6), nullable=False)
    total_pnl_after_fee_kimp = Column(Numeric(13, 6))
    remark = Column(Text)

    trade_history = relationship('TradeHistory', primaryjoin='PnlHistory.enter_trade_history_uuid == TradeHistory.uuid')
    trade_history1 = relationship('TradeHistory', primaryjoin='PnlHistory.exit_trade_history_uuid == TradeHistory.uuid')
    trade_config = relationship('TradeConfig')
    trade_log = relationship('TradeLog')

class TriggerScanner(Base):
    __tablename__ = 'trigger_scanner'

    id = Column(Integer, primary_key=True, server_default=text("nextval('trigger_scanner_id_seq'::regclass)"))
    uuid = Column(UUID(as_uuid=True), unique=True, server_default=text("gen_random_uuid()"))
    trade_config_uuid = Column(ForeignKey('trade_config.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    registered_datetime = Column(DateTime)
    last_updated_datetime = Column(DateTime)
    low = Column(Numeric(8, 3), nullable=False)
    high = Column(Numeric(8, 3), nullable=False)
    min_target_atp = Column(Numeric(20, 3))
    min_origin_atp = Column(Numeric(20, 3))
    min_target_funding_rate = Column(Numeric(8, 6))
    min_origin_funding_rate = Column(Numeric(8, 6))
    funding_rate_diff_threshold = Column(Numeric(8, 6))
    between_futures = Column(Boolean)
    trade_capital = Column(Integer)
    curr_repeat_num = Column(Integer, server_default=text("0"))
    max_repeat_num = Column(Integer)
    repeat_term_secs = Column(Integer, server_default=text("300"))
    remark = Column(Text)

    trade_config = relationship('TradeConfig')