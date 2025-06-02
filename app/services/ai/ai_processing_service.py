import asyncio
import logging
from typing import List
from app.schemas.truth import TruthSchema
from app.services.ai.openai_service import OpenAIService
from app.repositories.truth_repository import TruthRepository
from app.services.sse_service import sse_manager
from app.database.db_config import async_session

logger = logging.getLogger(__name__)

class AIProcessingService:
    def __init__(
            self,
        ):
        self.ai_service = OpenAIService()
        self.processing_queue = asyncio.Queue()
        self.is_running = False
        self.worker_tasks = []
    
    async def start(self, num_workers: int = 2):
        """Start AI processing workers"""
        if self.is_running:
            return
            
        self.is_running = True
        logger.info(f"Starting {num_workers} AI processing workers")
        
        # Start worker tasks
        for i in range(num_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(task)
    
    async def stop(self):
        """Stop AI processing workers"""
        logger.info("Stopping AI processing workers")
        self.is_running = False
        
        # Cancel all workers
        for task in self.worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        self.worker_tasks.clear()
    
    async def queue_truth_for_processing(self, truth_data: TruthSchema):
        """Add a truth to the AI processing queue"""
        await self.processing_queue.put(truth_data)
        logger.info(f"🚀🚀🚀 - Queued truth {truth_data} for AI processing")
    
    async def _worker(self, worker_name: str):
        """Background worker for processing AI summaries"""
        logger.info(f"🚀🚀🚀 - AI worker {worker_name} started")
        logger.debug(f"🚀🚀🚀 - Worker {worker_name} is running with queue size: {self.processing_queue.qsize()}")
        logger.debug(f"🚀🚀🚀 - Worker {worker_name} is running with is_running: {self.is_running}")
        while self.is_running:
            try:
                logger.debug(f"🟦🟦🟦🟦🟦🟦🟦 Worker {worker_name} waiting for truth ID")
                truth_data = await asyncio.wait_for(
                    self.processing_queue.get(), 
                    timeout=30.0
                )
                
                logger.info(f"Worker {worker_name} processing truth {truth_data}")
                await self._process_truth_ai(truth_data)
                self.processing_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(5)
        
        logger.info(f"AI worker {worker_name} stopped")
    
    async def _process_truth_ai(self, truth: TruthSchema):
        logger.info(f"🚀🚀🚀- Processing AI for truth {truth.id}")
        truth_id = truth.id
        async with async_session() as session:
            truth_repo = TruthRepository(session)
            try:
                logger.info(f"Starting AI processing for truth ID {truth_id}...")
                context = await self.ai_service.generate_summary_and_context(truth_content=truth.content)
                logger.info(f"AI processing completed for truth ID {truth_id}.")
                
                truth.ai_context = context
                truth.ai_processed = True
                
                updated_truth = await truth_repo.update_truth(truth)
                
                pydantic_posts = [
                    TruthSchema(
                        id=updated_truth.id,
                        content=updated_truth.content,
                        timestamp=updated_truth.timestamp,
                        url=updated_truth.url,
                        media_urls=updated_truth.media_urls or [],
                        ai_context=updated_truth.ai_context,
                        ai_processed=updated_truth.ai_processed,
                        ai_processing=updated_truth.ai_processing
                    )
                ]

                if pydantic_posts:
                    broadcast_data = []
                    for post in pydantic_posts:
                        post_dict = post.dict()
                        # Convert datetime to string for JSON support
                        if post_dict.get('timestamp'):
                            post_dict['timestamp'] = str(post_dict['timestamp'])
                        broadcast_data.append(post_dict)
                
                await sse_manager.broadcast_truths(broadcast_data, broadcast_type="truth_ai_update")
                
                
            except Exception as e:
                logger.info(f"Failed AI processing for truth ID {truth_id}: {e}", exc_info=True)
                try:
                    # TODO: Update the truth status to 'ai_failed' in the database
                    logger.info(f"Marked truth ID {truth_id} as 'ai_failed' due to error.")
                except Exception as db_e:
                    logger.info(f"Failed to update truth ID {truth_id} status to 'ai_failed': {db_e}")
    
    
    async def _broadcast_ai_update(self, truths:List[TruthSchema]):
        """Broadcast AI update to SSE clients"""
        try:
            await sse_manager.broadcast_truths(truths, broadcast_type="truth_ai_update")
            logger.info(f"Broadcasted AI update for  {len(truths)} truths")
            
        except Exception as e:
            logger.info(f"Failed to broadcast AI update: {e}")


def get_ai_processing_service() -> AIProcessingService:
    return AIProcessingService()