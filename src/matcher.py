"""
Core matching engine for AI Venture Relationship Intelligence Agent.

Scores founder-investor compatibility across 14 dimensions.
Supports many-to-many matching: each founder can match with multiple investors
and vice versa.
"""

from typing import List, Optional, Dict
from .models import Investor, Founder, MatchScore, Match


# ── AI Subsector Classification ──

AI_SUBSECTORS = {
    "infrastructure": ["infra", "compute", "gpu", "cloud", "devops", "mlops", "training", "inference"],
    "agents": ["agent", "copilot", "assistant", "automation", "workflow", "orchestration"],
    "healthcare": ["health", "medical", "clinical", "biotech", "pharma", "drug", "clinical"],
    "fintech": ["finance", "fintech", "wealth", "banking", "payment", "insurance", "compliance", "securities"],
    "defense": ["defense", "military", "autonomous", "fleet", "drone", "security", "offensive"],
    "developer_tools": ["developer", "devtools", "coding", "ide", "sdk", "api", "open-source"],
    "enterprise": ["enterprise", "b2b", "saas", "crm", "erp", "productivity"],
    "consumer": ["consumer", "social", "creator", "content", "media", "gaming", "entertainment"],
    "legal": ["legal", "law", "compliance", "regulatory"],
    "vertical": ["vertical", "industry", "sector", "niche"],
    "robotics": ["robot", "humanoid", "physical", "embodied"],
    "space": ["space", "orbital", "satellite", "orbit"],
    "energy": ["energy", "quantum", "chip", "semiconductor", "power"],
    "drug_discovery": ["drug discovery", "pharmaceutical", "protein", "alphafold", "molecular"],
    "crypto": ["crypto", "blockchain", "web3", "defi", "token"],
    "voice": ["voice", "speech", "audio", "conversational"],
    "data": ["data", "analytics", "visualization", "labeling"],
    "search": ["search", "knowledge", "retrieval", "rag"],
    "foundation": ["foundation model", "llm", "large language", "gpt", "transformer"],
}


def _classify_subsector(text: str) -> List[str]:
    """Classify text into AI subsectors."""
    text_lower = text.lower()
    matched = []
    for sector, keywords in AI_SUBSECTORS.items():
        if any(kw in text_lower for kw in keywords):
            matched.append(sector)
    return matched or ["general_ai"]


# ── Scoring Functions (0-100 each) ──

def _score_industry_alignment(founder: Founder, investor: Investor) -> float:
    """Score 0-100: How well do the founder's and investor's AI focus areas overlap?"""
    founder_sectors = set(_classify_subsector(
        f"{founder.ai_subsector} {founder.brand_positioning} {founder.ideal_investor_profile}"
    ))
    investor_sectors = set(_classify_subsector(
        " ".join(investor.ai_focus) + " " + investor.firm
    ))
    overlap = founder_sectors & investor_sectors
    if overlap:
        return min(100, 60 + len(overlap) * 12)
    return 40.0


def _score_stage_compatibility(founder: Founder, investor: Investor) -> float:
    """Score 0-100: Does the founder's stage match the investor's focus?"""
    stage = founder.stage.lower()
    investor_stages = [s.lower() for s in investor.stage_focus]

    # Determine stage label
    stage_label = ""
    if "pre-seed" in stage or "preseed" in stage:
        stage_label = "pre-seed"
    elif "seed" in stage:
        stage_label = "seed"
    elif "series a" in stage:
        stage_label = "series a"
    elif "series b" in stage:
        stage_label = "series b"
    elif "series c" in stage:
        stage_label = "series c"
    elif "growth" in stage or "series d" in stage:
        stage_label = "growth"

    if stage_label:
        # Direct match
        for s in investor_stages:
            if stage_label in s or s in stage_label:
                return 90.0
        # Adjacent stage match
        if stage_label in ["pre-seed", "seed"] and any("seed" in s for s in investor_stages):
            return 80.0
        if stage_label in ["series a", "series b"] and any("series" in s for s in investor_stages):
            return 70.0
        if stage_label == "growth" and any("growth" in s for s in investor_stages):
            return 85.0
    return 50.0


def _score_geography(founder: Founder, investor: Investor) -> float:
    """Score 0-100: Geographic alignment."""
    f_loc = founder.location.lower()
    i_loc = investor.geography.lower()

    if "us" in f_loc and "us" in i_loc:
        return 90.0
    if "europe" in f_loc and ("global" in i_loc or "europe" in i_loc):
        return 80.0
    if "europe" in f_loc and "us" in i_loc:
        return 55.0
    if "global" in i_loc:
        return 75.0
    return 60.0


