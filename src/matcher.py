"""Core matching engine - scores founder-investor compatibility."""

from typing import List
from .models import Investor, Founder, MatchScore, Match


# AI subsector keywords for matching
AI_SUBSECTORS = {
    "infrastructure": ["infra", "compute", "gpu", "cloud", "devops", "mlops", "training", "inference"],
    "agents": ["agent", "copilot", "assistant", "automation", "workflow", "orchestration"],
    "healthcare": ["health", "medical", "clinical", "biotech", "pharma", "drug"],
    "fintech": ["finance", "fintech", "wealth", "banking", "payment", "insurance"],
    "defense": ["defense", "military", "autonomous", "fleet", "drone", "security"],
    "developer_tools": ["developer", "devtools", "coding", "ide", "sdk", "api", "open-source"],
    "enterprise": ["enterprise", "b2b", "saas", "crm", "erp", "productivity"],
    "consumer": ["consumer", "social", "creator", "content", "media", "gaming"],
    "legal": ["legal", "law", "compliance", "regulatory"],
    "vertical": ["vertical", "industry", "sector", "niche"],
}


def _classify_subsector(text: str) -> List[str]:
    """Classify text into AI subsectors."""
    text_lower = text.lower()
    matched = []
    for sector, keywords in AI_SUBSECTORS.items():
        if any(kw in text_lower for kw in keywords):
            matched.append(sector)
    return matched or ["general_ai"]


def _score_industry_alignment(founder: Founder, investor: Investor) -> float:
    """Score 0-100: How well do founder's AI subsectors match investor focus?"""
    founder_sectors = set(_classify_subsector(
        f"{founder.ai_subsector} {founder.brand_positioning} {founder.ideal_investor_profile}"
    ))
    investor_sectors = set(_classify_subsector(
        " ".join(investor.ai_focus) + " " + investor.firm
    ))

    overlap = founder_sectors & investor_sectors
    if overlap:
        return min(100, 60 + len(overlap) * 15)
    # Partial match via broader categories
    return 40.0


def _score_stage_compatibility(founder: Founder, investor: Investor) -> float:
    """Score 0-100: Does investor's check/stage match founder's current stage?"""
    stage = founder.stage.lower()
    investor_stages = [s.lower() for s in investor.stage_focus]

    # Extract numeric amount if present
    import re
    amounts = re.findall(r'\$[\d.]+[BMK]', stage)
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

    if stage_label:
        for s in investor_stages:
            if stage_label in s or s in stage_label:
                return 90.0
        # Close match
        if stage_label in ["pre-seed", "seed"] and any("seed" in s for s in investor_stages):
            return 80.0
        if stage_label in ["series a", "series b"] and any("series" in s for s in investor_stages):
            return 70.0
    return 50.0


def _score_geography(founder: Founder, investor: Investor) -> float:
    """Score 0-100: Geographic alignment."""
    f_loc = founder.location.lower()
    i_loc = investor.geography.lower()

    if "us" in f_loc and "us" in i_loc:
        return 90.0
    if "europe" in f_loc and "global" in i_loc:
        return 75.0
    if "europe" in f_loc and "us" in i_loc:
        return 55.0
    return 60.0


def _score_founder_pedigree(founder: Founder, investor: Investor) -> float:
    """Score 0-100: Founder background strength."""
    pedigree = (founder.founder_pedigree + " " + founder.background).lower()
    score = 50.0

    # Big tech experience
    big_tech = ["google", "meta", "openai", "deepmind", "amazon", "apple", "microsoft", "twitter"]
    for company in big_tech:
        if company in pedigree:
            score += 10
            break

    # Academic credentials
    if any(kw in pedigree for kw in ["professor", "phd", "stanford", "mit", "cmu"]):
        score += 10

    # Serial entrepreneur
    if any(kw in pedigree for kw in ["serial", "founded", "exited", "acquisition"]):
        score += 10

    # Strategic investors backing
    if any(kw in pedigree for kw in ["intel ceo", "databricks", "sequoia", "a16z"]):
        score += 10

    return min(100, score)


def _score_traction(founder: Founder, investor: Investor) -> float:
    """Score 0-100: Startup traction signals."""
    traction = (founder.traction + " " + founder.stage).lower()
    score = 50.0

    # Funding amount signals
    import re
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

    # Oversubscribed signal
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
    if any(kw in positioning for kw in ["first", "native", "default"]):
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

    # Check for compatible styles
    compatible = [
        ("technical", "technical"),
        ("enterprise", "enterprise"),
        ("developer", "developer"),
        ("product", "product"),
    ]
    for f_kw, i_kw in compatible:
        if any(f_kw in s for s in f_style) and any(i_kw in s for s in i_style):
            return 70.0
    return 50.0


def _score_social_proof(founder: Founder) -> float:
    """Score 0-100: Social proof strength."""
    proof = (founder.social_proof + " " + founder.traction).lower()
    score = 50.0

    strong_signals = ["wsj", "cnbc", "techcrunch", "bloomberg", "forbes", "nyt"]
    for signal in strong_signals:
        if signal in proof:
            score += 10
            break

    if any(kw in proof for kw in ["yc", "y combinator", "accelerator"]):
        score += 15

    if any(kw in proof for kw in ["elevenlabs", "openai", "anthropic"]):
        score += 10

    return min(100, score)


def _score_investor_behavior(investor: Investor) -> float:
    """Score 0-100: Investor response likelihood."""
    behavior = investor.response_behavior.lower()
    if "high" in behavior:
        return 85.0
    if "moderate" in behavior:
        return 65.0
    return 50.0


def _score_portfolio_similarity(founder: Founder, investor: Investor) -> float:
    """Score 0-100: Overlap with investor's existing portfolio."""
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
    base = scores.total  # Already 0-100
    # Adjust for investor decision speed
    speed = investor.decision_speed.lower()
    if "fast" in speed or "days" in speed:
        return min(100, base + 10)
    if "very fast" in speed:
        return min(100, base + 15)
    return base


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
        conversion_likelihood=0.0,  # Set below
    )
    scores.conversion_likelihood = _score_conversion(founder, investor, scores)
    return scores


def find_top_matches(
    founders: List[Founder],
    investors: List[Investor],
    top_n: int = 10,
) -> List[Match]:
    """Find the top N founder-investor matches."""
    all_matches = []

    for founder in founders:
        for investor in investors:
            scores = calculate_match_score(founder, investor)
            total = scores.total

            if total >= 60:  # Only consider matches above threshold
                match = Match(
                    founder=founder,
                    investor=investor,
                    score=scores,
                    total_score=total,
                    match_rationale="",  # Filled by report generator
                    concerns=[],
                    meeting_acceptance_likelihood=min(100, total + 5),
                    investment_probability=max(0, total - 15),
                    ideal_communication_style=investor.communication_style,
                    best_timing="Within 1-2 weeks",
                    warm_intro_pathways=investor.warm_intro_paths,
                    intro_email_draft="",
                )
                all_matches.append(match)

    # Sort by total score descending
    all_matches.sort(key=lambda m: m.total_score, reverse=True)

    # Deduplicate: one match per investor and per founder
    seen_investors = set()
    seen_founders = set()
    unique_matches = []

    for match in all_matches:
        if (
            match.investor.id not in seen_investors
            and match.founder.id not in seen_founders
        ):
            seen_investors.add(match.investor.id)
            seen_founders.add(match.founder.id)
            unique_matches.append(match)

        if len(unique_matches) >= top_n:
            break

    return unique_matches
