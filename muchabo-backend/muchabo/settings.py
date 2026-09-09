from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MUCHABO_", env_file=".env", extra="ignore")

    app_name: str = "muchabo backend"
    log_level: str = "INFO"


settings = Settings()