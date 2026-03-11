from __future__ import annotations

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
class PostgresConfig:
    host: str
    port: int
    user: str
    passwd: str


@dataclass(frozen=True)
class ExchangeReadOnlyConfig:
    api_key: str | None
    secret_key: str | None
    passphrase: str | None = None


@dataclass(frozen=True)
class TradeCoreRuntimeConfig:
    prod: bool
    node: str
    proc_n: int
    logging_dir: str
    config_path: str
    admin_telegram_id: int
    staff_telegram_id_list: list[int]
    acw_api_url: str
    encryption_key: str | None
    openai_api_key: str | None
    mongodb: MongoConfig
    redis: RedisConfig
    postgres: PostgresConfig
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

    @property
    def postgres_db_dict(self):
        return {
            "host": self.postgres.host,
            "port": self.postgres.port,
            "user": self.postgres.user,
            "passwd": self.postgres.passwd,
        }
