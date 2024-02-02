from sqlalchemy import BigInteger, Boolean, Column, DateTime, Numeric, ForeignKey, Integer, SmallInteger, Text, text
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
    acw_user_uuid = Column(UUID(as_uuid=True), nullable=False)
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
    target_market_safe_reverse = Column(Boolean)
    origin_market_safe_reverse = Column(Boolean)
    target_market_risk_threshold_p = Column(Numeric(3, 3))
    origin_market_risk_threshold_p = Column(Numeric(3, 3))
    repeat_limit_p = Column(Numeric(3, 3))
    repeat_limit_direction = Column(Text)
    repeat_num_limit = Column(Integer)
    on_off = Column(Boolean)
    remark = Column(Text)


class Trade(Base):
    __tablename__ = 'trade'

    id = Column(Integer, primary_key=True, server_default=text("nextval('trade_id_seq'::regclass)"))
    uuid = Column(UUID(as_uuid=True), unique=True, server_default=text("gen_random_uuid()"))
    trade_config_uuid = Column(ForeignKey('trade_config.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    registered_datetime = Column(DateTime)
    last_updated_datetime = Column(DateTime)
    base_asset = Column(Text, nullable=False)
    usdt_conversion = Column(Boolean, nullable=False)
    low = Column(Numeric(5, 3), nullable=False)
    high = Column(Numeric(5, 3), nullable=False)
    trigger_switch = Column(SmallInteger)
    trade_switch = Column(SmallInteger)
    trade_capital = Column(Integer)
    enter_target_market_order_id = Column(Text)
    enter_origin_market_order_id = Column(Text)
    exit_target_market_order_id = Column(Text)
    exit_origin_market_order_id = Column(Text)
    status = Column(Text)
    remark = Column(Text)

    trade_config = relationship('TradeConfig')


class RepeatTrade(Base):
    __tablename__ = 'repeat_trade'

    id = Column(Integer, primary_key=True, server_default=text("nextval('repeat_trade_id_seq'::regclass)"))
    uuid = Column(UUID(as_uuid=True), unique=True, server_default=text("gen_random_uuid()"))
    trade_uuid = Column(ForeignKey('trade.uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    registered_datetime = Column(DateTime)
    last_update_datetime = Column(DateTime)
    pauto_num = Column(Numeric(3, 3))
    switch = Column(SmallInteger)
    auto_trade_switch = Column(SmallInteger)
    enter_target_market_order_id = Column(Text)
    enter_origin_market_order_id = Column(Text)
    exit_target_market_order_id = Column(Text)
    exit_origin_market_order_id = Column(Text)
    status = Column(Text, nullable=False)
    remark = Column(Text)

    trade = relationship('Trade')