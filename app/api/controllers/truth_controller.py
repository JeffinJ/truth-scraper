from typing import Annotated
from fastapi import APIRouter, Depends
from app.database.db_config import DbSession
from app.services.truth_service import TruthService, get_truth_service

router = APIRouter(
    prefix="/truths",
)

truth_service_dependency = Annotated[TruthService, Depends(get_truth_service)]

@router.get("/latest")
async def get_truths(
    db:DbSession,
    truth_service: truth_service_dependency,
):
    truths = await truth_service.get_truths(db)
    return truths