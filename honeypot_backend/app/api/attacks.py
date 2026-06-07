from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.db.session import get_db
from app.schemas.attack import AttackListResponse, AttackFilters, PaginationParams
from app.schemas.stats import DashboardStats, TopAttacker, CountryStats, TimelineBucket
from app.services.attack_service import attack_service
from app.middleware.auth import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/attacks/live", response_model=AttackListResponse)
async def get_live_attacks(
    service: Optional[str] = None,
    severity: Optional[str] = None,
    src_ip: Optional[str] = None,
    country: Optional[str] = None,
    attack_type: Optional[str] = None,
    reputation: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db)
):
    filters = {}
    if service: filters["service"] = service
    if severity: filters["severity"] = severity
    if src_ip: filters["src_ip"] = src_ip
    if country: filters["src_country_code"] = country
    if attack_type: filters["attack_type"] = attack_type
    if reputation: filters["reputation"] = reputation
    
    skip = (page - 1) * page_size
    result = await attack_service.get_attacks(db, skip=skip, limit=page_size, filters=filters)
    
    total = result["total"]
    pages = (total + page_size - 1) // page_size
    
    return {
        "items": result["items"],
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages
    }

@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    return await attack_service.get_attack_stats(db)

@router.get("/top-attackers", response_model=list[TopAttacker])
async def get_top_attackers(limit: int = Query(10, ge=1, le=50), db: AsyncSession = Depends(get_db)):
    # Placeholder for a complex query
    return []

@router.get("/countries", response_model=list[CountryStats])
async def get_countries(db: AsyncSession = Depends(get_db)):
    # Placeholder for a complex query
    return []

@router.get("/timeline", response_model=list[TimelineBucket])
async def get_timeline(interval: str = Query("1h"), db: AsyncSession = Depends(get_db)):
    # Placeholder for a complex query
    return []
