"""
Core matching engine v2 for AI Venture Relationship Intelligence Agent.

Scores founder-investor compatibility across 18 dimensions in 5 categories:
  - Core Fit (40%): industry, stage, geography, portfolio
  - Founder Strength (25%): pedigree, team, technical depth
  - Business Quality (20%): revenue, growth, moat
  - Market & Signal (15%): positioning, social proof, regulatory
  - Relationship: communication, responsiveness, reputation, intros, conversion

Supports many-to-many matching.
"""

import re
from typing import List, Optional, Dict
from .models import Investor, Founder, MatchScore, Match


# ── AI Subsector Classification ──

AI_SUBSECTORS = {
    "infrastructure": ["infra", "compute", "gpu", "cloud", "devops", "mlops", "training", "inference", "serverless"],
    "agents": ["agent", "copilot", "assistant", "automation", "workflow", "orchestration", "agentic"],
    "healthcare": ["health", "medical", "clinical", "biotech", "pharma", "drug", "diagnostic", "patient"],
    "fintech": ["finance", "fintech", "wealth", "banking", "payment", "insurance", "compliance", "securities", "trading"],
    "defense": ["defense", "military", "autonomous", "fleet", "drone", "security", "offensive", "tactical"],
    "developer_tools": ["developer", "devtools", "coding", "ide", "sdk", "api", "open-source", "devtool"],
    "enterprise": ["enterprise", "b2b", "saas", "crm", "erp", "productivity", "workflow"],
    "consumer": ["consumer", "social", "creator", "content", "media", "gaming", "entertainment", "character"],
    "legal": ["legal", "law", "compliance", "regulatory", "litigation"],
    "robotics": ["robot", "humanoid", "physical", "embodied", "manipulation"],
    "space": ["space", "orbital", "satellite", "orbit", "aerospace"],
    "energy": ["energy", "quantum", "chip", "semiconductor", "power", "battery"],
    "drug_discovery": ["drug discovery", "pharmaceutical", "protein", "alphafold", "molecular", "bio"],
    "crypto": ["crypto", "blockchain", "web3", "defi", "token"],
    "voice": ["voice", "speech", "audio", "conversational", "tts", "stt"],
    "data": ["data", "analytics", "visualization", "labeling", "annotation", "synthetic"],
    "search": ["search", "knowledge", "retrieval", "rag", "retrieval-augmented"],
    "foundation": ["foundation model", "llm", "large language", "gpt", "transformer", "pre-training"],
    "cybersecurity": ["cyber", "penetration", "soc", "threat", "vulnerability", "ransomware"],
    "construction": ["construction", "supply chain", "procurement", "logistics"],
}


# ── Capital Needs Assessment ──

def _extract_total_raised_millions(stage_text: str) -> float:
    """Extract total raised amount in millions from stage text like 'Growth ($352M raised)'."""
    text = stage_text.lower().strip()
    # Match patterns like "$352m raised", "$230m total", "$1.5b"
    m = re.search(r'\$([\d.]+)\s*([bm])\b', text)
    if m:
        val = float(m.group(1))
        unit = m.group(2)
        return val * 1000 if unit == 'b' else val
    return 0.0


def _extract_stage_label(stage_text: str) -> str:
    """Extract normalized stage label from stage text."""
    stage = stage_text.lower()
    stage_map = [
        ("pre-seed", ["pre-seed", "preseed"]),
        ("seed", ["seed"]),
        ("series_a", ["series a"]),
        ("series_b", ["series b"]),
        ("series_c", ["series c"]),
        ("growth", ["growth", "series d", "series e", "late stage"]),
    ]
    for label, keywords in stage_map:
        if any(kw in stage for kw in keywords):
            return label
    return "unknown"


