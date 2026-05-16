#!/usr/bin/env python3
"""AI Venture Relationship Intelligence — Web UI v3 (save, auto-refresh, themes)."""
import sys
import os
import json
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import load_investors, load_founders
from src.matcher import (
    find_top_matches,
    find_top_matches_for_founder,
    find_top_matches_for_investor,
)

from src.matcher import assess_capital_needs, filter_capital_ready

investors = load_investors()
founders = load_founders()
investor_map = {i.id: i for i in investors}
founder_map = {f.id: f for f in founders}

# Assess capital needs on load
for f in founders:
    assess_capital_needs(f)
founders_needing_capital = [f for f in founders if f.needs_capital]


def extract_country(location):
    loc = location.lower().strip()
    for kw, country in [
        # Check country names FIRST (more specific, avoid false matches)
        (["india"], "India"),
        (["singapore"], "Singapore"),
        (["china"], "China"),
        (["israel"], "Israel"),
        (["japan"], "Japan"),
        (["canada"], "Canada"),
        (["france"], "France"),
        (["poland"], "Poland"),
        (["uk","london"], "UK"),
        (["warsaw"], "Poland"),
        (["paris"], "France"),
        (["europe"], "Europe"),
        # US cities/states LAST (avoid matching "US" in "India + US")
        (["san francisco","new york","palo alto","seattle","houston","boston","canton","emeryville","mountain view","san mateo","berkeley"], "US"),
        (["middle east","dubai","uae","tel aviv"], "Israel"),
    ]:
        if any(k in loc for k in kw): return country
    # Only match bare "us" if no other country was found
    if "us" in loc and "india" not in loc and "singapore" not in loc and "china" not in loc:
        return "US"
    return "Other"

founder_countries = sorted(set(extract_country(f.location) for f in founders))
investor_countries = sorted(set(extract_country(i.geography) for i in investors))
all_countries = sorted(set(founder_countries + investor_countries))

def score_bar(val, width=100):
    color = "#22c55e" if val >= 75 else "#eab308" if val >= 55 else "#ef4444"
    return f'<div style="display:flex;align-items:center;gap:6px"><div style="width:{width}px;height:6px;background:var(--bar-bg);border-radius:3px;overflow:hidden"><div style="width:{val}%;height:100%;background:{color};border-radius:3px"></div></div><span class="score-num">{val:.0f}</span></div>'

def badge(score):
    if score >= 70: return '<span class="badge badge-hot">🔥 HOT</span>'
    elif score >= 66: return '<span class="badge badge-warm">⚡ WARM</span>'
    return '<span class="badge badge-good">✓ GOOD</span>'

def score_color(score):
    return "#22c55e" if score >= 75 else "#eab308" if score >= 65 else "#ef4444"

def email_draft(m):
    f, i = m.founder, m.investor
    return f"""Subject: {f.company} — {f.brand_positioning[:60]} × {i.firm}'s {i.focus_areas_display} Thesis

Hi {i.firm} Team,

I see strong alignment between {i.firm} and {f.company}.

{f.company} ({f.stage}) is building {f.ai_subsector}.
- {f.brand_positioning}
- {f.traction[:150]}
- Founder: {f.founder_pedigree[:150]}

Given {i.firm}'s focus on {i.focus_areas_display} and portfolio ({', '.join(i.portfolio[:3])}), this is a compelling fit.

Would you be open to a conversation with {f.name}?

Best,
[Your Name]"""


def match_uid(m):
    return f"{m.founder.id}__{m.investor.id}"


