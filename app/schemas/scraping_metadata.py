from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ScrapingMetadata(BaseModel):
    profile_id: str
    last_scraped: datetime
    last_post_timestamp: datetime
    
    
class ScrapingMetadataCreate(ScrapingMetadata):
    """Schema for creating new scraping metadata"""
    pass


class ScrapingMetadataUpdate(BaseModel):
    """Schema for updating scraping metadata"""
    last_scraped_at: Optional[datetime] = None
    last_post_timestamp: Optional[datetime] = None