from pydantic import BaseModel
from typing import Optional, Any
from app.schemas.attack import AttackFilters
import uuid

class AIAnalysisRequest(BaseModel):
    attack_ids: Optional[list[uuid.UUID]] = None
    filters: Optional[AttackFilters] = None

class AIAnalysisResponse(BaseModel):
    summary: str
    severity: str
    attack_type: str
    recommendation: str
    confidence: float
    prompt_version: str

class ChainStep(BaseModel):
    step_number: int
    action: str
    mitre_id: Optional[str] = None
    description: str

class SimilarAttackSummary(BaseModel):
    attack_id: str
    similarity_score: float
    src_ip: str
    service: str
    attack_type: str

class InvestigationRequest(BaseModel):
    attack_id: Optional[uuid.UUID] = None
    filters: Optional[AttackFilters] = None
    query: Optional[str] = None

class InvestigationResponse(BaseModel):
    summary: str
    attack_chain: list[ChainStep]
    severity: str
    threat_actor_profile: str
    recommended_actions: list[str]
    confidence: float
    mitre_techniques: list[str]
    similar_attacks: list[SimilarAttackSummary]
