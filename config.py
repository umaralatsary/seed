from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_ignore_empty=True)

    API_ID: int
    API_HASH: str
    TELEGRAM_ID: int = 1190101871
    AUTO_UPGRADE: bool = True
    AUTO_SPIN: bool = True
    AUTO_SELL_TRANSFER_EGG: bool = True
    AUTO_SELL_WORMS: bool = True
    PRICE_COMMON_EGG: int = 35
    PRICE_LEGENDARY_WORM: int = 69
    PRICE_EPIC_WORM: int = 9
    PRICE_RARE_WORM: int = 1

settings = Settings()