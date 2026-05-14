"""Data models for investors and founders."""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Investor:
    id: str
    name: str
    firm: str
    type: str  # "VC", "Angel", "Accelerator", "CVC"
    check_size: str
    stage_focus: List[str]
    ai_focus: List[str]
    geography: str
    portfolio: List[str]
    decision_speed: str
    communication_style: str
    response_behavior: str
    thought_leadership: str
    warm_intro_paths: List[str]
    reputation_score: int  # 1-10
    last_activity: str
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    website: Optional[str] = None

    @property
    def focus_areas_display(self) -> str:
        return ", ".join(self.ai_focus[:3])


@dataclass
class Founder:
    id: str
    name: str
    company: str
    role: str
    background: str
    stage: str
    ai_subsector: str
    location: str
    traction: str
    founder_pedigree: str
    growth_velocity: str
    brand_positioning: str
    social_proof: str
    communication_style: str
    ideal_investor_profile: str
    warm_intro_needs: str
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None


@dataclass
class MatchScore:
    industry_alignment: float = 0.0
    stage_compatibility: float = 0.0
    geography_preference: float = 0.0
    founder_track_record: float = 0.0
    startup_traction: float = 0.0
    growth_velocity: float = 0.0
    brand_positioning: float = 0.0
    communication_style: float = 0.0
    social_proof: float = 0.0
    investor_response_behavior: float = 0.0
    portfolio_similarity: float = 0.0
    reputation_score: float = 0.0
    relationship_proximity: float = 0.0
    conversion_likelihood: float = 0.0

    @property
    def total(self) -> float:
        weights = {
            "industry_alignment": 0.15,
            "stage_compatibility": 0.12,
            "geography_preference": 0.05,
            "founder_track_record": 0.12,
            "startup_traction": 0.10,
            "growth_velocity": 0.08,
            "brand_positioning": 0.05,
            "communication_style": 0.05,
            "social_proof": 0.05,
            "investor_response_behavior": 0.05,
            "portfolio_similarity": 0.05,
            "reputation_score": 0.05,
            "relationship_proximity": 0.05,
            "conversion_likelihood": 0.03,
        }
        # Scores are already 0-100, weights sum to 1.0
        # Result is weighted average, also 0-100
        return round(
            sum(getattr(self, k) * v for k, v in weights.items()), 1
        )


@dataclass
class Match:
    founder: Founder
    investor: Investor
    score: MatchScore
    total_score: float
    match_rationale: str
    concerns: List[str]
    meeting_acceptance_likelihood: float
    investment_probability: float
    ideal_communication_style: str
    best_timing: str
    warm_intro_pathways: List[str]
    intro_email_draft: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
