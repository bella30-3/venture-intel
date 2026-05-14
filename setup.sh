#!/bin/bash
# AI Venture Relationship Intelligence Agent - Setup Script
# Paste this into your Mac terminal to create the full project

set -e

PROJECT_DIR="$HOME/venture-intel"
echo "🚀 Creating project at $PROJECT_DIR ..."

mkdir -p "$PROJECT_DIR"/{src,data,reports,templates,tests,.github/workflows}
cd "$PROJECT_DIR"

# ─────────────────────────────────────────────
# requirements.txt
# ─────────────────────────────────────────────
cat > requirements.txt << 'ENDOFFILE'
requests>=2.31.0
beautifulsoup4>=4.12.0
feedparser>=6.0.0
secure-smtplib>=0.1.0
pydantic>=2.0.0
jinja2>=3.1.0
schedule>=1.2.0
python-dotenv>=1.0.0
ENDOFFILE

# ─────────────────────────────────────────────
# .env.example
# ─────────────────────────────────────────────
cat > .env.example << 'ENDOFFILE'
# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com
EMAIL_TO=pooja0360@yahoo.com,ubella93@gmail.com
ENDOFFILE

# ─────────────────────────────────────────────
# .gitignore
# ─────────────────────────────────────────────
cat > .gitignore << 'ENDOFFILE'
.env
.env.local
*.pyc
__pycache__/
.vscode/
.idea/
.DS_Store
Thumbs.db
*.tmp
*.log
ENDOFFILE

# ─────────────────────────────────────────────
# config.json
# ─────────────────────────────────────────────
cat > config.json << 'ENDOFFILE'
{
  "version": "1.0",
  "criteria": {
    "industry_alignment": { "weight": 0.15 },
    "stage_compatibility": { "weight": 0.12 },
    "geography_preference": { "weight": 0.05 },
    "founder_track_record": { "weight": 0.12 },
    "startup_traction": { "weight": 0.10 },
    "growth_velocity": { "weight": 0.08 },
    "brand_positioning": { "weight": 0.05 },
    "communication_style": { "weight": 0.05 },
    "social_proof": { "weight": 0.05 },
    "investor_response_behavior": { "weight": 0.05 },
    "portfolio_similarity": { "weight": 0.05 },
    "reputation_score": { "weight": 0.05 },
    "relationship_proximity": { "weight": 0.05 },
    "conversion_likelihood": { "weight": 0.03 }
  }
}
ENDOFFILE

# ─────────────────────────────────────────────
# src/__init__.py
# ─────────────────────────────────────────────
cat > src/__init__.py << 'ENDOFFILE'
"""AI Venture Relationship Intelligence Agent"""
__version__ = "1.0.0"
ENDOFFILE

# ─────────────────────────────────────────────
# src/models.py
# ─────────────────────────────────────────────
cat > src/models.py << 'ENDOFFILE'
"""Data models for investors and founders."""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Investor:
    id: str
    name: str
    firm: str
    type: str
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
    reputation_score: int
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
        return round(sum(getattr(self, k) * v for k, v in weights.items()), 1)


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
ENDOFFILE

# ─────────────────────────────────────────────
# src/matcher.py
# ─────────────────────────────────────────────
cat > src/matcher.py << 'ENDOFFILE'
"""Core matching engine - scores founder-investor compatibility."""
from typing import List
from .models import Investor, Founder, MatchScore, Match

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
    text_lower = text.lower()
    matched = []
    for sector, keywords in AI_SUBSECTORS.items():
        if any(kw in text_lower for kw in keywords):
            matched.append(sector)
    return matched or ["general_ai"]


def _score_industry_alignment(founder: Founder, investor: Investor) -> float:
    founder_sectors = set(_classify_subsector(
        f"{founder.ai_subsector} {founder.brand_positioning} {founder.ideal_investor_profile}"
    ))
    investor_sectors = set(_classify_subsector(
        " ".join(investor.ai_focus) + " " + investor.firm
    ))
    overlap = founder_sectors & investor_sectors
    return min(100, 60 + len(overlap) * 15) if overlap else 40.0


def _score_stage_compatibility(founder: Founder, investor: Investor) -> float:
    import re
    stage = founder.stage.lower()
    investor_stages = [s.lower() for s in investor.stage_focus]
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
        if stage_label in ["pre-seed", "seed"] and any("seed" in s for s in investor_stages):
            return 80.0
        if stage_label in ["series a", "series b"] and any("series" in s for s in investor_stages):
            return 70.0
    return 50.0


def _score_geography(founder: Founder, investor: Investor) -> float:
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
    pedigree = (founder.founder_pedigree + " " + founder.background).lower()
    score = 50.0
    for c in ["google", "meta", "openai", "deepmind", "amazon", "apple", "microsoft", "twitter"]:
        if c in pedigree:
            score += 10
            break
    if any(kw in pedigree for kw in ["professor", "phd", "stanford", "mit", "cmu"]):
        score += 10
    if any(kw in pedigree for kw in ["serial", "founded", "exited", "acquisition"]):
        score += 10
    if any(kw in pedigree for kw in ["intel ceo", "databricks", "sequoia", "a16z"]):
        score += 10
    return min(100, score)


def _score_traction(founder: Founder, investor: Investor) -> float:
    import re
    traction = (founder.traction + " " + founder.stage).lower()
    score = 50.0
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
    if "oversubscribed" in traction:
        score += 10
    return min(100, score)


def _score_growth_velocity(founder: Founder) -> float:
    velocity = founder.growth_velocity.lower()
    if "very high" in velocity:
        return 95.0
    if "high" in velocity:
        return 80.0
    if "moderate" in velocity:
        return 60.0
    return 50.0


def _score_brand_positioning(founder: Founder) -> float:
    positioning = founder.brand_positioning.lower()
    score = 50.0
    if any(kw in positioning for kw in ["category", "infrastructure", "platform", "protocol"]):
        score += 20
    if any(kw in positioning for kw in ["first", "native", "default"]):
        score += 15
    return min(100, score)


def _score_communication_style(founder: Founder, investor: Investor) -> float:
    f_style = set(founder.communication_style.lower().split(", "))
    i_style = set(investor.communication_style.lower().split(", "))
    overlap = f_style & i_style
    if len(overlap) >= 2:
        return 90.0
    if overlap:
        return 75.0
    for f_kw, i_kw in [("technical","technical"),("enterprise","enterprise"),("developer","developer"),("product","product")]:
        if any(f_kw in s for s in f_style) and any(i_kw in s for s in i_style):
            return 70.0
    return 50.0


