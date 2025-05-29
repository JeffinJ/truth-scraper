from sqlalchemy import Column, String, DateTime
from app.database.db_config import Base

class ScapingMetadataModel(Base):
    __tablename__ = "scraping_metadata"

    profile_id = Column(String, primary_key=True)
    last_scraped = Column(DateTime(timezone=True))
    last_post_timestamp = Column(DateTime(timezone=True))