def render_match_card(m, idx, show_entity="both"):
    sc = m.total_score
    sc_col = score_color(sc)
    uid = match_uid(m)
    f_country = extract_country(m.founder.location)
    i_country = extract_country(m.investor.geography)

    if show_entity == "investor":
        title = f"{m.investor.firm}"
        sub = f"{m.investor.name} · {m.investor.type} · {m.investor.check_size}"
    elif show_entity == "founder":
        title = f"{m.founder.company}"
        sub = f"{m.founder.name} · {m.founder.stage} · {m.founder.ai_subsector[:60]}"
    else:
        title = f"{m.founder.company} ↔ {m.investor.firm}"
        sub = f"{m.founder.name} · {m.founder.stage} · {m.founder.ai_subsector[:60]}"

    dims = [
        # Core Fit
        ("🏭 Industry Fit", m.score.industry_alignment),
        ("📅 Stage Match", m.score.stage_compatibility),
        ("🌍 Geography", m.score.geography_preference),
        ("📊 Portfolio Fit", m.score.portfolio_similarity),
        # Founder Strength
        ("🏆 Pedigree", m.score.founder_pedigree),
        ("👥 Team Balance", m.score.team_composition),
        ("🔬 Tech Depth", m.score.technical_depth),
        # Business Quality
        ("💰 Revenue", m.score.revenue_traction),
        ("📈 Growth", m.score.growth_momentum),
        ("🛡️ Moat", m.score.moat_defensibility),
        # Market & Signal
        ("🎯 Positioning", m.score.market_positioning),
        ("⭐ Social Proof", m.score.social_proof),
        ("📋 Compliance", m.score.regulatory_readiness),
        # Relationship
        ("💬 Comms Fit", m.score.communication_fit),
        ("⚡ Responsiveness", m.score.investor_responsiveness),
        ("🌟 Reputation", m.score.investor_reputation),
        ("🤝 Intro Access", m.score.warm_intro_access),
        ("🎯 Conversion", m.score.conversion_likelihood),
    ]

    scores_html = "".join(
        f'<div class="score-row"><div class="score-label">{n}</div>{score_bar(v, 80)}</div>'
        for n, v in dims
    )
    intros = "".join(f"<li class='intro-item'>→ {p}</li>" for p in m.warm_intro_pathways)

    return f'''
<div class="match-card" data-score="{sc}" data-investor="{m.investor.firm}" data-founder="{m.founder.company}" data-investor-id="{m.investor.id}" data-founder-id="{m.founder.id}" data-fcountry="{f_country}" data-icountry="{i_country}" data-uid="{uid}">
  <div class="match-header" onclick="this.nextElementSibling.classList.toggle('open')">
    <div class="match-rank">#{idx}</div>
    <div class="match-title">
      <div class="match-name">{title}</div>
      <div class="match-sub">{sub}</div>
    </div>
    <div class="match-meta">
      <button class="save-btn" onclick="event.stopPropagation();toggleSave('{uid}',this)" title="Save this match">☆</button>
      {badge(sc)}
      <div class="match-score" style="color:{sc_col}">{sc:.0f}</div>
    </div>
  </div>
  <div class="details">
    <div class="details-grid">
      <div class="detail-section">
        <h4>🏢 Founder</h4>
        <p><strong>{m.founder.name}</strong> — {m.founder.role}<br>{m.founder.background[:200]}</p>
        {f'<div class="founder-links"><a href="{m.founder.website}" target="_blank" class="link-btn">🌐 Website</a>' if m.founder.website else ''}{f' <a href="{m.founder.linkedin_url}" target="_blank" class="link-btn">💼 LinkedIn</a>' if m.founder.linkedin_url else ''}{f' <a href="{m.founder.twitter_url}" target="_blank" class="link-btn">🐦 Twitter</a>' if m.founder.twitter_url else ''}{'</div>' if (m.founder.website or m.founder.linkedin_url or m.founder.twitter_url) else ''}
        <p><strong>Mission:</strong> {m.founder.mission[:200]}<br><strong>Traction:</strong> {m.founder.traction[:200]}<br><strong>Brand:</strong> {m.founder.brand_positioning[:150]}<br><strong>Location:</strong> {m.founder.location}</p>
        <div class='detail-grid'><strong>Incorporated:</strong> {m.founder.year_incorporated} &nbsp;|&nbsp; <strong>Proj. Sales Y1:</strong> {m.founder.projected_sales_y1} &nbsp;|&nbsp; <strong>Growth (12mo):</strong> {m.founder.growth_last_12mo}</div>
        {f'<p style="margin-top:8px"><strong>🔬 Tech:</strong> {m.founder.technical_depth[:180]}</p>' if m.founder.technical_depth else ''}
        {f'<p><strong>🛡️ Moat:</strong> {m.founder.moat[:180]}</p>' if m.founder.moat else ''}
      </div>
      <div class="detail-section">
        <h4>💰 Investor</h4>
        <p><strong>{m.investor.name}</strong> — {m.investor.firm}<br>{m.investor.type} · {m.investor.check_size}<br><br><strong>Focus:</strong> {', '.join(m.investor.ai_focus)}<br><strong>Stages:</strong> {', '.join(m.investor.stage_focus)}<br><strong>Speed:</strong> {m.investor.decision_speed}<br><strong>Location:</strong> {m.investor.geography}</p>
      </div>
    </div>
    <div class="detail-section" style="margin-top:16px">
      <h4>📊 Score Breakdown</h4>
      <div class="scores-grid">{scores_html}</div>
    </div>
    <div class="details-grid" style="margin-top:16px">
      <div class="detail-section">
        <h4>🎯 Intelligence</h4>
        <p><strong>Meeting Acceptance:</strong> {m.meeting_acceptance_likelihood:.0f}%<br><strong>Investment Probability:</strong> {m.investment_probability:.0f}%<br><strong>Timing:</strong> {m.best_timing}<br><strong>Style:</strong> {m.ideal_communication_style}</p>
      </div>
      <div class="detail-section">
        <h4>🔗 Warm Intro Pathways</h4>
        <ul class="intro-list">{intros}</ul>
      </div>
    </div>
    <div class="detail-section" style="margin-top:16px">
      <h4>📧 Draft Email</h4>
      <div class="email-draft">{email_draft(m)}</div>
    </div>
  </div>
</div>'''


country_options = '<option value="all">🌍 All Countries</option>' + "".join(
    f'<option value="{c}">{c}</option>' for c in all_countries
)

last_updated = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

def render_page(view="all", entity_id=None, top_n=10000):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    if view == "founder" and entity_id and entity_id in founder_map:
        f = founder_map[entity_id]
        matches = find_top_matches_for_founder(f, investors, top_n=top_n or 9999)
        if matches:
            page_title = f"Top {len(matches)} Investors for {f.company}"
        else:
            page_title = f"No active investor matches for {f.company} (well-capitalized or no fit ≥ 65)"
        show_entity = "investor"
    elif view == "investor" and entity_id and entity_id in investor_map:
        inv = investor_map[entity_id]
        matches = find_top_matches_for_investor(inv, founders, top_n=top_n)
        if matches:
            page_title = f"Top {len(matches)} Founders for {inv.firm}"
        else:
            page_title = f"No active founder matches for {inv.firm} (all filtered or no fit ≥ 65)"
        show_entity = "founder"
    else:
        matches = find_top_matches(founders, investors, top_n=top_n, min_score=65)
        page_title = f"Top {len(matches)} Matches"
        show_entity = "both"

    founder_opts = "".join(
        f'<option value="{f.id}" {"selected" if entity_id == f.id else ""}>{f.company} ({f.name[:20]})</option>'
        for f in sorted(founders_needing_capital, key=lambda x: x.company)
    )
    investor_opts = "".join(
        f'<option value="{i.id}" {"selected" if entity_id == i.id else ""}>{i.firm}</option>'
        for i in sorted(investors, key=lambda x: x.firm)
    )
    # Escape for JS strings
    founder_opts_js = founder_opts.replace("'", "\\'")
    investor_opts_js = investor_opts.replace("'", "\\'")

    cards = "".join(render_match_card(m, idx, show_entity) for idx, m in enumerate(matches, 1))
    avg_score = sum(m.total_score for m in matches) / len(matches) if matches else 0
    hot = sum(1 for m in matches if m.total_score >= 70)
    warm = sum(1 for m in matches if 66 <= m.total_score < 70)

    # Auto-save: find top 10 highest-scoring matches for JS persistence
    top10_matches = find_top_matches(founders, investors, top_n=10, min_score=65)
    saved_data = json.dumps({match_uid(m): {"f": m.founder.company, "i": m.investor.firm, "s": m.total_score, "auto": True}
                             for m in top10_matches})

    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>🤖 AI Venture Intel</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=VT323&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;transition:all .3s}}

