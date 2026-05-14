"""Generates daily match reports in Markdown and HTML formats."""

from datetime import datetime
from typing import List
from .models import Match


def _score_bar(score: float) -> str:
    """Generate a visual score bar."""
    filled = int(score / 10)
    return "█" * filled + "░" * (10 - filled)


def _generate_email_draft(match: Match, rank: int) -> str:
    """Generate a personalized introduction email draft."""
    f = match.founder
    i = match.investor

    return f"""Subject: {f.company} — {f.brand_positioning[:60]} × {i.firm}'s {i.focus_areas_display} Thesis

Hi {i.firm} Team,

I'm reaching out because I see a strong alignment between what you're building at {i.firm} and what {f.name} and the {f.company} team are creating.

{f.company} ({f.stage}) is building {f.ai_subsector}. What differentiates them:
- {f.brand_positioning}
- {f.traction[:150]}
- Founder background: {f.founder_pedigree[:150]}

Given {i.firm}'s focus on {i.focus_areas_display} and your portfolio ({', '.join(i.portfolio[:3])}), this represents a compelling fit:
- Industry alignment: {f.ai_subsector} matches your investment thesis
- Stage fit: {f.stage} aligns with your {', '.join(i.stage_focus)} focus
- Traction signal: {f.social_proof[:100]}

Would you be open to a conversation with {f.name}? Happy to arrange at your convenience.

Best,
[Your Name]"""


def generate_markdown_report(matches: List[Match], report_date: str = None) -> str:
    """Generate a full Markdown report."""
    if report_date is None:
        report_date = datetime.utcnow().strftime("%Y-%m-%d")

    lines = []
    lines.append("# 🤖 AI Venture Relationship Intelligence Report")
    lines.append(f"## Daily Match Digest — {report_date}")
    lines.append("")
    lines.append("**Focus:** AI Founders ↔ AI Investors")
    lines.append("**Data Sources:** Public funding announcements, investor portfolios, press releases, social signals")
    lines.append(f"**Matches Found:** {len(matches)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Executive Summary
    lines.append("## 📊 Executive Summary")
    lines.append("")
    lines.append(f"- **{len(matches)} high-quality matches** identified today")
    avg_score = sum(m.total_score for m in matches) / len(matches) if matches else 0
    lines.append(f"- **Average compatibility score:** {avg_score:.1f}/100")
    top_sectors = set()
    for m in matches:
        top_sectors.add(m.founder.ai_subsector.split()[0] if m.founder.ai_subsector else "AI")
    lines.append(f"- **Top sectors:** {', '.join(list(top_sectors)[:5])}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Individual Matches
    lines.append("## 🏆 TOP MATCHES")
    lines.append("")

    for rank, match in enumerate(matches, 1):
        f = match.founder
        i = match.investor

        lines.append(f"### MATCH #{rank} — Score: {match.total_score:.0f}/100")
        lines.append("")
        lines.append(f"**Founder:** {f.name} ({f.company})")
        lines.append(f"**Investor:** {i.name} ({i.firm})")
        lines.append(f"**Stage:** {f.stage} | **Focus:** {f.ai_subsector}")
        lines.append("")

        # Score breakdown
        lines.append("| Dimension | Score | |")
        lines.append("|-----------|-------|---|")
        score = match.score
        dimensions = [
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
        ]
        for dim_name, dim_score in dimensions:
            lines.append(f"| {dim_name} | {dim_score:.0f} | {_score_bar(dim_score)} |")
        lines.append("")

        # Rationale
        lines.append(f"**Why This Match Is Strong:**")
        lines.append(f"- {i.firm}'s focus on {i.focus_areas_display} aligns with {f.company}'s {f.ai_subsector}")
        lines.append(f"- {f.founder_pedigree[:200]}")
        lines.append(f"- Investor response behavior: {i.response_behavior}")
        lines.append("")

        # Concerns
        lines.append(f"**Potential Concerns:**")
        lines.append(f"- {i.firm} typical check size ({i.check_size}) vs. {f.stage}")
        lines.append(f"- {i.decision_speed} decision timeline")
        lines.append("")

        # Predictions
        lines.append(f"**Meeting Acceptance Likelihood:** {match.meeting_acceptance_likelihood:.0f}%")
        lines.append(f"**Investment Probability:** {match.investment_probability:.0f}%")
        lines.append("")

        # Communication
        lines.append(f"**Ideal Communication Style:** {match.ideal_communication_style}")
        lines.append(f"**Best Timing:** {match.best_timing}")
        lines.append("")

        # Warm intro paths
        lines.append(f"**Warm Introduction Pathways:**")
        for path in match.warm_intro_pathways:
            lines.append(f"- {path}")
        lines.append("")

        # Email draft
        lines.append("### 📧 Draft Introduction Email")
        lines.append("")
        lines.append("```")
        lines.append(_generate_email_draft(match, rank))
        lines.append("```")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Market signals
    lines.append("## 📈 MARKET SIGNALS TO WATCH")
    lines.append("")
    lines.append("| Signal | Action |")
    lines.append("|--------|--------|")
    lines.append("| Agent infrastructure consolidation | Invest in agent-layer companies now |")
    lines.append("| Defense AI moving to procurement | Defense-tech VCs will be more active |")
    lines.append("| Healthcare AI regulation clarity | Healthcare AI timing is optimal |")
    lines.append("| AI compute cost pressure | Infrastructure optimization is premium |")
    lines.append("| European AI ecosystem maturation | Watch for EU→US expansion plays |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*Generated by AI Venture Relationship Intelligence Agent v1.0*")
    lines.append(f"*{report_date}*")

    return "\n".join(lines)


def generate_html_report(matches: List[Match], report_date: str = None) -> str:
    """Generate an HTML email-friendly report."""
    if report_date is None:
        report_date = datetime.utcnow().strftime("%Y-%m-%d")

    md = generate_markdown_report(matches, report_date)

    # Simple conversion for email
    html = md.replace("\n", "<br>")
    html = html.replace("# ", "<h1>").replace("## ", "<h2>").replace("### ", "<h3>")

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>AI Venture Intel - {report_date}</title></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; color: #333;">
<pre style="white-space: pre-wrap; font-family: inherit;">{md}</pre>
</body>
</html>"""
