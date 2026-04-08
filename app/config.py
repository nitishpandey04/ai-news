from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"

    database_url: str = "postgresql+asyncpg://newsuser:newspass@db:5432/newsdb"
    redis_url: str = "redis://redis:6379/0"

    whatsapp_access_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = "whatsapp_verify_secret"

    dispatch_tick_interval_seconds: int = 300


settings = Config()
