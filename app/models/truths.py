from sqlalchemy import Column, String, DateTime, Text, ARRAY, Boolean
from sqlalchemy.dialects.postgresql import BIGINT
from app.database.db_config import Base

class TruthModel(Base):
    __tablename__ = "truths"

    id = Column(BIGINT, primary_key=True)
    content = Column(Text)
    timestamp = Column(DateTime(timezone=True))
    url = Column(String, unique=True)
    media_urls = Column(ARRAY(String))
    ai_context = Column(Text, nullable=True)
    ai_processed = Column(Boolean, default=False)
    ai_processing = Column(Boolean, default=False)