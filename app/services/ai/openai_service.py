import openai
from typing import Optional, Tuple
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
            # contextual insight
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
            
            context_response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo", 
                messages=[{"role": "user", "content": context_prompt}],
                max_tokens=150,
                temperature=0.3
            )
            
            context = "No context provided."
            
            if context_response:
                context = context_response.choices[0].message.content.strip()
            return context
            
        except Exception as e:
            logger.exception("AI service error")
            logger.info(f"AI service error: {e}")
            return None, None

def get_openai_service() -> OpenAIService:
    """Dependency to provide OpenAIService instance."""
    return OpenAIService()