:root,[data-theme="dark"]{{
  --bg:#0a0a0f;--bg2:#0d0d14;--card:#12121a;--border:#1e1e2e;
  --accent:#6366f1;--accent2:#8b5cf6;--text:#e2e8f0;--muted:#64748b;--dim:#334155;
  --bar-bg:#1e1e2e;--header-bg:linear-gradient(135deg,#0f0f1a,#1a1033);
  --btn-bg:#12121a;--btn-border:#1e1e2e;--btn-active-bg:#6366f1;--btn-active-text:#fff;
  --input-bg:#12121a;--input-border:#1e1e2e;
  --badge-hot-bg:rgba(239,68,68,.15);--badge-hot-color:#ef4444;
  --badge-warm-bg:rgba(234,179,8,.15);--badge-warm-color:#eab308;
  --badge-good-bg:rgba(34,197,94,.15);--badge-good-color:#22c55e;
  --email-bg:#0a0a12;--footer-color:#334155;--save-color:#fbbf24;
}}

[data-theme="cyberpunk"]{{
  --bg:#0a0014;--bg2:#0d001a;--card:#140020;--border:#ff2d9533;
  --accent:#ff2d95;--accent2:#00f0ff;--text:#f0e0ff;--muted:#a080c0;--dim:#503070;
  --bar-bg:#1a0030;--header-bg:linear-gradient(135deg,#0a0014,#1a0030);
  --btn-bg:#140020;--btn-border:#ff2d9533;--btn-active-bg:#ff2d95;--btn-active-text:#fff;
  --input-bg:#140020;--input-border:#ff2d9533;
  --badge-hot-bg:rgba(255,45,149,.2);--badge-hot-color:#ff2d95;
  --badge-warm-bg:rgba(0,240,255,.15);--badge-warm-color:#00f0ff;
  --badge-good-bg:rgba(184,41,221,.15);--badge-good-color:#b829dd;
  --email-bg:#0a0014;--footer-color:#503070;--save-color:#ff2d95;
}}
[data-theme="cyberpunk"] .match-card:hover{{box-shadow:0 0 20px rgba(255,45,149,.15)}}
[data-theme="cyberpunk"] .match-name{{text-shadow:0 0 8px rgba(255,45,149,.3)}}
[data-theme="cyberpunk"] .match-score{{text-shadow:0 0 12px currentColor}}
[data-theme="cyberpunk"] .stat-num{{text-shadow:0 0 8px var(--accent)}}
[data-theme="cyberpunk"] .logo{{background:linear-gradient(135deg,#ff2d95,#00f0ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
[data-theme="cyberpunk"] .badge{{border:1px solid currentColor}}
[data-theme="cyberpunk"] .score-row:hover{{background:rgba(255,45,149,.05)}}
[data-theme="cyberpunk"] .match-card{{border-color:#ff2d9522}}
[data-theme="cyberpunk"] .match-card:hover{{border-color:#ff2d95}}

[data-theme="pastel"]{{
  --bg:#faf7f2;--bg2:#f5f0e8;--card:#ffffff;--border:#e0d8cc;
  --accent:#9b8ec4;--accent2:#c4a0a0;--text:#3d3535;--muted:#8a7e7e;--dim:#b5abab;
  --bar-bg:#e8e0d8;--header-bg:linear-gradient(135deg,#faf7f2,#f0e8e0);
  --btn-bg:#ffffff;--btn-border:#e0d8cc;--btn-active-bg:#9b8ec4;--btn-active-text:#fff;
  --input-bg:#ffffff;--input-border:#e0d8cc;
  --badge-hot-bg:rgba(200,100,120,.12);--badge-hot-color:#c86478;
  --badge-warm-bg:rgba(200,170,100,.12);--badge-warm-color:#c8aa64;
  --badge-good-bg:rgba(120,170,140,.12);--badge-good-color:#6aaa7c;
  --email-bg:#f8f4ee;--footer-color:#b5abab;--save-color:#d4a07c;
}}
[data-theme="pastel"] .match-card:hover{{box-shadow:0 2px 12px rgba(155,142,196,.12)}}
[data-theme="pastel"] .match-card{{border-color:#e0d8cc}}
[data-theme="pastel"] .match-card:hover{{border-color:#9b8ec4}}
[data-theme="pastel"] .score-row:hover{{background:rgba(155,142,196,.06)}}
[data-theme="pastel"] .badge{{border:1px solid currentColor}}
[data-theme="pastel"] .logo{{background:linear-gradient(135deg,#9b8ec4,#c4a0a0);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}

.header{{background:var(--header-bg);border-bottom:1px solid var(--border);padding:20px 0}}
.header-inner{{max-width:1200px;margin:0 auto;padding:0 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px}}
.logo{{font-size:22px;font-weight:700;background:linear-gradient(135deg,var(--accent),var(--accent2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.subtitle{{color:var(--muted);font-size:12px;margin-top:2px}}
.stats{{display:flex;gap:20px}}
.stat{{text-align:center}}.stat-num{{font-size:24px;font-weight:700;color:var(--accent)}}.stat-label{{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px}}

.controls{{max-width:1200px;margin:0 auto;padding:16px 24px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;background:var(--bg2);border-bottom:1px solid var(--border)}}
.btn{{padding:7px 14px;border-radius:8px;border:1px solid var(--btn-border);background:var(--btn-bg);color:var(--text);cursor:pointer;font-size:12px;font-weight:600;transition:all .15s}}
.btn:hover{{border-color:var(--accent)}}
.btn.active{{background:var(--btn-active-bg);border-color:var(--btn-active-bg);color:var(--btn-active-text)}}
.btn-theme{{position:relative}}
[data-theme="cyberpunk"] .refresh-badge{{background:rgba(255,45,149,.15);color:#ff2d95}}
[data-theme="pastel"] .refresh-badge{{background:rgba(155,142,196,.12);color:#9b8ec4}}
input,select{{padding:7px 12px;border-radius:8px;border:1px solid var(--input-border);background:var(--input-bg);color:var(--text);cursor:pointer;font-size:12px;outline:none}}
input:focus,select:focus{{border-color:var(--accent)}}
input::placeholder{{color:var(--dim)}}
.search-box{{flex:1;min-width:180px}}

.match-card{{background:var(--card);border:1px solid var(--border);border-radius:12px;margin-bottom:12px;overflow:hidden;transition:all .2s}}
.match-card:hover{{border-color:var(--accent)}}
.match-card.saved{{border-left:3px solid var(--save-color)}}
.match-header{{display:flex;justify-content:space-between;align-items:center;padding:16px 20px;cursor:pointer}}
.match-rank{{font-size:13px;font-weight:700;color:var(--accent);min-width:35px}}
.match-title{{flex:1}}.match-name{{font-size:15px;font-weight:600}}.match-sub{{color:var(--muted);font-size:12px;margin-top:3px}}
.match-meta{{display:flex;align-items:center;gap:10px}}
.match-score{{font-size:24px;font-weight:700;min-width:45px;text-align:right}}
.save-btn{{background:none;border:none;font-size:20px;cursor:pointer;color:var(--dim);transition:all .2s;padding:4px}}
.save-btn:hover{{transform:scale(1.2)}}
.save-btn.saved{{color:var(--save-color);text-shadow:0 0 8px var(--save-color)}}
.badge{{padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600}}
.badge-hot{{background:var(--badge-hot-bg);color:var(--badge-hot-color)}}
.badge-warm{{background:var(--badge-warm-bg);color:var(--badge-warm-color)}}
.badge-good{{background:var(--badge-good-bg);color:var(--badge-good-color)}}
.details{{display:none;border-top:1px solid var(--border);padding:20px;background:var(--bg2)}}
.open{{display:block!important}}
.details-grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
.detail-section h4{{font-size:12px;text-transform:uppercase;letter-spacing:1px;color:var(--muted);margin-bottom:10px}}
.detail-section p{{font-size:13px;line-height:1.6}}
.scores-grid{{display:grid;grid-template-columns:1fr 1fr;gap:6px}}
.score-row{{display:flex;align-items:center;gap:8px;font-size:12px;padding:3px 6px;border-radius:4px;transition:background .15s}}
.score-row:hover{{background:rgba(99,102,241,.05)}}
.score-label{{width:100px;color:var(--muted);text-align:right;flex-shrink:0}}
.score-num{{font-size:12px;color:var(--muted)}}
.intro-list{{list-style:none;padding:0}}.intro-item{{font-size:12px;color:var(--muted);padding:2px 0}}
.email-draft{{background:var(--email-bg);border:1px solid var(--border);border-radius:8px;padding:14px;font-size:12px;line-height:1.6;color:var(--muted);white-space:pre-wrap;font-family:'JetBrains Mono',monospace;max-height:180px;overflow-y:auto}}
.detail-grid{{display:inline-flex;gap:8px;flex-wrap:wrap;background:var(--bg2);padding:6px 10px;border-radius:6px;border:1px solid var(--border);font-size:11px;margin-top:6px}}
.detail-grid strong{{color:var(--muted)}}
.founder-links{{margin:8px 0;display:flex;gap:6px;flex-wrap:wrap}}
.link-btn{{display:inline-block;padding:5px 12px;border-radius:6px;border:1px solid var(--border);background:var(--btn-bg);color:var(--accent);text-decoration:none;font-size:11px;font-weight:600;transition:all .15s}}
.link-btn:hover{{border-color:var(--accent);background:var(--accent);color:#fff}}
.footer{{text-align:center;padding:20px;color:var(--footer-color);font-size:11px;border-top:1px solid var(--border)}}
.page-title{{font-size:16px;font-weight:600;margin-bottom:16px}}
.saved-count{{position:absolute;top:-6px;right:-6px;background:var(--save-color);color:#000;border-radius:50%;width:18px;height:18px;font-size:10px;font-weight:700;display:flex;align-items:center;justify-content:center}}
.refresh-badge{{display:inline-block;padding:3px 8px;border-radius:6px;background:rgba(34,197,94,.15);color:#22c55e;font-size:10px;font-weight:600;margin-left:8px;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.5}}}}
@media(max-width:768px){{.details-grid,.scores-grid{{grid-template-columns:1fr}}.header-inner{{flex-direction:column;gap:12px}}.controls{{flex-direction:column}}}}

/* ── Chat Widget ── */
.chat-toggle{{position:fixed;bottom:24px;right:24px;width:56px;height:56px;border-radius:50%;background:var(--accent);color:#fff;border:none;font-size:24px;cursor:pointer;z-index:999;box-shadow:0 4px 20px rgba(0,0,0,.3);transition:all .2s;display:flex;align-items:center;justify-content:center}}
.chat-toggle:hover{{transform:scale(1.1);background:var(--accent2)}}
.chat-toggle .close-icon{{display:none}}
.chat-toggle.open .chat-icon{{display:none}}
.chat-toggle.open .close-icon{{display:inline}}
.chat-window{{position:fixed;bottom:90px;right:24px;width:400px;height:560px;background:var(--card);border:1px solid var(--border);border-radius:16px;z-index:998;display:none;flex-direction:column;box-shadow:0 8px 40px rgba(0,0,0,.4)}}
.chat-window.open{{display:flex}}
.chat-header{{padding:12px 16px;background:var(--header-bg);border-bottom:1px solid var(--border);font-size:14px;font-weight:600;flex-shrink:0;display:flex;justify-content:space-between;align-items:center}}
.chat-header-btns{{display:flex;gap:6px}}
.chat-header-btn{{background:var(--btn-bg);border:1px solid var(--border);color:var(--muted);border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer;transition:all .15s}}
.chat-header-btn:hover{{border-color:var(--accent);color:var(--accent)}}
.chat-body{{flex:1;display:flex;flex-direction:column;overflow:hidden;min-height:0}}
.chat-messages{{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:10px;min-height:0}}
.chat-msg{{max-width:85%;padding:10px 14px;border-radius:12px;font-size:13px;line-height:1.5;animation:fadeIn .3s;flex-shrink:0}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}
.chat-msg.bot{{background:var(--bg2);border:1px solid var(--border);align-self:flex-start;border-bottom-left-radius:4px}}
.chat-msg.user{{background:var(--accent);color:#fff;align-self:flex-end;border-bottom-right-radius:4px}}
.chat-msg.user .chat-msg-text{{color:#fff}}
.chat-options{{display:flex;flex-wrap:wrap;gap:6px;padding:10px 14px;border-top:1px solid var(--border);flex-shrink:0;max-height:200px;overflow-y:auto;background:var(--bg2)}}
.chat-opt{{padding:8px 14px;border-radius:20px;border:1px solid var(--border);background:var(--btn-bg);color:var(--text);cursor:pointer;font-size:12px;transition:all .15s}}
.chat-opt:hover{{border-color:var(--accent);background:var(--accent);color:#fff}}
.chat-opt.selected{{background:var(--accent);border-color:var(--accent);color:#fff}}
.chat-result{{margin:0;padding:10px 14px;background:var(--bg2);border-top:1px solid var(--border);font-size:12px;color:var(--muted);flex-shrink:0}}
.chat-result-btns{{display:flex;gap:6px;margin-top:8px}}
.chat-result strong{{color:var(--text);font-size:13px}}
.chat-reset{{padding:8px 14px;border-radius:8px;border:1px solid var(--border);background:var(--btn-bg);color:var(--text);cursor:pointer;font-size:12px;transition:all .15s}}
.chat-reset:hover{{border-color:var(--accent)}}
[data-theme="pastel"] .chat-toggle{{box-shadow:0 2px 12px rgba(155,142,196,.3)}}
[data-theme="cyberpunk"] .chat-toggle{{box-shadow:0 4px 20px rgba(255,45,149,.3)}}
@media(max-width:480px){{.chat-window{{right:8px;left:8px;width:auto;bottom:80px;height:500px}}}}
</style></head><body>

<div class="header">
<div class="header-inner">
<div>
<div class="logo">🤖 AI Venture Intelligence</div>
<div class="subtitle">Many-to-Many · {len(founders_needing_capital)} founders seeking capital ({len(founders)} total) · {len(investors)} investors · Last updated: {last_updated} <span class="refresh-badge">🔄 Auto-refreshes every 48h</span></div>
</div>
<div class="stats">
<div class="stat"><div class="stat-num">{len(matches)}</div><div class="stat-label">Matches</div></div>
<div class="stat"><div class="stat-num">{hot}</div><div class="stat-label">🔥 Hot</div></div>
<div class="stat"><div class="stat-num">{warm}</div><div class="stat-label">⚡ Warm</div></div>
<div class="stat"><div class="stat-num">{avg_score:.0f}</div><div class="stat-label">Avg</div></div>
</div></div></div>

<div class="controls">
<button class="btn btn-theme" id="btn-dark" onclick="setTheme('dark')">🌙 Dark</button>
<button class="btn btn-theme" id="btn-cyberpunk" onclick="setTheme('cyberpunk')">💜 Cyberpunk</button>
<button class="btn btn-theme" id="btn-pastel" onclick="setTheme('pastel')">🌸 Pastel</button>

<button class="btn" id="btn-all" onclick="window.location.href='?view=all'">All Matches</button>
<button class="btn" id="btn-founder" onclick="showSelect('founder')">By Founder</button>
<button class="btn" id="btn-investor" onclick="showSelect('investor')">By Investor</button>
<button class="btn" id="btn-saved" onclick="filterSaved()" style="position:relative">⭐ Saved <span class="saved-count" id="saved-count" style="display:none">0</span></button>
<button class="btn" onclick="location.reload()" title="Reload page with latest data">🔄 Refresh</button>

<select id="entity-select" onchange="goToEntity()" style="display:none;min-width:250px">
<option value="">Select...</option>
<optgroup label="Founders">{founder_opts}</optgroup>
<optgroup label="Investors">{investor_opts}</optgroup>
</select>

<select id="country-filter" onchange="filterCountry()">{country_options}</select>

<input type="text" id="search" class="search-box" placeholder="🔍 Search investors, founders, companies...">
<select id="sort" onchange="sortCards()">
<option value="score">Score ↓</option><option value="score-asc">Score ↑</option><option value="investor">Investor</option><option value="founder">Founder</option></select>
<select id="filter" onchange="filterScore()">
<option value="all">All</option><option value="hot">🔥 Hot (70+)</option><option value="warm">⚡ Warm (66-69)</option><option value="good">✓ Good (65)</option></select>
<button class="btn" onclick="document.querySelectorAll('.details').forEach(d=>d.classList.add('open'))">Expand All</button>
<button class="btn" onclick="document.querySelectorAll('.details').forEach(d=>d.classList.remove('open'))">Collapse</button>
</div>

<div style="max-width:1200px;margin:0 auto;padding:16px 24px 40px">
<div class="page-title" id="page-title">{page_title}</div>
<div id="matches">{cards}</div>
</div>

<div class="footer">
AI Venture Intelligence v3.0 · {len(founders)} founders × {len(investors)} investors = {len(founders)*len(investors)} pairs · Auto-refreshes every 48h · Saves persist in browser
</div>

<script>
// ── ALL MATCH DATA for saved view ──
const ALL_MATCHES = {saved_data};

// ── Theme ──
function setTheme(t){{
  document.documentElement.setAttribute('data-theme',t);
  localStorage.setItem('theme',t);
  ['dark','cyberpunk','pastel'].forEach(s=>{{
    const b=document.getElementById('btn-'+s);
    if(b)b.classList.toggle('active',t===s);
  }});
}}
(function(){{setTheme(localStorage.getItem('theme')||'dark')}})();

// ── Saved matches ──
function getSaved(){{return JSON.parse(localStorage.getItem('saved_matches')||'{{}}')}}
function saveSaved(s){{localStorage.setItem('saved_matches',JSON.stringify(s));updateSavedCount()}}
function toggleSave(uid,btn){{
  const s=getSaved();
  if(s[uid]){{delete s[uid];btn.classList.remove('saved');btn.textContent='☆'}}
  else{{
    const card=btn.closest('.match-card');
    s[uid]={{f:card.dataset.founder,i:card.dataset.investor,s:card.dataset.score,ts:Date.now()}};
    btn.classList.add('saved');btn.textContent='★';
  }}
  saveSaved(s);
}}
function updateSavedCount(){{
  let s=getSaved();
  // Always cap at 10 — keep highest scores
  const entries=Object.entries(s).sort((a,b)=>(b[1].s||0)-(a[1].s||0));
  if(entries.length>10){{
    const trimmed=Object.fromEntries(entries.slice(0,10));
    localStorage.setItem('saved_matches',JSON.stringify(trimmed));
    s=trimmed;
  }}
  const n=Object.keys(s).length;
  const el=document.getElementById('saved-count');
  el.style.display=n>0?'flex':'none';
  el.textContent=n;
}}
// Auto-save top 10 on load — merge with existing, keep highest scores
(function(){{
  const AUTO_SAVE_DATA={saved_data};
  let s=getSaved();
  // Merge auto-saved top 10 into existing saved
  Object.entries(AUTO_SAVE_DATA).forEach(([uid,data])=>{{
    if(!s[uid]||(data.s||0)>(s[uid].s||0)){{
      s[uid]=data;
    }}
  }});
  // Cap at 10 — keep highest scores
  const entries=Object.entries(s).sort((a,b)=>(b[1].s||0)-(a[1].s||0));
  const capped=Object.fromEntries(entries.slice(0,10));
  localStorage.setItem('saved_matches',JSON.stringify(capped));
  s=capped;
  // Mark saved buttons on cards
  document.querySelectorAll('.match-card').forEach(c=>{{
    const uid=c.dataset.uid;
    const btn=c.querySelector('.save-btn');
    if(s[uid]){{btn.classList.add('saved');btn.textContent='★';c.classList.add('saved')}}
  }});
  updateSavedCount();
}})();

// ── Filter saved ──
let showingSaved=false;
function filterSaved(){{
  showingSaved=!showingSaved;
  const s=getSaved();
  const btn=document.getElementById('btn-saved');
  btn.classList.toggle('active',showingSaved);
  if(showingSaved){{
    document.querySelectorAll('.match-card').forEach(c=>{{
      c.style.display=s[c.dataset.uid]?'':'none';
    }});
    document.getElementById('page-title').textContent='⭐ Saved Matches ('+Object.keys(s).length+')';
  }} else {{
    document.querySelectorAll('.match-card').forEach(c=>{{c.style.display=''}});
    document.getElementById('page-title').textContent='{page_title}';
  }}
}}

// ── Views ──
function showSelect(type){{
  const sel=document.getElementById('entity-select');
  sel.style.display='block';
  if(type==='founder'){{
    sel.innerHTML='<option value="">Select founder...</option><optgroup label="Founders">{founder_opts_js}</optgroup>';
  }} else {{
    sel.innerHTML='<option value="">Select investor...</option><optgroup label="Investors">{investor_opts_js}</optgroup>';
  }}
}}
function goToEntity(){{
  const v=document.getElementById('entity-select').value;
  if(!v)return;
  const og=document.getElementById('entity-select').querySelector('option[value="'+v+'"]');
  if(!og)return;
  const isF=og.closest('optgroup').label==='Founders';
  window.location.href='?view='+(isF?'founder':'investor')+'&id='+v;
}}

// ── Client-side routing for static site ──
(function(){{
  const params=new URLSearchParams(window.location.search);
  const view=params.get('view');
  const id=params.get('id');
  if(!view||view==='all')return;
  const cards=document.querySelectorAll('.match-card');
  let count=0;
  if(view==='founder'&&id){{
    cards.forEach(c=>{{
      if(c.dataset.founderId===id){{c.style.display='';count++}}
      else c.style.display='none';
    }});
    const nameEl=document.querySelector('[data-founder-id="'+id+'"] .match-name');
    const fname=nameEl?nameEl.textContent:id;
    document.getElementById('page-title').textContent=count>0?'🏢 '+fname+' — Top '+count+' investor matches':'🏢 '+fname+' — No active matches (may be well-capitalized or below threshold)';
  }} else if(view==='investor'&&id){{
    cards.forEach(c=>{{
      if(c.dataset.investorId===id){{c.style.display='';count++}}
      else c.style.display='none';
    }});
    const nameEl=document.querySelector('[data-investor-id="'+id+'"] .match-name');
    const iname=nameEl?nameEl.textContent:id;
    document.getElementById('page-title').textContent=count>0?'💰 '+iname+' — Top '+count+' founder matches':'💰 '+iname+' — No active matches found';
  }}
  if(count>0){{
    const notice=document.createElement('div');
    notice.className='controls';
    notice.style.cssText='justify-content:center;background:var(--bg2);margin:0 auto;max-width:1200px;padding:8px 24px';
    notice.innerHTML='<span style="color:var(--muted);font-size:12px">Showing '+count+' matches · <a href="?view=all" style="color:var(--accent)">← Back to all matches</a></span>';
    document.querySelector('.controls').after(notice);
  }} else {{
    const notice=document.createElement('div');
    notice.className='controls';
    notice.style.cssText='justify-content:center;background:var(--bg2);margin:0 auto;max-width:1200px;padding:12px 24px';
    notice.innerHTML='<span style="color:var(--muted);font-size:13px">This founder/investor has no matches above the threshold. <a href="?view=all" style="color:var(--accent)">← Back to all matches</a></span>';
    document.querySelector('.controls').after(notice);
  }}
}})();

// ── Search ──
document.getElementById('search').addEventListener('input',function(q){{
  const t=q.target.value.toLowerCase();
  document.querySelectorAll('.match-card').forEach(c=>{{c.style.display=c.textContent.toLowerCase().includes(t)?'':'none'}});
}});

// ── Sort ──
function sortCards(){{
  const v=document.getElementById('sort').value;
  const c=document.getElementById('matches'),cards=[...c.children];
  cards.sort((a,b)=>{{
    if(v==='score')return b.dataset.score-a.dataset.score;
    if(v==='score-asc')return a.dataset.score-b.dataset.score;
    if(v==='investor')return a.dataset.investor.localeCompare(b.dataset.investor);
    return a.dataset.founder.localeCompare(b.dataset.founder);
  }});
  cards.forEach(x=>c.appendChild(x));
  [...c.children].forEach((x,i)=>{{const r=x.querySelector('.match-rank');if(r)r.textContent='#'+(i+1)}});
}}

// ── Filters ──
function filterScore(){{
  const m=document.getElementById('filter').value;
  document.querySelectorAll('.match-card').forEach(c=>{{
    const s=parseFloat(c.dataset.score);
    c.style.display=(m==='all')?'':(m==='hot'&&s>=70)?'':(m==='warm'&&s>=66&&s<70)?'':(m==='good'&&s>=65&&s<66)?'':'none';
  }});
}}
function filterCountry(){{
  const country=document.getElementById('country-filter').value;
  document.querySelectorAll('.match-card').forEach(c=>{{
    if(country==='all'){{c.style.display='';return;}}
    const fc=c.dataset.fcountry||'';const ic=c.dataset.icountry||'';
    c.style.display=(fc===country||ic===country)?'':'none';
  }});
}}

// ── Chat Widget ──
const CHAT_STEPS = [
  {{id:'sector',q:'What kind of AI startup are you looking to invest in?',options:['AI Infrastructure','Healthcare AI','Fintech AI','Defense AI','Developer Tools','Legal AI','Consumer AI','Robotics','Foundation Models','All Sectors']}},
  {{id:'stage',q:'What stage do you prefer?',options:['Pre-Seed / Seed','Series A','Series B','Growth','Any Stage']}},
  {{id:'region',q:'Which region?',options:['US','India','Singapore','Europe','Asia (excl. India/Singapore)','Global','Any Region']}},
  {{id:'priority',q:'What matters most to you?',options:['Highest Traction','Best Team','Fastest Growth','Strongest Brand','Top Social Proof','Show Me Everything']}},
];
let chatStep=0;
let chatAnswers={{}};
let chatOpen=false;

function toggleChat(){{
  chatOpen=!chatOpen;
  document.getElementById('chat-window').classList.toggle('open',chatOpen);
  document.getElementById('chat-toggle').classList.toggle('open',chatOpen);
  if(chatOpen && chatStep===0) startChat();
}}

function restartChat(){{
  document.getElementById('chat-result').style.display='none';
  document.getElementById('chat-options').innerHTML='';
  // Reset all filters
  document.querySelectorAll('.match-card').forEach(c=>c.style.display='');
  document.getElementById('page-title').textContent='{page_title}';
  startChat();
}}

function startChat(){{
  chatStep=0; chatAnswers={{}};
  const msgs=document.getElementById('chat-messages');
  msgs.innerHTML='';
  document.getElementById('chat-options').innerHTML='';
  document.getElementById('chat-result').style.display='none';
  addBotMsg('Hey! 👋 I can help you find the perfect AI startup matches. Let me ask you a few questions.');
  setTimeout(()=>showStep(0),600);
}}

function addBotMsg(text){{
  const msgs=document.getElementById('chat-messages');
  const d=document.createElement('div');d.className='chat-msg bot';d.innerHTML=text;
  msgs.appendChild(d);msgs.scrollTop=msgs.scrollHeight;
}}

function addUserMsg(text){{
  const msgs=document.getElementById('chat-messages');
  const d=document.createElement('div');d.className='chat-msg user';d.innerHTML='<span class="chat-msg-text">'+text+'</span>';
  msgs.appendChild(d);msgs.scrollTop=msgs.scrollHeight;
}}

function showStep(idx){{
  if(idx>=CHAT_STEPS.length){{applyFilters();return;}}
  const step=CHAT_STEPS[idx];
  addBotMsg(step.q);
  const opts=document.getElementById('chat-options');
  opts.innerHTML='';
  step.options.forEach(o=>{{
    const btn=document.createElement('button');btn.className='chat-opt';btn.textContent=o;
    btn.onclick=()=>selectOption(step.id,o,btn);
    opts.appendChild(btn);
  }});
}}

function selectOption(stepId,value,btn){{
  document.querySelectorAll('.chat-opt').forEach(b=>b.classList.remove('selected'));
  btn.classList.add('selected');
  chatAnswers[stepId]=value;
  addUserMsg(value);
  setTimeout(()=>{{
    document.getElementById('chat-options').innerHTML='';
    chatStep++;
    showStep(chatStep);
  }},400);
}}

function applyFilters(){{
  const cards=[...document.querySelectorAll('.match-card')];
  let visible=0;

  cards.forEach(c=>{{
    let show=true;
    const text=c.textContent.toLowerCase();

    // Sector filter
    const sector=chatAnswers.sector;
    if(sector && sector!=='All Sectors'){{
      const sectorMap={{'ai infrastructure':['infra','compute','gpu','cloud','developer','agent','protocol','search'],'healthcare ai':['health','medical','clinical','drug','pharma'],'fintech ai':['finance','fintech','wealth','compliance','banking','payment'],'defense ai':['defense','military','autonomous','fleet','security'],'developer tools':['developer','devtools','coding','api','sdk','open-source'],'legal ai':['legal','law'],'consumer ai':['consumer','social','creator','entertainment','voice','character'],'robotics':['robot','humanoid','physical'],'foundation models':['foundation','llm','language model','moonshot','mistral']}};
      const kws=sectorMap[sector.toLowerCase()]||[];
      if(!kws.some(k=>text.includes(k))) show=false;
    }}

    // Stage filter
    const stage=chatAnswers.stage;
    if(stage && stage!=='Any Stage'){{
      const stageKws={{'pre-seed / seed':['pre-seed','seed','yc-backed'],'series a':['series a'],'series b':['series b'],'growth':['growth','series c','series d','series b ($']}};
      const kws=stageKws[stage.toLowerCase()]||[];
      if(!kws.some(k=>text.includes(k))) show=false;
    }}

    // Region filter
    const region=chatAnswers.region;
    if(region && region!=='Any Region'){{
      const fc=c.dataset.fcountry||'';const ic=c.dataset.icountry||'';
      if(region==='US'){{if(fc!=='US'&&ic!=='US')show=false;}}
      else if(region==='India'){{if(fc!=='India'&&ic!=='India')show=false;}}
      else if(region==='Singapore'){{if(fc!=='Singapore'&&ic!=='Singapore')show=false;}}
      else if(region==='Europe'){{if(!['Europe','UK','France','Poland'].includes(fc)&&!['Europe','UK','France','Poland'].includes(ic))show=false;}}
      else if(region==='Asia (excl. India/Singapore)'){{if(!['Asia','Singapore','India'].includes(fc)&&!['Asia','Singapore','India'].includes(ic))show=false;}}
      else if(region==='Global'){{show=true;}}
    }}

    if(show){{visible++;c.style.display='';}}
    else c.style.display='none';
  }});

  // Priority sort
  const priority=chatAnswers.priority;
  if(priority && priority!=='Show Me Everything'){{
    const container=document.getElementById('matches');
    const sorted=[...container.children].filter(c=>c.style.display!=='none');
    sorted.sort((a,b)=>{{
      if(priority==='Highest Traction'){{
        const aT=parseFloat(a.dataset.score);const bT=parseFloat(b.dataset.score);
        return bT-aT;
      }}
      return parseFloat(b.dataset.score)-parseFloat(a.dataset.score);
    }});
    sorted.forEach(x=>container.appendChild(x));
    [...container.children].forEach((x,i)=>{{if(x.style.display!=='none'){{const r=x.querySelector('.match-rank');if(r)r.textContent='#'+(i+1)}}}});
  }}

  // Show result
  const resultDiv=document.getElementById('chat-result');
  resultDiv.style.display='block';
  resultDiv.innerHTML=`<strong>${{visible}} matches found</strong> for ${{chatAnswers.sector||'All'}} · ${{chatAnswers.stage||'Any'}} · ${{chatAnswers.region||'Anywhere'}}`;
  document.getElementById('page-title').textContent=`Filtered: ${{visible}} matches`;
  document.getElementById('chat-options').innerHTML='';
}}
</script>

<!-- Chat Widget -->
<button class="chat-toggle" id="chat-toggle" onclick="toggleChat()">
  <span class="chat-icon">💬</span>
  <span class="close-icon">✕</span>
</button>
<div class="chat-window" id="chat-window">
  <div class="chat-header">
    <span>🤖 Investment Preference Finder</span>
    <div class="chat-header-btns">
      <button class="chat-header-btn" onclick="restartChat()" title="Restart">🔄</button>
      <button class="chat-header-btn" onclick="toggleChat()" title="Close">✕</button>
    </div>
  </div>
  <div class="chat-body">
    <div class="chat-messages" id="chat-messages"></div>
    <div class="chat-options" id="chat-options"></div>
    <div class="chat-result" id="chat-result" style="display:none"></div>
  </div>
</div>

</body></html>'''


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        path = parsed.path
        if path == "/" or path == "":
            view = params.get("view", ["all"])[0]
            entity_id = params.get("id", [None])[0]
            top_n = int(params.get("top", [10000])[0])
            if view in ("founder", "investor") and entity_id:
                html = render_page(view=view, entity_id=entity_id, top_n=top_n)
            else:
                html = render_page(view="all", top_n=top_n)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())
        elif path == "/api/matches":
            matches = find_top_matches(founders, investors, top_n=10000, min_score=65)
            data = [{"rank": i+1, "founder": m.founder.company, "investor": m.investor.firm, "score": m.total_score} for i, m in enumerate(matches)]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()
    def log_message(self, *a): pass

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--host", type=str, default="0.0.0.0")
    args = p.parse_args()
    server = HTTPServer((args.host, args.port), Handler)
    print(f"🚀 AI Venture Intel v3 → http://localhost:{args.port}")
    server.serve_forever()
