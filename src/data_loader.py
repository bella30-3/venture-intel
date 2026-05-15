"""Load investor and founder data from JSON files."""

import json
from pathlib import Path
from typing import List
from .models import Investor, Founder


DATA_DIR = Path(__file__).parent.parent / "data"


def load_investors(filepath: str = None) -> List[Investor]:
    """Load investors from JSON file."""
    path = Path(filepath) if filepath else DATA_DIR / "investors.json"
    with open(path, "r") as f:
        data = json.load(f)

    investors = []
    for item in data:
        investors.append(Investor(
            id=item["id"],
            name=item["name"],
            firm=item["firm"],
            type=item["type"],
            check_size=item["check_size"],
            stage_focus=item["stage_focus"],
            ai_focus=item["ai_focus"],
            geography=item["geography"],
            portfolio=item["portfolio"],
            decision_speed=item["decision_speed"],
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
    """Load founders from JSON file."""
    path = Path(filepath) if filepath else DATA_DIR / "founders.json"
    with open(path, "r") as f:
        data = json.load(f)

    founders = []
    for item in data:
        founders.append(Founder(
            id=item["id"],
            name=item["name"],
            company=item["company"],
            role=item["role"],
            background=item["background"],
            stage=item["stage"],
            ai_subsector=item["ai_subsector"],
            location=item["location"],
            traction=item["traction"],
            founder_pedigree=item["founder_pedigree"],
            growth_velocity=item["growth_velocity"],
            brand_positioning=item["brand_positioning"],
            social_proof=item["social_proof"],
            communication_style=item["communication_style"],
            ideal_investor_profile=item["ideal_investor_profile"],
            warm_intro_needs=item["warm_intro_needs"],
            mission=item.get("mission", ""),
            projected_sales_y1=item.get("projected_sales_y1", ""),
            year_incorporated=item.get("year_incorporated", ""),
            growth_last_12mo=item.get("growth_last_12mo", ""),
            technical_depth=item.get("technical_depth", ""),
            moat=item.get("moat", ""),
            team_composition=item.get("team_composition", ""),
            regulatory_readiness=item.get("regulatory_readiness", ""),
            needs_capital=item.get("needs_capital", True),
            capital_stage=item.get("capital_stage", "actively_raising"),
            capital_notes=item.get("capital_notes", ""),
            linkedin_url=item.get("linkedin_url"),
            twitter_url=item.get("twitter_url"),
            website=item.get("website"),
            email=item.get("email"),
        ))
    return founders
