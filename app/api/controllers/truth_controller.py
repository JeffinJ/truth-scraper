from typing import Annotated
from fastapi import APIRouter, Depends
from app.database.db_config import DbSession
from app.schemas.truth import TruthSchema
from app.services.ai.openai_service import OpenAIService, get_openai_service
from app.services.truth_service import TruthService, get_truth_service

router = APIRouter(
    prefix="/truths",
)

truth_service_dependency = Annotated[TruthService, Depends(get_truth_service)]
ai_service_dependency = Annotated[OpenAIService, Depends(get_openai_service)]

@router.get("/latest")
async def get_truths(
    db:DbSession,
    truth_service: truth_service_dependency,
):
    truths = await truth_service.get_truths(db)
    return truths


@router.post("/summary")
async def summarize_truths(
    item:TruthSchema,  
    ai_service: ai_service_dependency,
):
    try:
        # log request body
        print(f"Received request body: {item}")
        await ai_service.generate_summary_and_context(item.content)
        return {"message": "Truths summarized successfully"}
    except Exception as e:
        return {"error": str(e)}