from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from datetime import datetime
import logging
from app.database.db_config import DbSession
from app.models.truths import TruthModel
from app.schemas.truth import TruthSchema

logger = logging.getLogger(__name__)


class TruthRepository:
    
    def __init__(self, session: AsyncSession):
        self.db = session
        pass
    
    
    async def create_or_update_truth(self, truth_data_list: List[Dict[Any, Any]]) -> List[TruthModel]:
        saved_posts = []

        for truth_data in truth_data_list:
            try:
                post_id = int(truth_data["id"])
                timestamp = datetime.fromisoformat(truth_data["timestamp"].replace("Z", "+00:00"))
                content = truth_data["content"]
                url = truth_data["url"]
                media_urls = truth_data.get("media_urls", [])

                stmt = select(TruthModel).where(TruthModel.id == post_id)
                result = await self.db.execute(stmt)
                existing_post = result.scalars().first()

                if existing_post:
                    logger.info(f"Updating existing post with ID: {post_id}")
                    existing_post.content = content
                    existing_post.timestamp = timestamp
                    existing_post.url = url
                    existing_post.media_urls = media_urls
                    post = existing_post
                else:
                    logger.info(f"Creating new post with ID: {post_id}")
                    post = TruthModel(
                        id=post_id,
                        content=content,
                        timestamp=timestamp,
                        url=url,
                        media_urls=media_urls
                    )
                    self.db.add(post)

                saved_posts.append(post)

            except Exception as e:
                logger.error(f"Error processing post data: {truth_data}. Error: {e}")

        await self.db.commit()

        for post in saved_posts:
            await self.db.refresh(post)

        return saved_posts


    async def get_last_truth(self) -> TruthModel:
        stmt = select(TruthModel).order_by(TruthModel.timestamp.desc()).limit(1)
        result = await self.db.execute(stmt)
        return result.scalars().first()


    async def get_all_truths(
            self, 
            limit: int = 20, 
            offset: int = 0
        ) -> Dict[str, Any]:

        stmt = select(TruthModel).order_by(TruthModel.timestamp.desc()).limit(limit+1).offset(offset)  
        result = await self.db.execute(stmt)
        posts = result.scalars().all()
        
        has_more = len(posts) > limit
        if has_more:
            posts = posts[:limit]
        
        return {
            "data": posts,
            "has_more": has_more,
            "next_offset": offset + limit if has_more else None
        }
        
    async def update_truth(self, truth: TruthSchema) -> TruthModel | None:
        try:
            stmt = select(TruthModel).where(TruthModel.id == truth.id)
            result = await self.db.execute(stmt)
            existing_truth = result.scalars().first()

            if not existing_truth:
                logger.warning(f"Truth with ID {truth.id} not found for update.")
                return None

            logger.info(f"Updating truth with ID: {truth.id}")

            existing_truth.content = truth.content
            existing_truth.timestamp = truth.timestamp
            existing_truth.url = truth.url
            existing_truth.media_urls = truth.media_urls
            existing_truth.ai_summary = truth.ai_summary
            existing_truth.ai_context = truth.ai_context
            existing_truth.ai_processed = truth.ai_processed
            existing_truth.ai_processing = truth.ai_processing

            await self.db.commit()
            await self.db.refresh(existing_truth)

            return existing_truth

        except Exception as e:
            logger.error(f"Failed to update truth with ID {truth.id}: {e}")
            await self.db.rollback()
            return None
    

    async def get_truth_by_id(self, truth_id: int) -> TruthModel:
        logger.info(f"Fetching truth with ID: {truth_id}")
        stmt = select(TruthModel).where(TruthModel.id == truth_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    
    
    
def get_truths_repository(db: DbSession) -> TruthRepository:
    return TruthRepository(db)