def _score_social_proof(founder: Founder) -> float:
    proof = (founder.social_proof + " " + founder.traction).lower()
    score = 50.0
    for s in ["wsj", "cnbc", "techcrunch", "bloomberg", "forbes", "nyt"]:
        if s in proof:
            score += 10
            break
    if any(kw in proof for kw in ["yc", "y combinator", "accelerator"]):
        score += 15
    if any(kw in proof for kw in ["elevenlabs", "openai", "anthropic"]):
        score += 10
    return min(100, score)


def _score_investor_behavior(investor: Investor) -> float:
    behavior = investor.response_behavior.lower()
    if "high" in behavior:
        return 85.0
    if "moderate" in behavior:
        return 65.0
    return 50.0


def _score_portfolio_similarity(founder: Founder, investor: Investor) -> float:
    founder_text = (founder.ai_subsector + " " + founder.brand_positioning).lower()
    portfolio_text = " ".join(investor.portfolio).lower()
    focus_text = " ".join(investor.ai_focus).lower()
    overlap_count = 0
    for keyword in founder_text.split():
        if len(keyword) > 3 and (keyword in portfolio_text or keyword in focus_text):
            overlap_count += 1
    return min(100, 40 + overlap_count * 10)


def _score_reputation(investor: Investor) -> float:
    return min(100, investor.reputation_score * 10)


def _score_relationship_proximity(founder: Founder, investor: Investor) -> float:
    paths = len(investor.warm_intro_paths)
    if paths >= 4:
        return 85.0
    if paths >= 3:
        return 70.0
    if paths >= 2:
        return 55.0
    return 40.0


def _score_conversion(founder: Founder, investor: Investor, scores: MatchScore) -> float:
    base = scores.total
    speed = investor.decision_speed.lower()
    if "fast" in speed or "days" in speed:
        return min(100, base + 10)
    if "very fast" in speed:
        return min(100, base + 15)
    return base


def calculate_match_score(founder: Founder, investor: Investor) -> MatchScore:
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


def find_top_matches(founders: List[Founder], investors: List[Investor], top_n: int = 10) -> List[Match]:
    all_matches = []
    for founder in founders:
        for investor in investors:
            scores = calculate_match_score(founder, investor)
            total = scores.total
            if total >= 60:
                match = Match(
                    founder=founder, investor=investor, score=scores, total_score=total,
                    match_rationale="", concerns=[],
                    meeting_acceptance_likelihood=min(100, total + 5),
                    investment_probability=max(0, total - 15),
                    ideal_communication_style=investor.communication_style,
                    best_timing="Within 1-2 weeks",
                    warm_intro_pathways=investor.warm_intro_paths, intro_email_draft="",
                )
                all_matches.append(match)
    all_matches.sort(key=lambda m: m.total_score, reverse=True)
    seen_investors, seen_founders, unique_matches = set(), set(), []
    for match in all_matches:
        if match.investor.id not in seen_investors and match.founder.id not in seen_founders:
            seen_investors.add(match.investor.id)
            seen_founders.add(match.founder.id)
            unique_matches.append(match)
        if len(unique_matches) >= top_n:
            break
    return unique_matches
ENDOFFILE

# ─────────────────────────────────────────────
# src/data_loader.py
# ─────────────────────────────────────────────
cat > src/data_loader.py << 'ENDOFFILE'
"""Load investor and founder data from JSON files."""
import json
from pathlib import Path
from typing import List
from .models import Investor, Founder

DATA_DIR = Path(__file__).parent.parent / "data"


def load_investors(filepath: str = None) -> List[Investor]:
    path = Path(filepath) if filepath else DATA_DIR / "investors.json"
    with open(path, "r") as f:
        data = json.load(f)
    investors = []
    for item in data:
        investors.append(Investor(
            id=item["id"], name=item["name"], firm=item["firm"], type=item["type"],
            check_size=item["check_size"], stage_focus=item["stage_focus"],
            ai_focus=item["ai_focus"], geography=item["geography"],
            portfolio=item["portfolio"], decision_speed=item["decision_speed"],
            communication_style=item["communication_style"],
            response_behavior=item["response_behavior"],
            thought_leadership=item["thought_leadership"],
            warm_intro_paths=item["warm_intro_paths"],
            reputation_score=item["reputation_score"],
            last_activity=item["last_activity"],
            linkedin_url=item.get("linkedin_url"),
            twitter_url=item.get("twitter_url"),
            website=item.get("website"),
        ))
    return investors


def load_founders(filepath: str = None) -> List[Founder]:
    path = Path(filepath) if filepath else DATA_DIR / "founders.json"
    with open(path, "r") as f:
        data = json.load(f)
    founders = []
    for item in data:
        founders.append(Founder(
            id=item["id"], name=item["name"], company=item["company"],
            role=item["role"], background=item["background"], stage=item["stage"],
            ai_subsector=item["ai_subsector"], location=item["location"],
            traction=item["traction"], founder_pedigree=item["founder_pedigree"],
            growth_velocity=item["growth_velocity"],
            brand_positioning=item["brand_positioning"],
            social_proof=item["social_proof"],
            communication_style=item["communication_style"],
            ideal_investor_profile=item["ideal_investor_profile"],
            warm_intro_needs=item["warm_intro_needs"],
            linkedin_url=item.get("linkedin_url"),
            twitter_url=item.get("twitter_url"),
            website=item.get("website"),
            email=item.get("email"),
        ))
    return founders
ENDOFFILE

# ─────────────────────────────────────────────
# src/report_generator.py
# ─────────────────────────────────────────────
cat > src/report_generator.py << 'ENDOFFILE'
"""Generates daily match reports in Markdown and HTML formats."""
from datetime import datetime
from typing import List
from .models import Match


def _score_bar(score: float) -> str:
    filled = int(score / 10)
    return "█" * filled + "░" * (10 - filled)


def _generate_email_draft(match: Match, rank: int) -> str:
    f = match.founder
    i = match.investor
    return f"""Subject: {f.company} — {f.brand_positioning[:60]} × {i.firm}'s {i.focus_areas_display} Thesis

Hi {i.firm} Team,

I'm reaching out because I see a strong alignment between what you're building at {i.firm} and what {f.name} and the {f.company} team are creating.

{f.company} ({f.stage}) is building {f.ai_subsector}. What differentiates them:
- {f.brand_positioning}
- {f.traction[:150]}
- Founder background: {f.founder_pedigree[:150]}

Given {i.firm}'s focus on {i.focus_areas_display} and your portfolio ({', '.join(i.portfolio[:3])}), this represents a compelling fit.

Would you be open to a conversation with {f.name}? Happy to arrange at your convenience.

Best,
[Your Name]"""


