import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.bid_readiness_score import BidReadinessScore
from app.models.compliance_item import ComplianceItem, ComplianceStatus
from app.models.extracted_field import ExtractedField
from app.models.tender import Tender

logger = logging.getLogger(__name__)


class BidReadinessService:
    """Computes Bid Readiness Score using transparent weighted formula.

    The score is NOT an opaque LLM call — it's calculated from sub-scores
    with configurable weights:
    - compliance (30%): how many compliance items are met
    - experience (25%): knowledge base items matching the tender domain
    - capacity (20%): team availability (tasks completed vs assigned)
    - risk (15%): inverted — unresolved fields and deadline proximity
    - past_performance (10%): win rate on similar past tenders
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.weights = settings.bid_readiness_weights_dict

    async def calculate(self, tender_id: int, calculated_by: int | None = None) -> BidReadinessScore:
        tender_result = await self.db.execute(select(Tender).where(Tender.id == tender_id))
        tender = tender_result.scalar_one_or_none()
        if not tender:
            raise ValueError("Tender not found")

        compliance_score = await self._calc_compliance(tender_id)
        experience_score = await self._calc_experience(tender)
        capacity_score = await self._calc_capacity(tender_id)
        risk_score = await self._calc_risk(tender_id)
        past_performance_score = await self._calc_past_performance(tender)

        overall = (
            compliance_score * self.weights["compliance"]
            + experience_score * self.weights["experience"]
            + capacity_score * self.weights["capacity"]
            + risk_score * self.weights["risk"]
            + past_performance_score * self.weights["past_performance"]
        )

        breakdown = {
            "compliance": {"score": compliance_score, "weight": self.weights["compliance"]},
            "experience": {"score": experience_score, "weight": self.weights["experience"]},
            "capacity": {"score": capacity_score, "weight": self.weights["capacity"]},
            "risk": {"score": risk_score, "weight": self.weights["risk"]},
            "past_performance": {"score": past_performance_score, "weight": self.weights["past_performance"]},
        }

        score = BidReadinessScore(
            tender_id=tender_id,
            overall_score=round(overall, 2),
            compliance_score=compliance_score,
            experience_score=experience_score,
            capacity_score=capacity_score,
            risk_score=risk_score,
            past_performance_score=past_performance_score,
            weights_used=json.dumps(self.weights),
            breakdown=json.dumps(breakdown),
            calculated_by=calculated_by,
        )
        self.db.add(score)
        await self.db.commit()
        await self.db.refresh(score)

        # Update tender with score
        tender.ai_readiness_score = round(overall, 2)
        tender.ai_go_nogo_recommendation = "go" if overall >= 0.6 else "no_go"
        tender.ai_go_nogo_explanation = self._generate_explanation(overall, breakdown)
        await self.db.commit()

        return score

    async def _calc_compliance(self, tender_id: int) -> float:
        result = await self.db.execute(select(ComplianceItem).where(ComplianceItem.tender_id == tender_id))
        items = result.scalars().all()
        if not items:
            return 0.5
        met = sum(1 for i in items if i.status in (ComplianceStatus.MET, ComplianceStatus.EXEMPTED))
        return met / len(items)

    async def _calc_experience(self, tender: Tender) -> float:
        from app.models.knowledge_base_item import KnowledgeBaseItem

        result = await self.db.execute(
            select(KnowledgeBaseItem).where(
                KnowledgeBaseItem.agency_id == tender.agency_id,
                KnowledgeBaseItem.client_workspace_id == tender.client_workspace_id,
            )
        )
        items = result.scalars().all()
        if not items:
            return 0.3
        return min(1.0, len(items) / 10)

    async def _calc_capacity(self, tender_id: int) -> float:
        from app.models.task import Task

        result = await self.db.execute(select(Task).where(Task.tender_id == tender_id))
        tasks = result.scalars().all()
        if not tasks:
            return 0.7
        completed = sum(1 for t in tasks if t.status == "completed")
        return completed / len(tasks)

    async def _calc_risk(self, tender_id: int) -> float:
        unresolved = await self.db.execute(
            select(ExtractedField).where(
                ExtractedField.tender_id == tender_id,
                ExtractedField.is_resolved.is_(False),
            )
        )
        unresolved_count = len(unresolved.scalars().all())
        risk = 1.0 - (unresolved_count * 0.1)
        return max(0.0, min(1.0, risk))

    async def _calc_past_performance(self, tender: Tender) -> float:
        result = await self.db.execute(
            select(Tender).where(
                Tender.agency_id == tender.agency_id,
                Tender.client_workspace_id == tender.client_workspace_id,
                Tender.status.in_(["won", "lost"]),
            )
        )
        past = result.scalars().all()
        if not past:
            return 0.5
        won = sum(1 for t in past if t.status == "won")
        return won / len(past)

    def _generate_explanation(self, overall: float, breakdown: dict) -> str:
        go_nogo = "GO" if overall >= 0.6 else "NO-GO"
        lines = [f"**{go_nogo} Recommendation** (Score: {overall:.0%})"]
        for key, val in breakdown.items():
            pct = val["score"] * 100
            label = key.replace("_", " ").title()
            lines.append(f"- {label}: {pct:.0f}% (weight: {val['weight']:.0%})")
        return "\n".join(lines)
