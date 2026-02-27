from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Ecommerce Bakong API"
    app_env: str = "development"
    app_debug: bool = True

    mongodb_url: str
    mongodb_db: str = "ecommerce_bakong"

    bakong_token: str
    bakong_account: str
    merchant_name: str
    merchant_city: str
    store_label: str
    phone_number: str
    frontend_url: str = "http://localhost:3000"

    payment_qr_expire_seconds: int = 180

    auth_secret_key: str
    auth_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    telegram_bot_token: str | None = None
    telegram_chat_id: str | None = None
    telegram_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
