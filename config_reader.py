from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


class Settings(BaseSettings):
    MAIN_ADMIN_ID: SecretStr

    TG_BOT_TOKEN: SecretStr
    TG_BOT_USERNAME: str

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str

    @property
    def DB_URL_SYNC(self):
        return f'postgresql+psycopg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    @property
    def DB_URL_ASYNC(self):
        return f'postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}'

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

config = Settings()