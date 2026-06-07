from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.attack import Attack
from app.models.ai_analysis import AIAnalysis
from app.ai.nim_client import nim_client
from app.ai.embedding_service import embedding_service
from app.services.correlation_service import correlation_service
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

class RAGService:
    def __init__(self):
        self.settings = get_settings()

    async def get_attack_history(self, db: AsyncSession, src_ip: str, days: int = 30) -> list[Attack]:
        # simplified fetch
        query = select(Attack).where(Attack.src_ip == src_ip).order_by(desc(Attack.timestamp)).limit(100)
        result = await db.execute(query)
        return list(result.scalars().all())

    def build_rag_context(self, target_attacks: list[Attack], similar_attacks: list[Any], correlation_data: list[Any]) -> str:
        context_lines = []
        context_lines.append("=== Target Attacks ===")
        for a in target_attacks:
            context_lines.append(f"[{a.timestamp}] {a.src_ip} -> {a.service} (port {a.dst_port}) | Type: {a.attack_type} | Cmd: {a.command}")
            
        context_lines.append("\n=== Similar Historical Attacks ===")
        for sa in similar_attacks:
            context_lines.append(f"Score: {sa.get('score', 0):.2f} | IP: {sa.get('src_ip', 'unknown')} | {sa.get('service', 'unknown')} | Type: {sa.get('attack_type', 'unknown')}")
            
        context_lines.append("\n=== Correlation Insights ===")
        for c in correlation_data:
            context_lines.append(f"{c.type}: {c.description}")
            
        return "\n".join(context_lines)

    async def investigate(self, db: AsyncSession, incident_id: str = None, filters: dict = None, query: str = None) -> dict[str, Any]:
        # 1. Load targets
        target_attacks = []
        if incident_id:
            db_query = select(Attack).where(Attack.id == incident_id)
            result = await db.execute(db_query)
            attack = result.scalars().first()
            if attack:
                target_attacks.append(attack)
        elif query:
            db_query = select(Attack).order_by(desc(Attack.timestamp)).limit(10)
            result = await db.execute(db_query)
            target_attacks = list(result.scalars().all())
        
        if not target_attacks:
            return {"error": "Target not found"}

        # 2 & 3. Get context (Qdrant)
        if incident_id:
            target = target_attacks[0]
            target_dict = {
                "src_ip": target.src_ip,
                "service": target.service,
                "username": target.username,
                "password": target.password,
                "command": target.command,
                "severity": target.severity,
                "threat_score": target.threat_score,
                "country": getattr(target, "src_country", "unknown")
            }
            query_embedding = await embedding_service.embed_attack(target_dict)
            correlations = await correlation_service.detect_correlations(target)
        else:
            query_embedding = await nim_client.generate_embedding(query)
            correlations = []

        similar = await embedding_service.search_similar_attacks(query_embedding, top_k=self.settings.MAX_RAG_CONTEXT_ATTACKS)
        
        # 4. Build context
        context_str = self.build_rag_context(target_attacks, similar, correlations)
        if query and not incident_id:
            context_str += f"\n\nUSER QUERY: {query}\nPlease answer the user query based on the provided context. Format as a summary."
        
        attacks_data = [{"query": query}] if not incident_id else [
            {
                "id": str(a.id),
                "timestamp": str(a.timestamp),
                "src_ip": a.src_ip,
                "dst_port": a.dst_port,
                "service": a.service,
                "attack_type": a.attack_type,
                "command": a.command,
            } for a in target_attacks
        ]
        
        # 5. Call NIM
        report_data, model_used, prompt_version = await nim_client.investigate_incident(
            attacks_data, 
            context_str
        )
        
        # 6. Store AIAnalysis
        if incident_id:
            analysis = AIAnalysis(
                attack_id=target_attacks[0].id,
                summary=report_data.get("summary", ""),
                severity=report_data.get("severity", "medium"),
                attack_type="investigation",
                recommendation="\n".join(report_data.get("recommended_actions", [])),
                attack_chain=report_data.get("attack_chain", []),
                threat_actor_profile=report_data.get("threat_actor_profile", {}),
                confidence=report_data.get("confidence", 0.0),
                model_used=model_used,
                prompt_version=prompt_version,
                analysis_type="investigation"
            )
            db.add(analysis)
            await db.commit()
        
        result_dict = report_data
        result_dict["similar_attacks"] = [
            {
                "attack_id": str(sa.get("id")),
                "similarity_score": sa.get("score", 0),
                "src_ip": sa.get("src_ip", "unknown"),
                "service": sa.get("service", "unknown"),
                "attack_type": sa.get("attack_type", "unknown")
            } for sa in similar
        ]
        return result_dict

rag_service = RAGService()