def assess_capital_needs(founder: Founder) -> Founder:
    """Assess whether a founder needs capital and set needs_capital/capital_stage.
    
    Rules:
    - Stage: Pre-Seed through Series A ($0-$50M raised) → actively_raising
    - Stage: Series B ($50-100M) → monitor  
    - Stage: Growth ($100M+) → well_capitalized
    - Year incorporated: before 2015 AND growth stage → well_capitalized
    - Projected sales $50M+ → well_capitalized
    - Projected sales $0-10M + early stage → actively_raising
    
    Regional note: $100M+ threshold applied globally (works for India too —
    companies like Freshworks, Postman raised $100M+ are well-capitalized).
    """
    total_raised = _extract_total_raised_millions(founder.stage)
    stage_label = _extract_stage_label(founder.stage)
    sales_mag = _extract_sales_magnitude(founder.projected_sales_y1)
    
    year_ok = True
    if founder.year_incorporated:
        try:
            year = int(founder.year_incorporated)
            year_ok = year >= 2015
        except ValueError:
            year_ok = True
    
    notes = []
    capital_stage = "actively_raising"
    needs_capital = True
    
    # Primary signal: total raised + stage
    if total_raised >= 100 or stage_label == "growth":
        capital_stage = "well_capitalized"
        needs_capital = False
        notes.append(f"${total_raised:.0f}M raised, {stage_label} stage")
    elif total_raised >= 50 or stage_label in ("series_b", "series_c"):
        capital_stage = "monitor"
        needs_capital = True  # Might be raising next round
        notes.append(f"${total_raised:.0f}M raised, {stage_label} — monitor for next round")
    elif total_raised > 0:
        capital_stage = "actively_raising"
        needs_capital = True
        notes.append(f"${total_raised:.0f}M raised, {stage_label} — likely seeking capital")
    
    # Secondary signal: projected sales (only upgrade, never downgrade from stage logic)
    if sales_mag >= 50 and capital_stage == "actively_raising":
        capital_stage = "well_capitalized"
        needs_capital = False
        notes.append(f"${sales_mag:.0f}M projected sales — self-sustaining")
    elif sales_mag >= 50 and capital_stage == "monitor":
        # High sales + mid-stage → upgrade to well_capitalized
        capital_stage = "well_capitalized"
        needs_capital = False
        notes.append(f"${sales_mag:.0f}M projected sales — self-sustaining despite mid-stage")
    elif sales_mag >= 10 and capital_stage == "actively_raising":
        capital_stage = "monitor"
        notes.append(f"${sales_mag:.0f}M projected sales — approaching sustainability")
    elif sales_mag >= 10:
        notes.append(f"${sales_mag:.0f}M projected sales — approaching sustainability")
    
    # Tertiary signal: company age (only finalize, never override stage+sales)
    if not year_ok and capital_stage == "monitor":
        capital_stage = "well_capitalized"
        needs_capital = False
        notes.append(f"Founded {founder.year_incorporated} — established company")
    
    founder.needs_capital = needs_capital
    founder.capital_stage = capital_stage
    founder.capital_notes = "; ".join(notes)
    return founder


def filter_capital_ready(founders: List[Founder]) -> List[Founder]:
    """Filter founders to only those who likely need capital.
    Applies capital assessment first if not already done."""
    result = []
    for f in founders:
        if not f.capital_notes:  # Not yet assessed
            assess_capital_needs(f)
        if f.needs_capital:
            result.append(f)
    return result


def _classify_subsector(text: str) -> List[str]:
    """Classify text into AI subsectors."""
    text_lower = text.lower()
    matched = []
    for sector, keywords in AI_SUBSECTORS.items():
        if any(kw in text_lower for kw in keywords):
            matched.append(sector)
    return matched or ["general_ai"]


def _extract_growth_pct(text: str) -> float:
    """Extract growth percentage from text like '320%' or '3x'."""
    if not text:
        return 0.0
    text = text.lower().strip()
    # Match "320%" or "320"
    m = re.search(r'(\d+)%', text)
    if m:
        return float(m.group(1))
    # Match "3x" or "3.5x"
    m = re.search(r'([\d.]+)x', text)
    if m:
        return float(m.group(1)) * 100 - 100
    # Match "N/A" or "pre-revenue"
    if any(kw in text for kw in ["n/a", "pre-revenue", "pre revenue", "new"]):
        return 0.0
    return 0.0