def generate_markdown_report(matches: List[Match], report_date: str = None) -> str:
    if report_date is None:
        report_date = datetime.utcnow().strftime("%Y-%m-%d")
    lines = []
    lines.append("# 🤖 AI Venture Relationship Intelligence Report")
    lines.append(f"## Daily Match Digest — {report_date}\n")
    lines.append("**Focus:** AI Founders ↔ AI Investors\n")
    lines.append("---\n")
    lines.append("## 📊 Executive Summary\n")
    avg_score = sum(m.total_score for m in matches) / len(matches) if matches else 0
    lines.append(f"- **{len(matches)} matches** identified (avg score: {avg_score:.1f}/100)\n")
    lines.append("---\n")
    lines.append("## 🏆 TOP MATCHES\n")

    for rank, match in enumerate(matches, 1):
        f, i = match.founder, match.investor
        lines.append(f"### MATCH #{rank} — Score: {match.total_score:.0f}/100\n")
        lines.append(f"**Founder:** {f.name} ({f.company})  ")
        lines.append(f"**Investor:** {i.name} ({i.firm})  ")
        lines.append(f"**Stage:** {f.stage} | **Focus:** {f.ai_subsector}\n")
        lines.append("| Dimension | Score | |")
        lines.append("|-----------|-------|---|")
        score = match.score
        for dim_name, dim_score in [
            ("Industry Alignment", score.industry_alignment),
            ("Stage Compatibility", score.stage_compatibility),
            ("Geography", score.geography_preference),
            ("Founder Track Record", score.founder_track_record),
            ("Traction", score.startup_traction),
            ("Growth Velocity", score.growth_velocity),
            ("Brand Positioning", score.brand_positioning),
            ("Communication Style", score.communication_style),
            ("Social Proof", score.social_proof),
            ("Investor Response", score.investor_response_behavior),
            ("Portfolio Similarity", score.portfolio_similarity),
            ("Reputation", score.reputation_score),
            ("Relationship Proximity", score.relationship_proximity),
            ("Conversion Likelihood", score.conversion_likelihood),
        ]:
            lines.append(f"| {dim_name} | {dim_score:.0f} | {_score_bar(dim_score)} |")
        lines.append("")
        lines.append(f"**Why This Match Is Strong:**")
        lines.append(f"- {i.firm}'s focus on {i.focus_areas_display} aligns with {f.company}'s {f.ai_subsector}")
        lines.append(f"- {f.founder_pedigree[:200]}\n")
        lines.append(f"**Meeting Acceptance:** {match.meeting_acceptance_likelihood:.0f}%  ")
        lines.append(f"**Investment Probability:** {match.investment_probability:.0f}%\n")
        lines.append(f"**Communication Style:** {match.ideal_communication_style}  ")
        lines.append(f"**Best Timing:** {match.best_timing}\n")
        lines.append("**Warm Intro Pathways:**")
        for path in match.warm_intro_pathways:
            lines.append(f"- {path}")
        lines.append(f"\n### 📧 Draft Introduction Email\n")
        lines.append("```")
        lines.append(_generate_email_draft(match, rank))
        lines.append("```\n---\n")

    lines.append(f"*Generated by AI Venture Relationship Intelligence Agent v1.0 — {report_date}*")
    return "\n".join(lines)


def generate_html_report(matches: List[Match], report_date: str = None) -> str:
    if report_date is None:
        report_date = datetime.utcnow().strftime("%Y-%m-%d")
    md = generate_markdown_report(matches, report_date)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>AI Venture Intel - {report_date}</title></head>
<body style="font-family:-apple-system,sans-serif;max-width:800px;margin:0 auto;padding:20px;color:#333;">
<pre style="white-space:pre-wrap;font-family:inherit;">{md}</pre></body></html>"""
ENDOFFILE

# ─────────────────────────────────────────────
# src/email_sender.py
# ─────────────────────────────────────────────
cat > src/email_sender.py << 'ENDOFFILE'
"""Email sender for daily match reports."""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional


def send_report_email(subject: str, body_markdown: str, body_html: Optional[str] = None,
                      recipients: Optional[List[str]] = None) -> bool:
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    email_from = os.getenv("EMAIL_FROM", smtp_user)

    if recipients is None:
        recipients_str = os.getenv("EMAIL_TO", "")
        recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]

    if not smtp_user or not smtp_password:
        print("⚠️  SMTP credentials not configured. Skipping email send.")
        return False
    if not recipients:
        print("⚠️  No recipients configured. Skipping email send.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = email_from
        msg["To"] = ", ".join(recipients)
        msg.attach(MIMEText(body_markdown, "plain", "utf-8"))
        if body_html:
            msg.attach(MIMEText(body_html, "html", "utf-8"))
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_password)
            server.sendmail(email_from, recipients, msg.as_string())
        print(f"✅ Email sent to: {', '.join(recipients)}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP auth failed. For Gmail, use an App Password.")
        return False
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False
ENDOFFILE

# ─────────────────────────────────────────────
# main.py
# ─────────────────────────────────────────────
cat > main.py << 'ENDOFFILE'
#!/usr/bin/env python3
"""AI Venture Relationship Intelligence Agent — Entry Point."""
import argparse
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.data_loader import load_investors, load_founders
from src.matcher import find_top_matches
from src.report_generator import generate_markdown_report, generate_html_report
from src.email_sender import send_report_email


def main():
    parser = argparse.ArgumentParser(description="AI Venture Relationship Intelligence Agent")
    parser.add_argument("--top", type=int, default=10, help="Number of top matches")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--investors", type=str, help="Investors JSON path")
    parser.add_argument("--founders", type=str, help="Founders JSON path")
    parser.add_argument("--match-only", action="store_true", help="Skip email")
    parser.add_argument("--recipients", type=str, help="Comma-separated email recipients")
    args = parser.parse_args()

    report_date = datetime.utcnow().strftime("%Y-%m-%d")
    output_dir = Path(__file__).parent / "reports"
    output_dir.mkdir(exist_ok=True)
    output_path = Path(args.output) if args.output else output_dir / f"{report_date}-daily-digest.md"

    print("📊 Loading data...")
    investors = load_investors(args.investors)
    founders = load_founders(args.founders)
    print(f"   → {len(investors)} investors, {len(founders)} founders")

    print(f"\n🔍 Finding top {args.top} matches...")
    matches = find_top_matches(founders, investors, top_n=args.top)
    print(f"   → {len(matches)} matches found\n")

    print("=" * 60)
    print("🏆 TOP MATCHES")
    print("=" * 60)
    for i, match in enumerate(matches, 1):
        print(f"  #{i}  Score: {match.total_score:.0f}/100  |  "
              f"{match.founder.company} ↔ {match.investor.firm}")
    print("=" * 60)

    report_md = generate_markdown_report(matches, report_date)
    report_html = generate_html_report(matches, report_date)

    with open(output_path, "w") as f:
        f.write(report_md)
    with open(output_path.with_suffix(".html"), "w") as f:
        f.write(report_html)
    print(f"\n📝 Report saved: {output_path}")

    if not args.match_only:
        print("\n📧 Sending email...")
        recipients = [r.strip() for r in args.recipients.split(",")] if args.recipients else None
        send_report_email(
            subject=f"🤖 AI Venture Intel — {len(matches)} Matches — {report_date}",
            body_markdown=report_md, body_html=report_html, recipients=recipients,
        )

    print(f"\n✅ Done!")
    return matches


if __name__ == "__main__":
    main()
ENDOFFILE

# ─────────────────────────────────────────────
# tests/test_matcher.py
# ─────────────────────────────────────────────
cat > tests/test_matcher.py << 'ENDOFFILE'
"""Tests for the matching engine."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import Investor, Founder, MatchScore
from src.matcher import calculate_match_score, find_top_matches


