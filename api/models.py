from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, SmallInteger, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from .database import Base

class UserInfo(Base):
    __tablename__ = 'user_info'

    id = Column(Integer, primary_key=True, server_default=text("nextval('user_info_id_seq'::regclass)"))
    user_uuid = Column(Text, nullable=False, unique=True)
    email = Column(Text)
    telegram_id = Column(BigInteger)
    telegram_name = Column(Text)
    registered_datetime = Column(DateTime)
    status = Column(Text)
    alarm_num = Column(Integer)
    alarm_period = Column(Integer)
    remark = Column(Text)


class ExchangeConfig(Base):
    __tablename__ = 'exchange_config'

    id = Column(Integer, primary_key=True, server_default=text("nextval('exchange_config_id_seq'::regclass)"))
    user_uuid = Column(ForeignKey('user_info.user_uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    registered_datetime = Column(DateTime)
    service_datetime_end = Column(DateTime)
    target_market_code = Column(Text)
    origin_market_code = Column(Text)
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
    target_market_risk_threshold_p = Column(Float)
    origin_market_risk_threshold_p = Column(Float)
    repeat_limit_p = Column(Float)
    repeat_limit_direction = Column(Text)
    repeat_num_limit = Column(Integer)
    on_off = Column(Boolean)
    remark = Column(Text)

    user_info = relationship('UserInfo')


class RepeatTrade(Base):
    __tablename__ = 'repeat_trade'

    id = Column(Integer, primary_key=True, server_default=text("nextval('repeat_trade_id_seq'::regclass)"))
    user_uuid = Column(ForeignKey('user_info.user_uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    last_update_datetime = Column(DateTime)
    uuid = Column(Text, nullable=False)
    base_asset = Column(Text, nullable=False)
    usdt_conversion = Column(Boolean, nullable=False)
    auto_low = Column(Float)
    auto_high = Column(Float)
    pauto_num = Column(Float)
    switch = Column(SmallInteger)
    repeat_switch = Column(SmallInteger)
    repeat_capital = Column(Float)
    repeat_num = Column(Integer)
    status = Column(Text, nullable=False)
    remark = Column(Text)

    user_info = relationship('UserInfo')


class Trade(Base):
    __tablename__ = 'trade'

    id = Column(Integer, primary_key=True, server_default=text("nextval('trade_id_seq'::regclass)"))
    user_uuid = Column(ForeignKey('user_info.user_uuid', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    registered_datetime = Column(DateTime)
    last_updated_datetime = Column(DateTime)
    uuid = Column(Text, nullable=False)
    connected_repeat_uuid = Column(Text)
    base_asset = Column(Text, nullable=False)
    usdt_conversion = Column(Boolean, nullable=False)
    target_market_code = Column(Text, nullable=False)
    origin_market_code = Column(Text, nullable=False)
    low = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    trigger_switch = Column(SmallInteger)
    trade_switch = Column(SmallInteger)
    trade_capital = Column(Float)
    enter_target_market_order_id = Column(Text)
    enter_origin_market_order_id = Column(Text)
    exit_target_market_order_id = Column(Text)
    exit_origin_market_order_id = Column(Text)
    status = Column(Text)
    remark = Column(Text)

    user_info = relationship('UserInfo')