def _extract_sales_magnitude(text: str) -> float:
    """Extract sales magnitude from text like '$2-5M' or '$100-200M'."""
    if not text:
        return 0.0
    text = text.lower().strip()
    # Match "$2-5m" or "$100-200m"
    m = re.search(r'\$([\d.]+)\s*-\s*([\d.]+)\s*([mbk])', text)
    if m:
        low, high = float(m.group(1)), float(m.group(2))
        unit = m.group(3)
        avg = (low + high) / 2
        if unit == 'b':
            return avg * 1000
        elif unit == 'm':
            return avg
        elif unit == 'k':
            return avg / 1000
    # Match "$50m" single value
    m = re.search(r'\$([\d.]+)\s*([mbk])', text)
    if m:
        val = float(m.group(1))
        unit = m.group(2)
        if unit == 'b':
            return val * 1000
        elif unit == 'm':
            return val
        elif unit == 'k':
            return val / 1000
    return 0.0


# ── Scoring Functions (0-100 each) ──

def _score_industry_alignment(founder: Founder, investor: Investor) -> float:
    """Sector & subsector overlap between founder and investor focus."""
    founder_sectors = set(_classify_subsector(
        f"{founder.ai_subsector} {founder.brand_positioning} {founder.ideal_investor_profile} {founder.mission}"
    ))
    investor_sectors = set(_classify_subsector(
        " ".join(investor.ai_focus) + " " + investor.firm + " " + " ".join(investor.portfolio)
    ))
    overlap = founder_sectors & investor_sectors
    if "general_ai" in overlap:
        overlap.discard("general_ai")
    if overlap:
        return min(100, 60 + len(overlap) * 12)
    # Partial: check if any keywords loosely match
    founder_text = f"{founder.ai_subsector} {founder.mission}".lower()
    focus_text = " ".join(investor.ai_focus).lower()
    if any(kw in founder_text for kw in focus_text.split() if len(kw) > 3):
        return 50.0
    return 35.0


def _score_stage_compatibility(founder: Founder, investor: Investor) -> float:
    """Does the founder's stage match the investor's focus?"""
    stage = founder.stage.lower()
    investor_stages = [s.lower() for s in investor.stage_focus]

    # Determine stage label
    stage_map = [
        ("pre-seed", ["pre-seed", "preseed"]),
        ("seed", ["seed"]),
        ("series a", ["series a"]),
        ("series b", ["series b"]),
        ("series c", ["series c"]),
        ("growth", ["growth", "series d", "series e"]),
    ]
    stage_label = ""
    for label, keywords in stage_map:
        if any(kw in stage for kw in keywords):
            stage_label = label
            break

    if stage_label:
        # Direct match
        for s in investor_stages:
            if stage_label in s or s in stage_label:
                return 92.0
        # Adjacent stage
        adjacent = {
            "pre-seed": ["seed"],
            "seed": ["pre-seed", "series a"],
            "series a": ["seed", "series b"],
            "series b": ["series a", "series c"],
            "series c": ["series b", "growth"],
            "growth": ["series c"],
        }
        for adj in adjacent.get(stage_label, []):
            if any(adj in s for s in investor_stages):
                return 72.0
        # "All stages" investors
        if any("all" in s or "stage-agnostic" in s for s in investor_stages):
            return 80.0
    return 45.0


def _score_geography(founder: Founder, investor: Investor) -> float:
    """Geographic alignment — expanded beyond US/EU binary."""
    f_loc = founder.location.lower().strip()
    i_loc = investor.geography.lower().strip()

    # Exact match
    if any(region in f_loc and region in i_loc for region in ["us", "europe", "asia", "india", "singapore", "uk", "israel"]):
        return 92.0

    # Global investors match everyone
    if "global" in i_loc or "worldwide" in i_loc:
        return 78.0

    # Regional proximity
    region_groups = {
        "north_america": ["us", "usa", "united states", "canada", "san francisco", "new york", "palo alto", "boston", "seattle", "austin"],
        "europe": ["europe", "uk", "london", "berlin", "paris", "france", "germany", "poland", "sweden", "netherlands"],
        "asia": ["asia", "singapore", "india", "bengaluru", "bangalore", "mumbai", "delhi", "tokyo", "seoul", "hong kong", "shanghai", "beijing"],
        "middle_east": ["israel", "tel aviv", "dubai", "uae"],
    }
    f_region = None
    i_region = None
    for region, keywords in region_groups.items():
        if any(kw in f_loc for kw in keywords):
            f_region = region
        if any(kw in i_loc for kw in keywords):
            i_region = region

    if f_region and i_region:
        if f_region == i_region:
            return 80.0
        # US investors often invest in Israel, Europe
        if (f_region == "middle_east" and i_region == "north_america") or \
           (f_region == "north_america" and i_region == "middle_east"):
            return 65.0
    return 50.0


