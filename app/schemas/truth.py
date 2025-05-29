from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TruthSchema(BaseModel):
    id: int
    content: str
    timestamp: datetime
    url: str
    media_urls: Optional[List[str]] = []

    class Config:
        from_attributes = True