def create_test_investor():
    return Investor(
        id="T-INV", name="Test Investor", firm="Test VC", type="VC",
        check_size="$1M–$10M", stage_focus=["Seed", "Series A"],
        ai_focus=["AI infrastructure", "developer tools"], geography="US",
        portfolio=["AI Company A", "Dev Tools Co"], decision_speed="Fast (days)",
        communication_style="Technical, direct", response_behavior="High for technical founders",
        thought_leadership="Active on Twitter", warm_intro_paths=["Portfolio founders", "angels"],
        reputation_score=8, last_activity="2026-05",
    )


def create_test_founder():
    return Founder(
        id="T-FOU", name="Test Founder", company="Test AI Co", role="CEO",
        background="Ex-Google AI researcher", stage="Seed ($5M)",
        ai_subsector="AI infrastructure for developers", location="San Francisco, US",
        traction="$5M raised, 10 enterprise pilots", founder_pedigree="Ex-Google, Stanford PhD",
        growth_velocity="High", brand_positioning="Developer-first AI infrastructure platform",
        social_proof="TechCrunch coverage", communication_style="Technical, developer-focused",
        ideal_investor_profile="AI infrastructure VCs", warm_intro_needs="Developer tools investors",
    )


if __name__ == "__main__":
    scores = calculate_match_score(create_test_founder(), create_test_investor())
    print(f"Score: {scores.total:.0f}/100")
    assert 0 < scores.total <= 100
    matches = find_top_matches([create_test_founder()], [create_test_investor()], 5)
    assert len(matches) > 0
    print(f"✅ All tests passed! ({len(matches)} matches)")
ENDOFFILE

# ─────────────────────────────────────────────
# GitHub Actions workflow
# ─────────────────────────────────────────────
cat > .github/workflows/daily-report.yml << 'ENDOFFILE'
name: Daily AI Venture Intel Report
on:
  schedule:
    - cron: '0 9 * * *'
  workflow_dispatch:
    inputs:
      top_matches:
        description: 'Number of top matches'
        default: '10'
        type: string

