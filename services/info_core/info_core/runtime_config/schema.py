from dataclasses import dataclass


@dataclass(frozen=True)
class MongoConfig:
    host: str
    port: int
    user: str | None
    passwd: str | None


@dataclass(frozen=True)
class RedisConfig:
    host: str
    port: int
    passwd: str | None


@dataclass(frozen=True)
class ExchangeReadOnlyConfig:
    api_key: str | None
    secret_key: str | None
    passphrase: str | None = None


@dataclass(frozen=True)
class InfoCoreRuntimeConfig:
    prod: bool
    node: str
    master: bool
    proc_n: int
    logging_dir: str
    config_path: str
    admin_telegram_id: int
    staff_telegram_id_list: list[int]
    acw_api_url: str
    ai_api_key: str | None
    enabled_market_klines: list[str]
    enabled_arbitrage_markets: list[str]
    mongodb: MongoConfig
    redis: RedisConfig
    exchange_api_key_dict: dict

    @property
    def mongodb_dict(self):
        return {
            "host": self.mongodb.host,
            "port": self.mongodb.port,
            "user": self.mongodb.user,
            "passwd": self.mongodb.passwd,
        }

    @property
    def redis_dict(self):
        return {
            "host": self.redis.host,
            "port": self.redis.port,
            "passwd": self.redis.passwd,
        }
