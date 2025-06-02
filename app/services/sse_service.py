import asyncio
import logging
from typing import Dict, List, Any, Set

from app.schemas.truth import TruthSchema

logger = logging.getLogger(__name__)

class SSEManager:
    def __init__(self):
        self.connections: Set[asyncio.Queue] = set()
        
        
    async def add_connection(self, queue: asyncio.Queue):
        """Add a new SSE connection"""
        self.connections.add(queue)
        logger.info(f"New SSE connection added. Total connections: {len(self.connections)}")
        
    async def remove_connection(self, queue: asyncio.Queue):
        """Remove an SSE connection"""
        self.connections.discard(queue)
        logger.info(f"SSE connection removed. Total connections: {len(self.connections)}")
        
    async def broadcast_truths(self, truths_data: List[TruthSchema], broadcast_type: str):
        """Broadcast new truths to all connected SSE clients"""
        if not self.connections:
            logger.info("No SSE connections to broadcast to")
            return
        
        message = {
            "type": broadcast_type,
            "data": truths_data,
            "timestamp": str(asyncio.get_event_loop().time())
        }
        
        logger.info(f"🔥 Broadcasting {broadcast_type} for {len(truths_data)} truths to {len(self.connections)} connections")
        
        # Send to all connections
        disconnected_connections = set()
        for connection_queue in self.connections.copy():
            try:
                await connection_queue.put(message)
                logger.info(f"✅ Sent message to SSE connection: {message}")
            except Exception as e:
                logger.error(f"🔥 Error sending to SSE connection: {e}")
                disconnected_connections.add(connection_queue)
        
        # Remove disconnected connections
        for conn in disconnected_connections:
            await self.remove_connection(conn)
            
            
sse_manager = SSEManager()