def _score_founder_pedigree(founder: Founder, investor: Investor) -> float:
    """Founder background, track record, and experience."""
    pedigree = (founder.founder_pedigree + " " + founder.background).lower()
    score = 45.0

    # Big tech experience
    big_tech = ["google", "meta", "openai", "deepmind", "amazon", "apple", "microsoft", "twitter", "nvidia", "tesla", "anthropic"]
    for company in big_tech:
        if company in pedigree:
            score += 8
            break

    # Academic credentials
    if any(kw in pedigree for kw in ["professor", "phd", "ph.d", "stanford", "mit", "cmu", "berkeley", "harvard"]):
        score += 10

    # Serial entrepreneur / exits
    if any(kw in pedigree for kw in ["serial", "founded", "exited", "acquisition", "ipo", "previous startup"]):
        score += 12

    # Domain expertise
    if any(kw in pedigree for kw in ["years experience", "expert", "lead", "head of", "vp", "cto", "ceo"]):
        score += 5

    # Top-tier backing signals
    if any(kw in pedigree for kw in ["yc", "y combinator", "sequoia", "a16z", "accel"]):
        score += 5

    # Year incorporated — younger companies with traction get bonus
    if founder.year_incorporated:
        try:
            years_active = 2026 - int(founder.year_incorporated)
            if years_active <= 2:
                score += 5  # Early stage, fast progress
        except ValueError:
            pass

    return min(100, score)


def _score_team_composition(founder: Founder) -> float:
    """Balance of AI PhDs + domain experts + GTM talent."""
    if not founder.team_composition:
        # Infer from background
        bg = (founder.background + " " + founder.founder_pedigree).lower()
        score = 50.0
        if any(kw in bg for kw in ["phd", "professor", "research", "paper", "published"]):
            score += 15
        if any(kw in bg for kw in ["domain", "industry", "years in", "practitioner"]):
            score += 10
        if any(kw in bg for kw in ["sales", "marketing", "growth", "gtm", "revenue"]):
            score += 10
        return min(100, score)

    team = founder.team_composition.lower()
    score = 40.0
    if any(kw in team for kw in ["phd", "researcher", "scientist", "papers", "patents"]):
        score += 20
    if any(kw in team for kw in ["domain expert", "industry veteran", "practitioner", "10+ years"]):
        score += 15
    if any(kw in team for kw in ["gtm", "sales lead", "marketing", "revenue", "growth lead"]):
        score += 15
    if any(kw in team for kw in ["ex-openai", "ex-google", "ex-deepmind", "ex-meta"]):
        score += 10
    return min(100, score)


def _score_technical_depth(founder: Founder) -> float:
    """Is it real AI or a GPT wrapper? Proprietary models, self-hosted, data moats."""
    tech = (founder.technical_depth + " " + founder.brand_positioning + " " + founder.ai_subsector).lower()
    score = 40.0

    # Proprietary models / self-hosted
    if any(kw in tech for kw in ["proprietary model", "self-hosted", "own model", "custom model", "fine-tuned", "trained from scratch"]):
        score += 25
    elif any(kw in tech for kw in ["fine-tun", "custom train", "domain-specific"]):
        score += 15

    # Research output
    if any(kw in tech for kw in ["paper", "published", "research", "arxiv", "patent"]):
        score += 10

    # Open source contributions
    if any(kw in tech for kw in ["open-source", "open source", "github", "community"]):
        score += 8

    # Proprietary data
    if any(kw in tech for kw in ["proprietary data", "unique dataset", "exclusive data", "data moat"]):
        score += 15

    # Infrastructure depth
    if any(kw in tech for kw in ["inference optimization", "training infra", "custom architecture", "novel architecture"]):
        score += 10

    return min(100, score)


