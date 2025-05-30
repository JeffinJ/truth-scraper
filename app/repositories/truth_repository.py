from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from datetime import datetime
import logging
from app.database.db_config import DbSession
from app.models.truths import TruthModel

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
    

    async def get_truth_by_id(self, truth_id: int) -> TruthModel:
        stmt = select(TruthModel).where(TruthModel.id == truth_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
    
    
    
    
def get_truths_repository(db: DbSession) -> TruthRepository:
    return TruthRepository(db)