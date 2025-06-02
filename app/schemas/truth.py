from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TruthSchema(BaseModel):
    id: int
    content: str
    timestamp: datetime
    url: str
    media_urls: Optional[List[str]] = []
    ai_summary: Optional[str] = None
    ai_context: Optional[str] = None
    ai_processed: bool = False
    ai_processing: bool = False

    class Config:
        from_attributes = True
