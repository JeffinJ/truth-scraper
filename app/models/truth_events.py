from collections import deque
from pydantic import BaseModel

from app.models.truths import TruthModel

class TruthEvent(BaseModel):
    data: TruthModel
    
    
class SSEEvent(BaseModel):
    EVENTS = deque()
    
    @staticmethod
    def add_event(self, event: TruthEvent):
        SSEEvent.EVENTS.append(event)
        
    @staticmethod
    def get_events(self):
        if len(SSEEvent.EVENTS) > 0:
            return SSEEvent.EVENTS.popleft()
        return None
    
    @staticmethod
    def count():
        return len(SSEEvent.EVENTS)
        
        