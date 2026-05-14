"""Tests for the matching engine v2."""

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
        background="Ex-Google AI researcher, Stanford PhD in ML",
        stage="Seed ($5M)",
        ai_subsector="AI infrastructure for developers",
        location="San Francisco, US",
        traction="$5M raised, 10 enterprise pilots",
        founder_pedigree="Ex-Google, Stanford PhD, serial entrepreneur",
        growth_velocity="High",
        brand_positioning="Developer-first AI infrastructure platform",
        social_proof="TechCrunch coverage, YC W24",
        communication_style="Technical, developer-focused",
        ideal_investor_profile="AI infrastructure VCs",
        warm_intro_needs="Developer tools investors",
        mission="Democratize AI infrastructure for every developer",
        projected_sales_y1="$2-5M",
        year_incorporated="2024",
        growth_last_12mo="320%",
        technical_depth="Custom inference engine, proprietary model optimization, self-hosted",
        moat="Developer ecosystem lock-in, open-source community, proprietary inference IP",
        team_composition="Ex-Google AI researchers + enterprise GTM lead",
        regulatory_readiness="SOC 2 compliant, enterprise security",
        website="https://example.com",
        linkedin_url="https://linkedin.com/company/testai",
    )


def test_match_score():
    investor = create_test_investor()
    founder = create_test_founder()

    scores = calculate_match_score(founder, investor)

    print(f"\n📊 Match Score v2 Test:")
    print(f"   ── Core Fit ──")
    print(f"   🏭 Industry Fit:        {scores.industry_alignment:.0f}")
    print(f"   📅 Stage Match:         {scores.stage_compatibility:.0f}")
    print(f"   🌍 Geography:           {scores.geography_preference:.0f}")
    print(f"   📊 Portfolio Fit:       {scores.portfolio_similarity:.0f}")
    print(f"   ── Founder Strength ──")
    print(f"   🏆 Founder Pedigree:    {scores.founder_pedigree:.0f}")
    print(f"   👥 Team Balance:        {scores.team_composition:.0f}")
    print(f"   🔬 Tech Depth:          {scores.technical_depth:.0f}")
    print(f"   ── Business Quality ──")
    print(f"   💰 Revenue Traction:    {scores.revenue_traction:.0f}")
    print(f"   📈 Growth Momentum:     {scores.growth_momentum:.0f}")
    print(f"   🛡️  Moat & Defense:     {scores.moat_defensibility:.0f}")
    print(f"   ── Market & Signal ──")
    print(f"   🎯 Market Positioning:  {scores.market_positioning:.0f}")
    print(f"   ⭐ Social Proof:        {scores.social_proof:.0f}")
    print(f"   📋 Regulatory:          {scores.regulatory_readiness:.0f}")
    print(f"   ── Relationship ──")
    print(f"   💬 Comms Fit:           {scores.communication_fit:.0f}")
    print(f"   ⚡ Responsiveness:      {scores.investor_responsiveness:.0f}")
    print(f"   🌟 Reputation:          {scores.investor_reputation:.0f}")
    print(f"   🤝 Intro Access:        {scores.warm_intro_access:.0f}")
    print(f"   🎯 Conversion:          {scores.conversion_likelihood:.0f}")
    print(f"   ─────────────────────────────")
    print(f"   TOTAL SCORE:            {scores.total:.0f}/100")

    assert scores.total > 0, "Score should be positive"
    assert scores.total <= 100, "Score should not exceed 100"
    # With good data, score should be reasonably high
    assert scores.total >= 55, f"Expected score >= 55 for good match, got {scores.total}"
    print("   ✅ All assertions passed!")


def test_new_dimensions():
    """Test that new dimensions (moat, tech depth, team, regulatory) work."""
    investor = create_test_investor()
    founder = create_test_founder()

    scores = calculate_match_score(founder, investor)

    # New dimensions should have meaningful scores
    assert scores.technical_depth > 50, f"Tech depth too low: {scores.technical_depth}"
    assert scores.moat_defensibility > 40, f"Moat too low: {scores.moat_defensibility}"
    assert scores.team_composition > 40, f"Team too low: {scores.team_composition}"
    assert scores.growth_momentum > 50, f"Growth too low: {scores.growth_momentum}"
    assert scores.founder_pedigree > 50, f"Pedigree too low: {scores.founder_pedigree}"

    print(f"\n🔬 New Dimensions Test:")
    print(f"   Tech Depth:      {scores.technical_depth:.0f} (expected >50) ✅")
    print(f"   Moat:            {scores.moat_defensibility:.0f} (expected >40) ✅")
    print(f"   Team:            {scores.team_composition:.0f} (expected >40) ✅")
    print(f"   Growth:          {scores.growth_momentum:.0f} (expected >50) ✅")
    print(f"   Pedigree:        {scores.founder_pedigree:.0f} (expected >50) ✅")
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
    test_new_dimensions()
    test_find_top_matches()
    print("\n✅ All tests passed!")
