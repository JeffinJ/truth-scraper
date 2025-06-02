from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    truth_profile_username: str = Field(alias="TRUTH_PROFILE_USERNAME")
    truth_scraper_interval: int = Field(alias="TRUTH_SCRAPER_INTERVAL")
    origins: List[str] = Field(alias="ORIGINS")
    truth_social_base_url: str = Field(alias="TRUTH_SOCIAL_BASE_URL", default="https://truthsocial.com")
    openai_api_key: str = Field(alias="OPENAI_API_KEY")
    ai_enabled: bool = True
    ai_workers: int = 2
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        populate_by_name=True,
        env_file_encoding='utf-8'
    )

settings = Settings()