#!/usr/bin/env python3
"""Regenerate the static HTML canvas document from current data."""
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from web import render_page

CANVAS_PATH = "/data/.openclaw/canvas/documents/venture-intel/index.html"

def refresh():
    print("🔄 Regenerating venture-intel static HTML...")
    html = render_page(view="all", top_n=10000)
    os.makedirs(os.path.dirname(CANVAS_PATH), exist_ok=True)
    with open(CANVAS_PATH, "w") as f:
        f.write(html)
    print(f"✅ Written {len(html):,} bytes → {CANVAS_PATH}")

    # Quick stats
    from src.data_loader import load_investors, load_founders
    from src.matcher import find_top_matches, assess_capital_needs
    investors = load_investors()
    founders = load_founders()
    for f in founders:
        assess_capital_needs(f)
    matches = find_top_matches(founders, investors, top_n=10000, min_score=65)
    hot = sum(1 for m in matches if m.total_score >= 70)
    warm = sum(1 for m in matches if 66 <= m.total_score < 70)
    print(f"📊 {len(matches)} matches | 🔥 {hot} hot | ⚡ {warm} warm")
    print(f"👥 {len(founders)} founders | 💰 {len(investors)} investors")

if __name__ == "__main__":
    refresh()
