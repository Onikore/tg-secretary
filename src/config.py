from pydantic_settings import BaseSettings


class Config(BaseSettings):
    bot_token: str
    gemini_api_key: str
    owner_user_id: int
    db_path: str = "data/bot.db"
    tz_offset_min: int = 0
    proxy_url: str = ""

    model_config = {"env_file": ".env"}


config = Config()