def _score_revenue_traction(founder: Founder) -> float:
    """Revenue, customers, growth metrics — uses new fields too."""
    import re
    traction = (founder.traction + " " + founder.stage).lower()
    score = 35.0

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

    # Projected sales
    sales_mag = _extract_sales_magnitude(founder.projected_sales_y1)
    if sales_mag >= 100:
        score += 15
    elif sales_mag >= 20:
        score += 10
    elif sales_mag >= 5:
        score += 7
    elif sales_mag > 0:
        score += 3

    # Oversubscribed
    if "oversubscribed" in traction:
        score += 8

    # Customer signals
    if any(kw in traction for kw in ["fortune 500", "enterprise customer", "100+ customer", "1000+ customer"]):
        score += 8

    return min(100, score)


def _score_growth_momentum(founder: Founder) -> float:
    """12-month growth and velocity — now uses actual growth_last_12mo data."""
    growth_pct = _extract_growth_pct(founder.growth_last_12mo)
    velocity = founder.growth_velocity.lower()

    # Start with growth data
    if growth_pct >= 500:
        score = 95.0
    elif growth_pct >= 300:
        score = 85.0
    elif growth_pct >= 200:
        score = 75.0
    elif growth_pct >= 100:
        score = 65.0
    elif growth_pct >= 50:
        score = 55.0
    elif growth_pct > 0:
        score = 45.0
    else:
        # Fall back to velocity text
        if "very high" in velocity:
            score = 85.0
        elif "high" in velocity:
            score = 70.0
        elif "moderate" in velocity:
            score = 50.0
        else:
            score = 40.0

    # Bonus for velocity text on top of data
    if growth_pct > 0:
        if "very high" in velocity:
            score = min(100, score + 8)
        elif "high" in velocity:
            score = min(100, score + 4)

    return score


def _score_moat_defensibility(founder: Founder) -> float:
    """Data moats, proprietary IP, network effects — #1 VC concern in 2026."""
    moat = (founder.moat + " " + founder.brand_positioning + " " + founder.technical_depth).lower()
    score = 35.0

    # Data moats
    if any(kw in moat for kw in ["proprietary data", "exclusive data", "data moat", "unique dataset", "data network effect"]):
        score += 25
    elif any(kw in moat for kw in ["data advantage", "growing dataset", "domain data"]):
        score += 15

    # Network effects
    if any(kw in moat for kw in ["network effect", "marketplace", "platform effect", "viral"]):
        score += 20

    # IP / Patents
    if any(kw in moat for kw in ["patent", "ip", "intellectual property", "trade secret"]):
        score += 15

    # Switching costs
    if any(kw in moat for kw in ["switching cost", "lock-in", "embedded", "workflow integration"]):
        score += 10

    # Category leadership
    if any(kw in moat for kw in ["category leader", "default", "standard", "de facto", "first mover"]):
        score += 10

    # Infer from brand positioning if moat field is empty
    if not founder.moat:
        pos = founder.brand_positioning.lower()
        if any(kw in pos for kw in ["category", "infrastructure", "platform", "protocol", "default"]):
            score += 15
        if any(kw in pos for kw in ["first", "native", "autonomous", "only"]):
            score += 10

    return min(100, score)


def _score_market_positioning(founder: Founder) -> float:
    """Brand strength and category leadership."""
    positioning = founder.brand_positioning.lower()
    score = 45.0
    if any(kw in positioning for kw in ["category", "infrastructure", "platform", "protocol"]):
        score += 18
    if any(kw in positioning for kw in ["first", "native", "default", "autonomous", "only"]):
        score += 12
    if any(kw in positioning for kw in ["defining", "leading", "pioneering"]):
        score += 10
    return min(100, score)


