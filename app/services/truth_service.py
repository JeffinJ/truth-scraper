from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated, List, Dict, Any
import logging

from app.database.db_config import DbSession
from app.repositories.truth_repository import TruthRepository, get_truths_repository
from app.schemas.truth import TruthSchema
from app.services.sse_service import sse_manager
from fastapi import Depends

logger = logging.getLogger(__name__)

truth_repository_dependency = Annotated[TruthRepository, Depends(get_truths_repository)]

class TruthService:
    
    def __init__(
            self, 
            truth_repository: truth_repository_dependency
        ):
        self.truth_repository = truth_repository
        pass
    
    
    async def get_last_truth(self) -> TruthSchema:
        """
        Get the most recent Truth Social post from the database

        Args:
            db: Database session

        Returns:
            TruthSchema: The most recent post as a Pydantic model or None if not found
        """
        post = await self.truth_repository.get_last_truth()
        if not post:
            return None

        return TruthSchema(
            id=post.id,
            content=post.content,
            timestamp=post.timestamp,
            url=post.url,
            media_urls=post.media_urls or []
        )
        

    async def save_truths(self,truths_data: List[Dict[Any, Any]]) -> List[TruthSchema]:
        """
        Save Truth Social posts to the database

        Args:
            db: Database session
            truths_data: List of dictionaries containing Truth Social post data

        Returns:
            List[TruthSchema]: The saved posts as Pydantic models
        """
        logger.info(f"Saving {len(truths_data)} Truth Social posts to database")
        
        # Save posts to database
        saved_posts = await self.truth_repository.create_or_update_truth(truths_data)

        pydantic_posts = [
            TruthSchema(
                id=post.id,
                content=post.content,
                timestamp=post.timestamp,
                url=post.url,
                media_urls=post.media_urls or []
            )
            for post in saved_posts
        ]

            # Broadcast new truths via SSE
        if pydantic_posts:
            broadcast_data = []
            for post in pydantic_posts:
                post_dict = post.dict()
                # Convert datetime to string for JSON serialization
                if post_dict.get('timestamp'):
                    post_dict['timestamp'] = str(post_dict['timestamp'])
                broadcast_data.append(post_dict)

            logger.info(f"Broadcasting {broadcast_data} truths to SSE clients")
            await sse_manager.broadcast_truths(broadcast_data)

        return pydantic_posts

    async def get_truths(self, db: AsyncSession) -> List[TruthSchema]:
        return await self.truth_repository.get_all_truths()

    async def get_truth(self, db: AsyncSession, truth_id: int) -> TruthSchema:
        post = await self.truth_repository.get_truth_by_id(truth_id)
        if not post:
            return None

        return TruthSchema(
            id=post.id,
            content=post.content,
            timestamp=post.timestamp,
            url=post.url,
            media_urls=post.media_urls or []
        )

def get_truth_service(db: DbSession) -> TruthService:
    truth_repository = TruthRepository(db)  
    return TruthService(truth_repository)