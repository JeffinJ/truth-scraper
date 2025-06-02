import openai
import asyncio
from typing import Optional, Tuple
import os
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key
        )
    
    async def generate_summary_and_context(self, truth_content: str) -> Tuple[Optional[str], Optional[str]]:
        """Generate both summary and contextual insights for a truth post."""
        try:
            # Generate summary
            summary_prompt = f"""
            Summarize this Donald Trump Truth Social post in 1-2 concise sentences:
            
            "{truth_content}"
            
            Focus on the main point or announcement. Keep it objective and factual.
            """
            
            # Generate contextual insight
            context_prompt = f"""
            Provide brief contextual insight for this Donald Trump Truth Social post:
            
            "{truth_content}"
            
            Consider:
            - Political/policy implications
            - Historical context if relevant
            - Public reaction potential or significance
            - Related current events
            
            Keep response to 2-3 sentences maximum. Be objective and informative.
            """
            
            # Run both requests concurrently for efficiency
            # summary_task = self.client.chat.completions.create(
            #     model="gpt-3.5-turbo",
            #     messages=[{"role": "user", "content": summary_prompt}],
            #     max_tokens=100,
            #     temperature=0.3
            # )
            
            # context_task = self.client.chat.completions.create(
            #     model="gpt-3.5-turbo", 
            #     messages=[{"role": "user", "content": context_prompt}],
            #     max_tokens=150,
            #     temperature=0.3
            # )
            
            # summary_response, context_response = await asyncio.gather(
            #     summary_task, context_task, return_exceptions=True
            # )
            
            # sleep for 3 seconds to simulate API call
            await asyncio.sleep(3)
            
            summary = "Sample summary of the truth post."
            context = "Sample contextual insight for the truth post."
            
            # if not isinstance(summary_response, Exception):
            #     summary = summary_response.choices[0].message.content.strip()
            
            # if not isinstance(context_response, Exception):
            #     context = context_response.choices[0].message.content.strip()
            
            return summary, context
            
        except Exception as e:
            logger.exception("AI service error")
            logger.info(f"AI service error: {e}")
            return None, None


# def get_truth_service(db: DbSession) -> TruthService:
#     truth_repository = TruthRepository(db)  
#     return TruthService(truth_repository)


def get_openai_service() -> OpenAIService:
    """Dependency to provide OpenAIService instance."""
    return OpenAIService()