def _score_social_proof(founder: Founder) -> float:
    """Media coverage, notable investors, accelerators, customer logos."""
    proof = (founder.social_proof + " " + founder.traction).lower()
    score = 40.0

    # Major media
    media_outlets = ["wsj", "cnbc", "techcrunch", "bloomberg", "forbes", "nyt", "financial times", "wired", "the information"]
    for outlet in media_outlets:
        if outlet in proof:
            score += 8
            break

    # Accelerators
    if any(kw in proof for kw in ["yc", "y combinator", "accelerator", "techstars"]):
        score += 12

    # Notable backers
    notable = ["elevenlabs", "openai", "anthropic", "sequoia", "a16z", "khosla", "google", "microsoft"]
    for backer in notable:
        if backer in proof:
            score += 8
            break

    # Valuation signals
    if any(kw in proof for kw in ["billion", "$1b", "$2b", "unicorn"]):
        score += 10

    # Customer logos
    if any(kw in proof for kw in ["fortune 500", "enterprise", "government", "dod"]):
        score += 8

    return min(100, score)


def _score_regulatory_readiness(founder: Founder) -> float:
    """Compliance, ethics, data governance — critical in 2026 EU AI Act era."""
    if not founder.regulatory_readiness:
        # Infer from sector — healthcare, fintech, defense need this most
        sector = founder.ai_subsector.lower()
        if any(kw in sector for kw in ["health", "fintech", "finance", "defense", "legal", "compliance"]):
            return 55.0  # Neutral — assume they handle it
        return 50.0

    reg = founder.regulatory_readiness.lower()
    score = 40.0
    if any(kw in reg for kw in ["soc 2", "soc2", "iso 27001", "hipaa", "gdpr", "compliant"]):
        score += 25
    if any(kw in reg for kw in ["bias detection", "fairness", "ethics", "responsible ai", "ai governance"]):
        score += 15
    if any(kw in reg for kw in ["eu ai act", "ftc", "regulatory", "audit"]):
        score += 10
    if any(kw in reg for kw in ["data governance", "privacy", "encryption", "security audit"]):
        score += 10
    return min(100, score)


def _score_communication_fit(founder: Founder, investor: Investor) -> float:
    """Communication style compatibility."""
    f_style = set(founder.communication_style.lower().split(", "))
    i_style = set(investor.communication_style.lower().split(", "))

    overlap = f_style & i_style
    if len(overlap) >= 2:
        return 90.0
    if overlap:
        return 75.0

    # Semantic matching
    pairs = [
        ("technical", "technical"), ("enterprise", "enterprise"),
        ("developer", "developer"), ("product", "product"),
        ("security", "security"), ("research", "research"),
        ("fintech", "fintech"), ("healthcare", "healthcare"),
        ("data-driven", "data"), ("visionary", "visionary"),
    ]
    for f_kw, i_kw in pairs:
        if any(f_kw in s for s in f_style) and any(i_kw in s for s in i_style):
            return 70.0
    return 50.0


def _score_investor_responsiveness(investor: Investor) -> float:
    """How responsive is this investor?"""
    behavior = investor.response_behavior.lower()
    if "very high" in behavior or "fast" in behavior:
        return 90.0
    if "high" in behavior:
        return 80.0
    if "moderate" in behavior:
        return 60.0
    return 45.0


def _score_investor_reputation(investor: Investor) -> float:
    """Investor reputation in the ecosystem."""
    return min(100, investor.reputation_score * 10)


def _score_warm_intro_access(founder: Founder, investor: Investor) -> float:
    """Warm introduction pathway availability."""
    paths = len(investor.warm_intro_paths)
    if paths >= 4:
        return 88.0
    if paths >= 3:
        return 72.0
    if paths >= 2:
        return 58.0
    if paths >= 1:
        return 45.0
    return 35.0


def _score_conversion(founder: Founder, investor: Investor, scores: MatchScore) -> float:
    """Overall conversion probability estimate."""
    base = scores.total
    speed = investor.decision_speed.lower()
    if "very fast" in speed or "48h" in speed:
        return min(100, base + 12)
    if "fast" in speed or "days" in speed:
        return min(100, base + 8)
    if "weeks" in speed:
        return min(100, base + 3)
    return base