def _score_founder_pedigree(founder: Founder, investor: Investor) -> float:
    """Score 0-100: Founder background and track record."""
    pedigree = (founder.founder_pedigree + " " + founder.background).lower()
    score = 50.0

    # Big tech experience
    for company in ["google", "meta", "openai", "deepmind", "amazon", "apple", "microsoft", "twitter"]:
        if company in pedigree:
            score += 10
            break

    # Academic credentials
    if any(kw in pedigree for kw in ["professor", "phd", "stanford", "mit", "cmu"]):
        score += 10

    # Serial entrepreneur
    if any(kw in pedigree for kw in ["serial", "founded", "exited", "acquisition"]):
        score += 10

    # Top-tier backing
    if any(kw in pedigree for kw in ["intel ceo", "databricks", "sequoia", "a16z", "noble"]):
        score += 10

    return min(100, score)


def _score_traction(founder: Founder, investor: Investor) -> float:
    """Score 0-100: Startup traction and momentum."""
    import re
    traction = (founder.traction + " " + founder.stage).lower()
    score = 50.0

    # Funding amounts
    amounts = re.findall(r'\$([\d.]+)\s*([BMK])', traction)
    for amount_str, unit in amounts:
        amount = float(amount_str)
        if unit == "B":
            score += 30
        elif unit == "M" and amount >= 100:
            score += 25
        elif unit == "M" and amount >= 20:
            score += 20
        elif unit == "M" and amount >= 5:
            score += 15
        elif unit == "M":
            score += 10
        elif unit == "K" and amount >= 500:
            score += 5

    if "oversubscribed" in traction:
        score += 10

    return min(100, score)


def _score_growth_velocity(founder: Founder) -> float:
    """Score 0-100: Speed of development."""
    velocity = founder.growth_velocity.lower()
    if "very high" in velocity:
        return 95.0
    if "high" in velocity:
        return 80.0
    if "moderate" in velocity:
        return 60.0
    return 50.0


def _score_brand_positioning(founder: Founder) -> float:
    """Score 0-100: Market positioning strength."""
    positioning = founder.brand_positioning.lower()
    score = 50.0
    if any(kw in positioning for kw in ["category", "infrastructure", "platform", "protocol"]):
        score += 20
    if any(kw in positioning for kw in ["first", "native", "default", "autonomous"]):
        score += 15
    return min(100, score)


def _score_communication_style(founder: Founder, investor: Investor) -> float:
    """Score 0-100: Communication style compatibility."""
    f_style = set(founder.communication_style.lower().split(", "))
    i_style = set(investor.communication_style.lower().split(", "))

    overlap = f_style & i_style
    if len(overlap) >= 2:
        return 90.0
    if overlap:
        return 75.0

    # Semantic matching
    pairs = [
        ("technical", "technical"),
        ("enterprise", "enterprise"),
        ("developer", "developer"),
        ("product", "product"),
        ("security", "security"),
        ("research", "research"),
        ("fintech", "fintech"),
        ("healthcare", "healthcare"),
    ]
    for f_kw, i_kw in pairs:
        if any(f_kw in s for s in f_style) and any(i_kw in s for s in i_style):
            return 70.0

    return 50.0


def _score_social_proof(founder: Founder) -> float:
    """Score 0-100: Media coverage, notable investors, accelerators."""
    proof = (founder.social_proof + " " + founder.traction).lower()
    score = 50.0

    # Major media
    for outlet in ["wsj", "cnbc", "techcrunch", "bloomberg", "forbes", "nyt", "financial times"]:
        if outlet in proof:
            score += 10
            break

    # Accelerators
    if any(kw in proof for kw in ["yc", "y combinator", "accelerator"]):
        score += 15

    # Notable backers
    if any(kw in proof for kw in ["elevenlabs", "openai", "anthropic", "sequoia", "a16z", "khosla"]):
        score += 10

    # Valuation signals
    if any(kw in proof for kw in ["billion", "$1b", "$2b", "valuation"]):
        score += 10

    return min(100, score)


def _score_investor_behavior(investor: Investor) -> float:
    """Score 0-100: How responsive is this investor?"""
    behavior = investor.response_behavior.lower()
    if "high" in behavior:
        return 85.0
    if "moderate" in behavior:
        return 65.0
    return 50.0


def _score_portfolio_similarity(founder: Founder, investor: Investor) -> float:
    """Score 0-100: How similar is this to the investor's existing portfolio?"""
    founder_text = (founder.ai_subsector + " " + founder.brand_positioning).lower()
    portfolio_text = " ".join(investor.portfolio).lower()
    focus_text = " ".join(investor.ai_focus).lower()

    overlap_count = 0
    for keyword in founder_text.split():
        if len(keyword) > 3 and (keyword in portfolio_text or keyword in focus_text):
            overlap_count += 1

    return min(100, 40 + overlap_count * 10)


