from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import uuid
from app.db.session import get_db
from app.schemas.ai import AIAnalysisRequest, AIAnalysisResponse, InvestigationRequest, InvestigationResponse, SimilarAttackSummary
from app.middleware.auth import get_current_user
from app.services.rag_service import rag_service
from app.ai.nim_client import nim_client

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/analyze", response_model=AIAnalysisResponse)
async def analyze_attacks(request: AIAnalysisRequest, db: AsyncSession = Depends(get_db)):
    # Placeholder for realtime analysis endpoint
    return AIAnalysisResponse(
        summary="Sample analysis summary",
        severity="high",
        attack_type="brute_force",
        recommendation="Block IP",
        confidence=0.95,
        prompt_version="realtime-v1"
    )

@router.post("/investigate", response_model=InvestigationResponse)
async def investigate_attacks(request: InvestigationRequest, db: AsyncSession = Depends(get_db)):
    try:
        report = await rag_service.investigate(db, incident_id=str(request.attack_id) if request.attack_id else None, query=request.query)
        if "error" in report:
            raise HTTPException(status_code=404, detail=report["error"])
        
        # Mapping dict to response model, in reality rag_service would return appropriate structured data
        if "similar_attacks" not in report:
            report["similar_attacks"] = []
        return InvestigationResponse(**report)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/similar/{attack_id}", response_model=list[SimilarAttackSummary])
async def get_similar_attacks(attack_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    # Placeholder
    return []