def _score_portfolio_similarity(founder: Founder, investor: Investor) -> float:
    """How similar is this to the investor's existing portfolio?"""
    founder_text = (founder.ai_subsector + " " + founder.brand_positioning + " " + founder.mission).lower()
    portfolio_text = " ".join(investor.portfolio).lower()
    focus_text = " ".join(investor.ai_focus).lower()

    # Count meaningful keyword overlaps
    founder_words = set(w for w in founder_text.split() if len(w) > 3)
    portfolio_words = set(portfolio_text.split() + focus_text.split())
    overlap = founder_words & portfolio_words

    return min(100, 35 + len(overlap) * 8)


# ── Main API ──

def calculate_match_score(founder: Founder, investor: Investor) -> MatchScore:
    """Calculate detailed match score between a founder and investor across 18 dimensions."""
    scores = MatchScore(
        # Core Fit
        industry_alignment=_score_industry_alignment(founder, investor),
        stage_compatibility=_score_stage_compatibility(founder, investor),
        geography_preference=_score_geography(founder, investor),
        portfolio_similarity=_score_portfolio_similarity(founder, investor),
        # Founder Strength
        founder_pedigree=_score_founder_pedigree(founder, investor),
        team_composition=_score_team_composition(founder),
        technical_depth=_score_technical_depth(founder),
        # Business Quality
        revenue_traction=_score_revenue_traction(founder),
        growth_momentum=_score_growth_momentum(founder),
        moat_defensibility=_score_moat_defensibility(founder),
        # Market & Signal
        market_positioning=_score_market_positioning(founder),
        social_proof=_score_social_proof(founder),
        regulatory_readiness=_score_regulatory_readiness(founder),
        # Relationship
        communication_fit=_score_communication_fit(founder, investor),
        investor_responsiveness=_score_investor_responsiveness(investor),
        investor_reputation=_score_investor_reputation(investor),
        warm_intro_access=_score_warm_intro_access(founder, investor),
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


def _smart_top_n(matches: List[Match], top_n: int = 10) -> List[Match]:
    """Select top N matches using tier-based logic.
    
    Keeps ALL matches at the highest score tier, then fills remaining
    slots from the next tier(s). Example with top_n=10:
    - If 1 match at 74, keep it (1/10 used)
    - If 6 matches at 73, keep all 6 (7/10 used)
    - Fill remaining 3 from 72s, then 71s, etc.
    """
    if not matches or top_n <= 0:
        return []
    
    # Group by integer score tier
    from collections import defaultdict
    tiers = defaultdict(list)
    for m in matches:
        tier = int(m.total_score)  # 73.5 -> 73
        tiers[tier].append(m)
    
    # Sort tiers descending
    sorted_tiers = sorted(tiers.keys(), reverse=True)
    
    result = []
    for tier in sorted_tiers:
        tier_matches = tiers[tier]
        remaining = top_n - len(result)
        if remaining <= 0:
            break
        if len(tier_matches) <= remaining:
            result.extend(tier_matches)
        else:
            # Take top N from this tier by exact score
            tier_matches.sort(key=lambda m: m.total_score, reverse=True)
            result.extend(tier_matches[:remaining])
    
    return result


def find_top_matches(
    founders: List[Founder],
    investors: List[Investor],
    top_n: int = 10,
    min_score: float = 55.0,
    filter_capital: bool = True,
) -> List[Match]:
    """Find top N matches across ALL founders and investors (many-to-many).
    
    By default, filters out well-capitalized founders who don't need capital.
    Uses smart tiering: keeps all matches at highest score tier, then fills
    remaining slots from next tiers.
    """
    # Assess capital needs and filter
    if filter_capital:
        founders = filter_capital_ready(founders)
        if not founders:
            return []
    
    all_matches = []
    for founder in founders:
        for investor in investors:
            scores = calculate_match_score(founder, investor)
            total = scores.total
            if total >= min_score:
                all_matches.append(_build_match(founder, investor, scores, total))
    all_matches.sort(key=lambda m: m.total_score, reverse=True)
    return _smart_top_n(all_matches, top_n)


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
    """Get a complete match matrix: for each founder, their ranked investor matches."""
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
