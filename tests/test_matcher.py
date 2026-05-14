"""Tests for the matching engine."""

import sys
sys.path.insert(0, "..")

from src.models import Investor, Founder, MatchScore
from src.matcher import calculate_match_score, find_top_matches


def create_test_investor():
    return Investor(
        id="TEST-INV-001",
        name="Test Investor",
        firm="Test VC",
        type="VC",
        check_size="$1M–$10M",
        stage_focus=["Seed", "Series A"],
        ai_focus=["AI infrastructure", "developer tools"],
        geography="US",
        portfolio=["AI Company A", "Dev Tools Co"],
        decision_speed="Fast (days)",
        communication_style="Technical, direct",
        response_behavior="High for technical founders",
        thought_leadership="Active on Twitter",
        warm_intro_paths=["Portfolio founders", "angels", "advisors"],
        reputation_score=8,
        last_activity="2026-05",
    )


def create_test_founder():
    return Founder(
        id="TEST-FOU-001",
        name="Test Founder",
        company="Test AI Co",
        role="CEO",
        background="Ex-Google AI researcher",
        stage="Seed ($5M)",
        ai_subsector="AI infrastructure for developers",
        location="San Francisco, US",
        traction="$5M raised, 10 enterprise pilots",
        founder_pedigree="Ex-Google, Stanford PhD",
        growth_velocity="High",
        brand_positioning="Developer-first AI infrastructure platform",
        social_proof="TechCrunch coverage",
        communication_style="Technical, developer-focused",
        ideal_investor_profile="AI infrastructure VCs",
        warm_intro_needs="Developer tools investors",
    )


def test_match_score():
    investor = create_test_investor()
    founder = create_test_founder()

    scores = calculate_match_score(founder, investor)

    print(f"\n📊 Match Score Test:")
    print(f"   Industry Alignment:     {scores.industry_alignment:.0f}")
    print(f"   Stage Compatibility:    {scores.stage_compatibility:.0f}")
    print(f"   Geography:              {scores.geography_preference:.0f}")
    print(f"   Founder Track Record:   {scores.founder_track_record:.0f}")
    print(f"   Traction:               {scores.startup_traction:.0f}")
    print(f"   Growth Velocity:        {scores.growth_velocity:.0f}")
    print(f"   Brand Positioning:      {scores.brand_positioning:.0f}")
    print(f"   Communication Style:    {scores.communication_style:.0f}")
    print(f"   Social Proof:           {scores.social_proof:.0f}")
    print(f"   Investor Response:      {scores.investor_response_behavior:.0f}")
    print(f"   Portfolio Similarity:   {scores.portfolio_similarity:.0f}")
    print(f"   Reputation:             {scores.reputation_score:.0f}")
    print(f"   Relationship Proximity: {scores.relationship_proximity:.0f}")
    print(f"   Conversion Likelihood:  {scores.conversion_likelihood:.0f}")
    print(f"   ─────────────────────────────")
    print(f"   TOTAL SCORE:            {scores.total:.0f}/100")

    assert scores.total > 0, "Score should be positive"
    assert scores.total <= 100, "Score should not exceed 100"
    print("   ✅ All assertions passed!")


def test_find_top_matches():
    investors = [create_test_investor()]
    founders = [create_test_founder()]

    matches = find_top_matches(founders, investors, top_n=5)

    print(f"\n🔍 Top Matches Test:")
    print(f"   Found {len(matches)} matches")

    for i, match in enumerate(matches, 1):
        print(f"   #{i}: {match.founder.company} ↔ {match.investor.firm} "
              f"(Score: {match.total_score:.0f})")

    assert len(matches) > 0, "Should find at least one match"
    print("   ✅ All assertions passed!")


if __name__ == "__main__":
    test_match_score()
    test_find_top_matches()
    print("\n✅ All tests passed!")
