import asyncio
import json
from fastapi import APIRouter, Request
import logging
from sse_starlette.sse import EventSourceResponse
from app.services.sse_service import sse_manager

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/truths-sse/stream")
async def stream_truths(request: Request):
    async def event_generator():
        connection_queue = asyncio.Queue()
        
        try:
            await sse_manager.add_connection(connection_queue)
            yield {
                "event": "connected",
                "data": json.dumps({"message": "Connected to Truth Social stream"})
            }
            
            logger.info("🔥 New SSE client connected")
            
            while True:
                if await request.is_disconnected():
                    logger.info("🔥 SSE client disconnected")
                    break
                
                try:
                    message = await asyncio.wait_for(connection_queue.get(), timeout=30.0)
                    yield {
                        "event": "truths",
                        "data": json.dumps(message)
                    }
                    
                except asyncio.TimeoutError:
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({"timestamp": str(asyncio.get_event_loop().time())})
                    }
                    
                except Exception as e:
                    logger.error(f"🔥 Error in SSE event generator: {e}")
                    break
        
        except Exception as e:
            logger.error(f"🔥 Error in SSE connection: {e}")
        
        finally:
            # Clean up connection
            await sse_manager.remove_connection(connection_queue)
            logger.info("🔥 SSE connection cleaned up")
    
    return EventSourceResponse(event_generator())
