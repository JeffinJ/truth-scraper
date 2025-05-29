from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    truth_profile_username: str
    truth_scraper_interval: int
    
    class Config:
        env_file = ".env"


settings = Settings()

