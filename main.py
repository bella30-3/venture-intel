#!/usr/bin/env python3
"""
AI Venture Relationship Intelligence Agent
============================================

Identifies highest probability investor-founder matches based on credibility,
investment behavior, relationship compatibility, startup traction, founder
experience, and communication patterns.

Usage:
    python main.py                    # Run full pipeline (match + report + email)
    python main.py --match-only       # Only run matching (no email)
    python main.py --top N            # Show top N matches (default: 10)
    python main.py --output FILE      # Save report to file
    python main.py --investors FILE   # Custom investors JSON path
    python main.py --founders FILE    # Custom founders JSON path
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use system env vars

from src.data_loader import load_investors, load_founders
from src.matcher import find_top_matches
from src.report_generator import generate_markdown_report, generate_html_report
from src.email_sender import send_report_email


def main():
    parser = argparse.ArgumentParser(
        description="AI Venture Relationship Intelligence Agent"
    )
    parser.add_argument("--top", type=int, default=10, help="Number of top matches")
    parser.add_argument("--output", type=str, help="Output file path")
    parser.add_argument("--investors", type=str, help="Investors JSON path")
    parser.add_argument("--founders", type=str, help="Founders JSON path")
    parser.add_argument("--match-only", action="store_true", help="Skip email")
    parser.add_argument("--email-only", action="store_true", help="Skip matching, use existing report")
    parser.add_argument("--report", type=str, help="Report file for --email-only mode")
    parser.add_argument("--recipients", type=str, help="Comma-separated email recipients")

    args = parser.parse_args()

    report_date = datetime.utcnow().strftime("%Y-%m-%d")
    output_dir = Path(__file__).parent / "reports"
    output_dir.mkdir(exist_ok=True)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = output_dir / f"{report_date}-daily-digest.md"

    # Load data
    print("📊 Loading investor and founder data...")
    investors = load_investors(args.investors)
    founders = load_founders(args.founders)
    print(f"   → {len(investors)} investors, {len(founders)} founders loaded")

    # Run matching
    print(f"\n🔍 Finding top {args.top} matches...")
    matches = find_top_matches(founders, investors, top_n=args.top)
    print(f"   → {len(matches)} high-quality matches found")

    # Display summary
    print("\n" + "=" * 60)
    print("🏆 TOP MATCHES SUMMARY")
    print("=" * 60)
    for i, match in enumerate(matches, 1):
        print(f"  #{i}  Score: {match.total_score:.0f}/100  |  "
              f"{match.founder.company} ↔ {match.investor.firm}")
    print("=" * 60)

    # Generate report
    print(f"\n📝 Generating report...")
    report_md = generate_markdown_report(matches, report_date)
    report_html = generate_html_report(matches, report_date)

    # Save report
    with open(output_path, "w") as f:
        f.write(report_md)
    print(f"   → Report saved to: {output_path}")

    # Also save HTML version
    html_path = output_path.with_suffix(".html")
    with open(html_path, "w") as f:
        f.write(report_html)
    print(f"   → HTML saved to: {html_path}")

    # Send email
    if not args.match_only:
        print("\n📧 Sending email report...")
        recipients = None
        if args.recipients:
            recipients = [r.strip() for r in args.recipients.split(",")]

        subject = f"🤖 AI Venture Intel — {len(matches)} Matches — {report_date}"
        send_report_email(
            subject=subject,
            body_markdown=report_md,
            body_html=report_html,
            recipients=recipients,
        )

    print(f"\n✅ Done! Report: {output_path}")
    return matches


if __name__ == "__main__":
    main()
