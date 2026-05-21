from pydantic_settings import BaseSettings


class Config(BaseSettings):
    bot_token: str
    gemini_api_key: str
    owner_user_id: int
    db_path: str = "data/bot.db"

    model_config = {"env_file": ".env"}


config = Config()
