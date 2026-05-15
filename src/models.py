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
    mission: str = ""  # What the organization is trying to achieve
    projected_sales_y1: str = ""  # Projected first-year sales
    year_incorporated: str = ""  # Year of incorporation
    growth_last_12mo: str = ""  # Growth in last 12 months
    technical_depth: str = ""  # Model architecture, proprietary data, self-hosted vs API
    moat: str = ""  # Data moats, network effects, IP, domain expertise
    team_composition: str = ""  # AI PhDs + domain experts + GTM balance
    regulatory_readiness: str = ""  # Compliance, ethics, data governance
    needs_capital: bool = True  # Whether founder is actively seeking capital
    capital_stage: str = "actively_raising"  # actively_raising | monitor | well_capitalized
    capital_notes: str = ""  # Why this capital stage assessment
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None


@dataclass
class MatchScore:
    # ── Core Fit (40% of total) ──
    industry_alignment: float = 0.0       # Sector & subsector overlap
    stage_compatibility: float = 0.0      # Funding stage match
    geography_preference: float = 0.0     # Geographic alignment
    portfolio_similarity: float = 0.0     # Overlap with investor portfolio

    # ── Founder Strength (25% of total) ──
    founder_pedigree: float = 0.0         # Track record, big tech, serial exits
    team_composition: float = 0.0         # AI PhDs + domain + GTM balance
    technical_depth: float = 0.0          # Real AI vs wrapper, proprietary models

    # ── Business Quality (20% of total) ──
    revenue_traction: float = 0.0         # Revenue, customers, growth metrics
    growth_momentum: float = 0.0          # 12-month growth, velocity
    moat_defensibility: float = 0.0       # Data moats, IP, network effects

    # ── Market & Signal (15% of total) ──
    market_positioning: float = 0.0       # Brand, category leadership
    social_proof: float = 0.0             # Media, accelerators, notable backers
    regulatory_readiness: float = 0.0     # Compliance, ethics, data governance

    # ── Relationship Factors ──
    communication_fit: float = 0.0        # Style compatibility
    investor_responsiveness: float = 0.0  # Response behavior
    investor_reputation: float = 0.0      # Fund reputation
    warm_intro_access: float = 0.0        # Introduction pathway availability
    conversion_likelihood: float = 0.0    # Overall probability estimate

    @property
    def total(self) -> float:
        weights = {
            # Core Fit (40%)
            "industry_alignment": 0.14,
            "stage_compatibility": 0.12,
            "geography_preference": 0.06,
            "portfolio_similarity": 0.08,
            # Founder Strength (25%)
            "founder_pedigree": 0.10,
            "team_composition": 0.07,
            "technical_depth": 0.08,
            # Business Quality (20%)
            "revenue_traction": 0.08,
            "growth_momentum": 0.06,
            "moat_defensibility": 0.06,
            # Market & Signal (15%)
            "market_positioning": 0.04,
            "social_proof": 0.04,
            "regulatory_readiness": 0.03,
            # Relationship
            "communication_fit": 0.02,
            "investor_responsiveness": 0.015,
            "investor_reputation": 0.015,
            "warm_intro_access": 0.015,
            "conversion_likelihood": 0.015,
        }
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
