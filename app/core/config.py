from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    database_url: str
    truth_profile_username: str
    truth_scraper_interval: int
    origins: List[str] = Field(alias="ORIGINS")

    model_config = SettingsConfigDict(env_file=".env", populate_by_name=True)

settings = Settings()