jobs:
  generate-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - name: Run matching engine
        env:
          SMTP_HOST: ${{ secrets.SMTP_HOST }}
          SMTP_PORT: ${{ secrets.SMTP_PORT }}
          SMTP_USER: ${{ secrets.SMTP_USER }}
          SMTP_PASSWORD: ${{ secrets.SMTP_PASSWORD }}
          EMAIL_FROM: ${{ secrets.EMAIL_FROM }}
          EMAIL_TO: ${{ secrets.EMAIL_TO }}
        run: python main.py --top ${{ inputs.top_matches || '10' }} --output reports/$(date +%Y-%m-%d)-daily-digest.md
      - uses: actions/upload-artifact@v4
        with:
          name: daily-report-${{ github.run_number }}
          path: reports/*-daily-digest.*
          retention-days: 90
      - name: Commit report
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add reports/
          git diff --staged --quiet || git commit -m "📊 Daily report $(date +%Y-%m-%d)"
          git push
ENDOFFILE

# ─────────────────────────────────────────────
# README.md
# ─────────────────────────────────────────────
cat > README.md << 'ENDOFFILE'
# 🤖 AI Venture Relationship Intelligence Agent

Identify the highest probability investor-founder matches based on credibility,
investment behavior, relationship compatibility, startup traction, and communication patterns.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run matching (no email)
python main.py --match-only

# Run with email
cp .env.example .env
# Edit .env with your SMTP credentials
python main.py
```

## Project Structure

```
venture-intel/
├── main.py                      # Entry point
├── requirements.txt             # Dependencies
├── .env.example                 # Config template
├── src/
│   ├── models.py                # Data models
│   ├── matcher.py               # 14-dimension scoring engine
│   ├── report_generator.py      # Report generation
│   ├── email_sender.py          # SMTP delivery
│   └── data_loader.py           # JSON data loading
├── data/
│   ├── investors.json           # 15 AI investor profiles
│   └── founders.json            # 20 AI founder profiles
├── reports/                     # Generated reports
├── tests/
│   └── test_matcher.py          # Tests
└── .github/workflows/
    └── daily-report.yml         # Daily automation
```

## Scoring (14 Dimensions)

| Dimension | Weight |
|-----------|--------|
| Industry Alignment | 15% |
| Stage Compatibility | 12% |
| Founder Track Record | 12% |
| Startup Traction | 10% |
| Growth Velocity | 8% |
| Brand Positioning | 5% |
| Communication Style | 5% |
| Social Proof | 5% |
| Investor Response | 5% |
| Portfolio Similarity | 5% |
| Reputation | 5% |
| Relationship Proximity | 5% |
| Geography | 5% |
| Conversion Likelihood | 3% |

## GitHub Actions (Daily Automation)

1. Push to GitHub
2. Go to **Settings → Secrets → Actions**
3. Add: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, `EMAIL_TO`
4. Go to **Actions → Daily AI Venture Intel Report → Enable**

## License

MIT
ENDOFFILE

# ─────────────────────────────────────────────
# data/investors.json
# ─────────────────────────────────────────────
cat > data/investors.json << 'ENDOFFILE'
[
  {"id":"INV-001","name":"Sarah Guo","firm":"Conviction","type":"Solo GP / AI-Native Fund","check_size":"$500K–$3M","stage_focus":["Seed","Series A"],"ai_focus":["AI infrastructure","AI-native applications","developer tools","transformative AI platforms"],"geography":"US (Bay Area)","portfolio":["Stealth AI infrastructure cos","frontier application startups"],"decision_speed":"Fast (days to weeks)","communication_style":"Technical, direct, thesis-driven","response_behavior":"High for technical founders with strong demos","thought_leadership":"Highly active on LinkedIn/Twitter, respected solo GP voice in AI","warm_intro_paths":["Portfolio founders","AI researcher network","Twitter/X DMs"],"reputation_score":9,"last_activity":"2026-05 — Active seed investments in AI infra"},
  {"id":"INV-002","name":"General Catalyst Team","firm":"General Catalyst","type":"Multi-Stage VC","check_size":"$3M–$25M","stage_focus":["Seed","Series A","Series B"],"ai_focus":["Healthcare AI","fintech AI","enterprise AI agents","infrastructure"],"geography":"US (Global offices)","portfolio":["Hippocratic AI","DataRobot","Shield AI","Concourse"],"decision_speed":"Moderate (weeks to months)","communication_style":"Partnership-oriented, long-term vision, operational support focus","response_behavior":"High for regulated-industry AI with clear category creation potential","thought_leadership":"Active conference presence, healthcare AI thought leadership","warm_intro_paths":["Startup success team","portfolio CEO introductions","academic advisors"],"reputation_score":9,"last_activity":"2026-05 — Co-led Hippocratic AI Series C"},
  {"id":"INV-003","name":"NFX Team","firm":"NFX","type":"Seed-Stage VC","check_size":"$500K–$5M","stage_focus":["Pre-Seed","Seed"],"ai_focus":["AI platforms with network effects","vertical SaaS + AI","marketplace AI","infrastructure"],"geography":"US (Bay Area, Israel)","portfolio":["500+ AI seed investments via Signal platform","F2 (financial AI)"],"decision_speed":"Fast (weeks)","communication_style":"Network-effects thesis, data-driven, platform-oriented","response_behavior":"High for AI products with viral/growth mechanics","thought_leadership":"Signal platform, active blog/podcast on network effects","warm_intro_paths":["Signal platform","portfolio founders","YC network"],"reputation_score":8,"last_activity":"2026-05 — Co-led CopilotKit $27M round"},
  {"id":"INV-004","name":"Lightspeed Venture Partners","firm":"Lightspeed Venture Partners","type":"Multi-Stage VC","check_size":"$2M–$30M","stage_focus":["Seed","Series A","Series B","Series C"],"ai_focus":["Foundation models","AI infrastructure","vertical AI applications","developer tools"],"geography":"US (Global)","portfolio":["Anthropic (early)","Unconventional AI","Mistral AI","Peec AI"],"decision_speed":"Moderate (deep technical diligence)","communication_style":"Technical depth, competitive analysis focus, hands-on partnership","response_behavior":"High for complex AI systems with clear differentiation","thought_leadership":"Active in AI infrastructure discourse","warm_intro_paths":["Sector-specific partners","portfolio CTOs","technical advisors"],"reputation_score":9,"last_activity":"2026-05 — Co-led Unconventional AI $475M seed"},
  {"id":"INV-005","name":"Accel","firm":"Accel","type":"Multi-Stage VC","check_size":"$1M–$50M","stage_focus":["Seed","Series A","Series B"],"ai_focus":["Developer tools","AI infrastructure","enterprise AI","PLG companies"],"geography":"US (Global)","portfolio":["Cursor ($2.3B Series D co-lead)","multiple AI infra startups"],"decision_speed":"Moderate","communication_style":"Enterprise-focused, PLG-oriented, global expansion support","response_behavior":"High for developer-facing AI products with traction","thought_leadership":"Developer tools and PLG expertise","warm_intro_paths":["Portfolio founders","developer community connections","partner network"],"reputation_score":9,"last_activity":"2026-05 — Co-led Cursor $29.3B valuation"},
  {"id":"INV-006","name":"Benchmark","firm":"Benchmark","type":"Seed/Early VC","check_size":"$500K–$3M","stage_focus":["Seed"],"ai_focus":["Consumer AI","enterprise software + AI","marketplace AI","developer tools"],"geography":"US (Bay Area)","portfolio":["Leya ($10.5M seed)","consumer and enterprise AI startups"],"decision_speed":"Moderate (deep engagement per investment)","communication_style":"Board-level involvement, equal partnership model, concentrated portfolio","response_behavior":"High for founders wanting deep investor engagement","thought_leadership":"Quiet but influential, known for concentrated bets","warm_intro_paths":["Portfolio founders","partner direct outreach","Silicon Valley network"],"reputation_score":9,"last_activity":"2026-05 — Active seed investments"},
  {"id":"INV-007","name":"Kleiner Perkins","firm":"Kleiner Perkins","type":"Multi-Stage VC","check_size":"$2M–$20M","stage_focus":["Seed","Series A","Series B"],"ai_focus":["Healthcare AI","sustainability AI","consumer AI","regulated industry AI"],"geography":"US (Bay Area)","portfolio":["Desktop Metal","Livongo","Nest","multiple healthcare AI cos"],"decision_speed":"Slow (up to 6 months, thorough technical DD)","communication_style":"Impact-oriented, societal benefit focus, technical depth","response_behavior":"High for founders who articulate societal impact + commercial upside","thought_leadership":"Healthcare and climate AI thought leadership","warm_intro_paths":["Academic advisors","technical advisors","portfolio founders"],"reputation_score":8,"last_activity":"2026-05 — Active in healthcare and sustainability AI"},
  {"id":"INV-008","name":"First Round Capital","firm":"First Round Capital","type":"Seed VC","check_size":"$500K–$2M","stage_focus":["Pre-Seed","Seed"],"ai_focus":["Developer tools","AI infrastructure","vertical enterprise AI","prosumer AI"],"geography":"US (Bay Area, NYC)","portfolio":["Multiple AI-native startups across developer tools"],"decision_speed":"Fast (founder-friendly terms)","communication_style":"Operational support, hands-on guidance, community-driven","response_behavior":"High for first-time founders with strong technical backgrounds","thought_leadership":"First Round Review, founder education content","warm_intro_paths":["First Round community","portfolio founders","angel network"],"reputation_score":8,"last_activity":"2026-05 — Active seed investments"},
  {"id":"INV-009","name":"Menlo Ventures","firm":"Menlo Ventures","type":"Multi-Stage VC","check_size":"$5M–$50M","stage_focus":["Series A","Series B","Series C"],"ai_focus":["AI creators","enterprise applications","AI infrastructure"],"geography":"US (Bay Area)","portfolio":["Suno ($250M Series C co-lead)","multiple enterprise AI cos"],"decision_speed":"Moderate","communication_style":"Enterprise-focused, scaling expertise, operational partnership","response_behavior":"High for AI products with clear enterprise adoption signals","thought_leadership":"Active in AI creator tools and enterprise AI","warm_intro_paths":["Portfolio CEOs","partner network","industry conferences"],"reputation_score":8,"last_activity":"2026-05 — Co-led Suno Series C"},
  {"id":"INV-010","name":"Felicis Ventures","firm":"Felicis Ventures","type":"Multi-Stage VC","check_size":"$2M–$30M","stage_focus":["Seed","Series A","Series B"],"ai_focus":["Biotech AI","scientific AI","AI infrastructure","frontier technology"],"geography":"US (Bay Area)","portfolio":["Periodic Labs ($300M seed)","biotech and scientific AI startups"],"decision_speed":"Fast for frontier tech","communication_style":"Science-first, technical depth, frontier technology orientation","response_behavior":"High for deep-tech AI with scientific applications","thought_leadership":"Biotech AI and scientific computing","warm_intro_paths":["Scientific advisory network","portfolio founders","academic connections"],"reputation_score":8,"last_activity":"2026-05 — Backed Periodic Labs $300M seed"},
  {"id":"INV-011","name":"Reid Hoffman","firm":"Angel / Greylock","type":"Angel Investor","check_size":"$25K–$500K","stage_focus":["Pre-Seed","Seed"],"ai_focus":["AI that amplifies human potential","professional networking AI","workplace productivity AI"],"geography":"US (Bay Area)","portfolio":["OpenAI","Inflection AI","DeepMind","40+ AI startups since 2020"],"decision_speed":"Fast (days)","communication_style":"Network effects vision, human amplification thesis, LinkedIn-native","response_behavior":"High for AI with clear network effects","thought_leadership":"Extremely active on LinkedIn, podcast host","warm_intro_paths":["LinkedIn connections","mutual Greylock contacts","portfolio founders"],"reputation_score":10,"last_activity":"2026-05 — Active angel in AI"},
  {"id":"INV-012","name":"Elad Gil","firm":"Angel / Ex-Google, Twitter","type":"Angel Investor","check_size":"$100K–$2M","stage_focus":["Seed","Series A"],"ai_focus":["AI infrastructure","developer tools","enterprise AI","scaling-stage AI"],"geography":"US (Bay Area)","portfolio":["Airbnb","Stripe","Notion","multiple AI infrastructure cos"],"decision_speed":"Very fast (days)","communication_style":"Technical depth, scaling expertise, concise and direct","response_behavior":"High for technical founders with clear scaling paths","thought_leadership":"Blog on scaling, active Twitter presence","warm_intro_paths":["Direct Twitter/X DMs","portfolio founder introductions","technical advisor network"],"reputation_score":10,"last_activity":"2026-05 — Active in AI infrastructure"},
  {"id":"INV-013","name":"Y Combinator","firm":"Y Combinator","type":"Accelerator / Seed","check_size":"$500K standard","stage_focus":["Pre-Seed","Seed"],"ai_focus":["AI agents","developer tools","vertical enterprise AI","consumer AI"],"geography":"US (Bay Area) + Global","portfolio":["Scale AI","1,397+ AI companies","~40% of W24 batch was AI"],"decision_speed":"Batch cycles (biannual) + fast follow-on","communication_style":"Demo-driven, traction-focused, batch community model","response_behavior":"High during batch applications, strong for AI startups","thought_leadership":"YC blog, Demo Day coverage","warm_intro_paths":["YC application","alumni network","Demo Day exposure"],"reputation_score":10,"last_activity":"2026-05 — 40%+ AI batch"},
  {"id":"INV-014","name":"Sequoia Capital","firm":"Sequoia Capital","type":"Multi-Stage VC","check_size":"$1M–$100M","stage_focus":["Seed","Series A","Series B","Series C","Series D"],"ai_focus":["Foundation models","vertical AI applications","developer tools","AI-native infrastructure"],"geography":"US (Global)","portfolio":["OpenAI","Hugging Face","Harvey","Character.ai","Vanta"],"decision_speed":"Moderate (thorough due diligence)","communication_style":"Long-term vision, patient capital, deep competitive analysis","response_behavior":"High for technical founders with ambitious multi-year visions","thought_leadership":"AI-first company thesis","warm_intro_paths":["Partner-level introductions","portfolio CEO connections","alumni network"],"reputation_score":10,"last_activity":"2026-05 — Portfolio raised $30B+ collectively"},
  {"id":"INV-015","name":"Andreessen Horowitz (a16z)","firm":"Andreessen Horowitz","type":"Multi-Stage Mega-Fund","check_size":"$500K–$50M","stage_focus":["Seed","Series A","Series B","Series C"],"ai_focus":["Foundation models","vertical AI copilots","AI infrastructure","agent platforms"],"geography":"US (Bay Area, NYC, Miami)","portfolio":["OpenAI","Databricks","Mistral AI","Glean","Harvey","Hippocratic AI"],"decision_speed":"Fast when conviction is high (weeks)","communication_style":"Technical moat emphasis, massive market vision, operational support","response_behavior":"High for category-defining AI with experienced teams","thought_leadership":"Marc Andreessen AI thesis, extensive blog/media presence","warm_intro_paths":["Portfolio CEOs","operating partners","technical advisors","warm referral preferred"],"reputation_score":10,"last_activity":"2026-05 — 50+ AI deals in 2025, AUM $90B+"}
]
ENDOFFILE

# ─────────────────────────────────────────────
# data/founders.json
# ─────────────────────────────────────────────
cat > data/founders.json << 'ENDOFFILE'
[
  {"id":"FOU-001","name":"Yu Su","company":"NeoCognition","role":"Co-Founder & CEO","background":"Ohio State professor, AI researcher","stage":"Seed ($40M)","ai_subsector":"Self-learning AI agents for enterprise","location":"US","traction":"$40M seed from Cambium Capital, Walden Catalyst, Vista, Intel CEO Lip-Bu Tan, Databricks","founder_pedigree":"Academic researcher with deep AI expertise, backed by top-tier strategic investors","growth_velocity":"High","brand_positioning":"Enterprise AI agents that learn through experience","social_proof":"Intel CEO and Databricks as investors","communication_style":"Technical, research-oriented, enterprise-focused","ideal_investor_profile":"AI infrastructure VCs with enterprise networks","warm_intro_needs":"Enterprise AI investors, strategic corporate VCs"},
  {"id":"FOU-002","name":"Founders (ex-Parallel team)","company":"Parallel","role":"CEO (ex-Twitter CEO)","background":"Former Twitter CEO, deep tech leadership","stage":"Series A ($230M total, $2B valuation)","ai_subsector":"Web-search infrastructure for AI agents","location":"US","traction":"$230M raised, $2B valuation","founder_pedigree":"Ex-Twitter CEO — top-tier tech leadership","growth_velocity":"Very high","brand_positioning":"Agent infrastructure layer — web retrieval for AI agents","social_proof":"WSJ coverage, massive valuation","communication_style":"Visionary, infrastructure-oriented, platform thinking","ideal_investor_profile":"Mega-funds with AI infrastructure thesis","warm_intro_needs":"AI infrastructure specialists, platform VCs"},
  {"id":"FOU-003","name":"Founders (Amazon & Apple vets)","company":"SageOx","role":"Co-Founders","background":"Early Amazon engineer, serial founders, Apple veterans","stage":"Seed ($15M)","ai_subsector":"AI hivemind for human-AI team alignment","location":"Seattle, US","traction":"$15M raised, building AI coordination layer","founder_pedigree":"Amazon and Apple engineering veterans, serial entrepreneurs","growth_velocity":"High","brand_positioning":"Human-AI team coordination, not replacing developers","social_proof":"GeekWire coverage, Amazon/Apple pedigree","communication_style":"Engineering-first, practical, enterprise developer focus","ideal_investor_profile":"Developer tools VCs, AI infrastructure investors","warm_intro_needs":"Developer tools specialists, enterprise AI investors"},
  {"id":"FOU-004","name":"Founders","company":"CopilotKit","role":"CEO","background":"AI agent protocol developers","stage":"Series A ($27M)","ai_subsector":"AI agent protocol — open-source framework","location":"Seattle, US","traction":"$27M raised, adopted by biggest names in tech","founder_pedigree":"Technical founders with open-source community building","growth_velocity":"Very high","brand_positioning":"Open-source AI agent infrastructure, protocol layer","social_proof":"Led by Glilot Capital, NFX, SignalFire","communication_style":"Developer-first, open-source community, protocol-oriented","ideal_investor_profile":"AI infrastructure VCs with developer ecosystem expertise","warm_intro_needs":"NFX network, developer tools investors"},
  {"id":"FOU-005","name":"Founders","company":"Scout AI","role":"CEO","background":"Defense technology, autonomous systems","stage":"Series A ($100M)","ai_subsector":"Defense AI — autonomous fleet operating software","location":"US","traction":"$100M Series A, defense contracts, field deployment","founder_pedigree":"Defense technology expertise","growth_velocity":"Very high","brand_positioning":"Mission software for uncrewed fleets, defense-grade AI","social_proof":"Aviation Week coverage, defense procurement validation","communication_style":"Mission-focused, defense-industry appropriate","ideal_investor_profile":"Defense-tech VCs, dual-use technology investors","warm_intro_needs":"Defense-tech specialists"},
  {"id":"FOU-006","name":"Founders","company":"Performativ","role":"CEO","background":"Fintech, wealth management","stage":"Seed (€5.5M)","ai_subsector":"AI-native operating system for wealth management","location":"Europe","traction":"€5.5M raised, regulated fintech AI platform","founder_pedigree":"Fintech and wealth management domain expertise","growth_velocity":"Moderate","brand_positioning":"Regulated AI for wealth management, compliance-first","social_proof":"FinTech Futures coverage","communication_style":"Regulation-aware, compliance-oriented","ideal_investor_profile":"Fintech AI VCs, regulated industry specialists","warm_intro_needs":"Fintech AI investors"},
  {"id":"FOU-007","name":"Founders","company":"Marloo","role":"CEO","background":"Financial advisory, fintech","stage":"Seed ($10M)","ai_subsector":"AI workflows for financial advisers","location":"US","traction":"$10M seed raised, adviser workflow automation","founder_pedigree":"Financial advisory and fintech background","growth_velocity":"Moderate","brand_positioning":"Vertical AI for financial advisers","social_proof":"FinTech Futures coverage","communication_style":"Customer-centric, workflow-oriented","ideal_investor_profile":"Fintech VCs, vertical AI specialists","warm_intro_needs":"Fintech AI investors"},
  {"id":"FOU-008","name":"Founders","company":"RadixArk","role":"CEO","background":"AI infrastructure, compute optimization","stage":"Seed ($100M)","ai_subsector":"SGLang software — reduces computing costs for AI models","location":"Palo Alto, US","traction":"$100M seed led by Accel, 50 employees","founder_pedigree":"AI infrastructure expertise","growth_velocity":"Very high","brand_positioning":"AI compute cost reduction, infrastructure optimization","social_proof":"SVBJ coverage, Accel-led seed","communication_style":"Technical, infrastructure-oriented","ideal_investor_profile":"AI infrastructure VCs, compute specialists","warm_intro_needs":"Accel network, AI infrastructure specialists"},
  {"id":"FOU-009","name":"Founders","company":"Krane","role":"CEO","background":"Construction tech, supply chain","stage":"Seed ($9M)","ai_subsector":"AI agents for construction supply chains (data centers)","location":"US","traction":"$9M raised, targeting data center construction","founder_pedigree":"Construction tech and supply chain expertise","growth_velocity":"Moderate","brand_positioning":"Vertical AI agents for construction","social_proof":"Business Insider coverage","communication_style":"Industry-specific, problem-focused","ideal_investor_profile":"ConTech VCs, vertical AI specialists","warm_intro_needs":"Construction tech investors"},
  {"id":"FOU-010","name":"Mati Staniszewski & Piotr Dabkowski","company":"Elastics","role":"Co-Founders","background":"AI/audio tech, prediction markets","stage":"Pre-Seed (€1.7M)","ai_subsector":"AI agents for prediction markets","location":"Warsaw, Europe","traction":"€1.7M oversubscribed, backed by ElevenLabs co-founders","founder_pedigree":"Backed by ElevenLabs founders as angels","growth_velocity":"High","brand_positioning":"AI agents for quantitative prediction markets","social_proof":"EU-Startups coverage, ElevenLabs founder angels","communication_style":"Technical, quantitative","ideal_investor_profile":"European AI VCs, quantitative/fintech AI investors","warm_intro_needs":"European AI specialists, ElevenLabs network"},
  {"id":"FOU-011","name":"Founders","company":"Counsel Health","role":"CEO","background":"Healthcare AI, clinical decision support","stage":"Series A","ai_subsector":"AI-powered clinical decision support","location":"Canton, MA, US","traction":"Series A raised, healthcare AI platform live","founder_pedigree":"Healthcare and clinical expertise","growth_velocity":"Moderate","brand_positioning":"Clinical AI decision support","social_proof":"Healthcare AI ecosystem recognition","communication_style":"Clinical, evidence-based","ideal_investor_profile":"Healthcare AI VCs","warm_intro_needs":"Healthcare AI investors"},
  {"id":"FOU-012","name":"Founders","company":"Metaforms","role":"CEO","background":"AI form builders, enterprise workflow","stage":"Series A","ai_subsector":"AI-powered form and workflow automation","location":"San Francisco, US","traction":"Series A raised, enterprise adoption","founder_pedigree":"Product and enterprise workflow expertise","growth_velocity":"Moderate","brand_positioning":"AI-native form building and workflow automation","social_proof":"Enterprise customer traction","communication_style":"Product-oriented, enterprise workflow","ideal_investor_profile":"Enterprise SaaS VCs","warm_intro_needs":"Enterprise SaaS investors"},
  {"id":"FOU-013","name":"Founders","company":"Caseflood.ai","role":"CEO","background":"Legal tech, AI","stage":"Seed","ai_subsector":"AI for legal case management","location":"San Francisco, US","traction":"Seed raised, legal industry traction","founder_pedigree":"Legal tech expertise","growth_velocity":"Moderate","brand_positioning":"Vertical AI for legal workflows","social_proof":"Legal tech ecosystem recognition","communication_style":"Legal-industry specific","ideal_investor_profile":"Legal tech VCs","warm_intro_needs":"Legal tech investors"},
  {"id":"FOU-014","name":"Founders","company":"Runloop AI","role":"CEO","background":"AI developer tools","stage":"Seed","ai_subsector":"AI-powered developer workflow automation","location":"San Francisco, US","traction":"Seed raised, developer community traction","founder_pedigree":"Developer tools expertise","growth_velocity":"High","brand_positioning":"AI developer tools, workflow automation","social_proof":"Developer community adoption","communication_style":"Developer-first, technical","ideal_investor_profile":"Developer tools VCs","warm_intro_needs":"Developer tools specialists"},
  {"id":"FOU-015","name":"Founders","company":"Julius AI","role":"CEO","background":"AI data analysis","stage":"Seed","ai_subsector":"AI-powered data analysis and visualization","location":"San Francisco, US","traction":"Seed raised, growing user base","founder_pedigree":"Data science and AI expertise","growth_velocity":"High","brand_positioning":"AI data analyst, natural language data exploration","social_proof":"Growing user community","communication_style":"Data-driven, product-demo oriented","ideal_investor_profile":"Data/AI VCs, PLG investors","warm_intro_needs":"Data AI investors"},
  {"id":"FOU-016","name":"Founders","company":"Hyprnote (YC S25)","role":"CEO","background":"AI meeting notes, productivity","stage":"Seed (YC-backed)","ai_subsector":"AI-powered meeting notes and productivity","location":"San Francisco, US","traction":"Seed raised, YC S25 batch","founder_pedigree":"YC-backed, productivity tool expertise","growth_velocity":"High","brand_positioning":"AI meeting intelligence, productivity automation","social_proof":"YC S25 batch","communication_style":"Product-oriented, YC network","ideal_investor_profile":"YC network investors, productivity VCs","warm_intro_needs":"YC alumni network"},
  {"id":"FOU-017","name":"Founders","company":"Charta Health","role":"CEO","background":"Healthcare AI, medical coding","stage":"Series A","ai_subsector":"AI-powered medical coding and revenue cycle","location":"San Francisco, US","traction":"Series A raised, healthcare provider traction","founder_pedigree":"Healthcare and medical coding expertise","growth_velocity":"Moderate","brand_positioning":"AI medical coding, healthcare revenue cycle","social_proof":"Healthcare AI ecosystem","communication_style":"Healthcare-specific, ROI-focused","ideal_investor_profile":"Healthcare AI VCs","warm_intro_needs":"Healthcare AI specialists"},
  {"id":"FOU-018","name":"Founders","company":"Cervo AI","role":"CEO","background":"AI agents, enterprise automation","stage":"Seed","ai_subsector":"AI agent platform for enterprise automation","location":"New York, US","traction":"Seed raised, enterprise pilot traction","founder_pedigree":"Enterprise automation expertise","growth_velocity":"Moderate","brand_positioning":"Enterprise AI agents, workflow automation","social_proof":"Enterprise pilot traction","communication_style":"Enterprise-focused, automation ROI","ideal_investor_profile":"Enterprise AI VCs","warm_intro_needs":"Enterprise AI specialists"},
  {"id":"FOU-019","name":"Founders","company":"Volca","role":"CEO","background":"AI sales tools","stage":"Seed","ai_subsector":"AI-powered sales automation","location":"New York, US","traction":"Seed raised, sales team adoption","founder_pedigree":"Sales technology expertise","growth_velocity":"High","brand_positioning":"AI sales intelligence","social_proof":"Sales team traction","communication_style":"Sales-oriented, ROI-focused","ideal_investor_profile":"Sales tech VCs","warm_intro_needs":"Sales tech investors"},
  {"id":"FOU-020","name":"Founders","company":"Questflow","role":"CEO","background":"AI workflow automation","stage":"Seed","ai_subsector":"AI-powered workflow automation and orchestration","location":"Emeryville, CA, US","traction":"Seed raised, workflow automation traction","founder_pedigree":"Workflow automation expertise","growth_velocity":"Moderate","brand_positioning":"AI workflow orchestration, multi-agent automation","social_proof":"Workflow automation ecosystem","communication_style":"Automation-focused, enterprise workflow","ideal_investor_profile":"Enterprise automation VCs","warm_intro_needs":"Enterprise automation specialists"}
]
ENDOFFILE

# ─────────────────────────────────────────────
# Initialize git and test
# ─────────────────────────────────────────────
echo ""
echo "📦 Initializing git..."
git init
git config user.email "venture-intel@local" 2>/dev/null || true
git config user.name "Venture Intel" 2>/dev/null || true
git add -A
git commit -m "🤖 AI Venture Relationship Intelligence Agent v1.0"

echo ""
echo "🧪 Running tests..."
python3 tests/test_matcher.py

echo ""
echo "============================================================"
echo "✅ PROJECT CREATED SUCCESSFULLY!"
echo "============================================================"
echo ""
echo "📁 Location: $PROJECT_DIR"
echo ""
echo "Next steps:"
echo "  1. cd $PROJECT_DIR"
echo "  2. pip install -r requirements.txt"
echo "  3. python main.py --match-only"
echo ""
echo "To push to GitHub:"
echo "  git remote add origin https://github.com/bella30-3/venture-intel.git"
echo "  git branch -M main"
echo "  git push -u origin main"
echo ""