def _score_reputation(investor: Investor) -> float:
    """Score 0-100: Investor reputation."""
    return min(100, investor.reputation_score * 10)


def _score_relationship_proximity(founder: Founder, investor: Investor) -> float:
    """Score 0-100: Warm introduction pathway availability."""
    paths = len(investor.warm_intro_paths)
    if paths >= 4:
        return 85.0
    if paths >= 3:
        return 70.0
    if paths >= 2:
        return 55.0
    return 40.0


def _score_conversion(founder: Founder, investor: Investor, scores: MatchScore) -> float:
    """Score 0-100: Overall conversion probability."""
    base = scores.total
    speed = investor.decision_speed.lower()
    if "very fast" in speed:
        return min(100, base + 15)
    if "fast" in speed or "days" in speed:
        return min(100, base + 10)
    return base


# ── Main API ──

def calculate_match_score(founder: Founder, investor: Investor) -> MatchScore:
    """Calculate detailed match score between a founder and investor."""
    scores = MatchScore(
        industry_alignment=_score_industry_alignment(founder, investor),
        stage_compatibility=_score_stage_compatibility(founder, investor),
        geography_preference=_score_geography(founder, investor),
        founder_track_record=_score_founder_pedigree(founder, investor),
        startup_traction=_score_traction(founder, investor),
        growth_velocity=_score_growth_velocity(founder),
        brand_positioning=_score_brand_positioning(founder),
        communication_style=_score_communication_style(founder, investor),
        social_proof=_score_social_proof(founder),
        investor_response_behavior=_score_investor_behavior(investor),
        portfolio_similarity=_score_portfolio_similarity(founder, investor),
        reputation_score=_score_reputation(investor),
        relationship_proximity=_score_relationship_proximity(founder, investor),
        conversion_likelihood=0.0,
    )
    scores.conversion_likelihood = _score_conversion(founder, investor, scores)
    return scores


def _build_match(founder: Founder, investor: Investor, scores: MatchScore, total: float) -> Match:
    """Build a Match object from scores."""
    return Match(
        founder=founder,
        investor=investor,
        score=scores,
        total_score=total,
        match_rationale="",
        concerns=[],
        meeting_acceptance_likelihood=min(100, total + 5),
        investment_probability=max(0, total - 15),
        ideal_communication_style=investor.communication_style,
        best_timing="Within 1-2 weeks",
        warm_intro_pathways=investor.warm_intro_paths,
        intro_email_draft="",
    )


def find_top_matches(
    founders: List[Founder],
    investors: List[Investor],
    top_n: int = 20,
    min_score: float = 55.0,
) -> List[Match]:
    """Find top N matches across ALL founders and investors (many-to-many).

    Each founder can appear multiple times (matched with different investors)
    and each investor can appear multiple times (matched with different founders).
    """
    all_matches = []

    for founder in founders:
        for investor in investors:
            scores = calculate_match_score(founder, investor)
            total = scores.total
            if total >= min_score:
                all_matches.append(_build_match(founder, investor, scores, total))

    all_matches.sort(key=lambda m: m.total_score, reverse=True)
    return all_matches[:top_n]


def find_top_matches_for_founder(
    founder: Founder,
    investors: List[Investor],
    top_n: int = 20,
) -> List[Match]:
    """Find top N investor matches for a specific founder."""
    matches = []
    for investor in investors:
        scores = calculate_match_score(founder, investor)
        total = scores.total
        if total >= 50:
            matches.append(_build_match(founder, investor, scores, total))

    matches.sort(key=lambda m: m.total_score, reverse=True)
    return matches[:top_n]


def find_top_matches_for_investor(
    investor: Investor,
    founders: List[Founder],
    top_n: int = 20,
) -> List[Match]:
    """Find top N founder matches for a specific investor."""
    matches = []
    for founder in founders:
        scores = calculate_match_score(founder, investor)
        total = scores.total
        if total >= 50:
            matches.append(_build_match(founder, investor, scores, total))

    matches.sort(key=lambda m: m.total_score, reverse=True)
    return matches[:top_n]


def get_all_matches_matrix(
    founders: List[Founder],
    investors: List[Investor],
    min_score: float = 50.0,
) -> Dict[str, List[Match]]:
    """Get a complete match matrix: for each founder, their ranked investor matches.

    Returns a dict keyed by founder.id with sorted match lists.
    """
    matrix: Dict[str, List[Match]] = {}

    for founder in founders:
        matches = []
        for investor in investors:
            scores = calculate_match_score(founder, investor)
            total = scores.total
            if total >= min_score:
                matches.append(_build_match(founder, investor, scores, total))
        matches.sort(key=lambda m: m.total_score, reverse=True)
        matrix[founder.id] = matches

    return matrix
