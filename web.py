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

investors = load_investors()
founders = load_founders()
investor_map = {i.id: i for i in investors}
founder_map = {f.id: f for f in founders}


def extract_country(location):
    loc = location.lower().strip()
    for kw, country in [
        (["san francisco","new york","palo alto","seattle","houston","boston","canton","emeryville","us"], "US"),
        (["uk","london"], "UK"), (["paris","france"], "France"),
        (["warsaw","poland"], "Poland"), (["india"], "India"),
        (["singapore"], "Singapore"), (["china"], "China"),
        (["israel"], "Israel"), (["europe"], "Europe"),
    ]:
        if any(k in loc for k in kw): return country
    return "Other"

founder_countries = sorted(set(extract_country(f.location) for f in founders))
investor_countries = sorted(set(extract_country(i.geography) for i in investors))
all_countries = sorted(set(founder_countries + investor_countries))

def score_bar(val, width=100):
    color = "#22c55e" if val >= 75 else "#eab308" if val >= 55 else "#ef4444"
    return f'<div style="display:flex;align-items:center;gap:6px"><div style="width:{width}px;height:6px;background:var(--bar-bg);border-radius:3px;overflow:hidden"><div style="width:{val}%;height:100%;background:{color};border-radius:3px"></div></div><span class="score-num">{val:.0f}</span></div>'

def badge(score):
    if score >= 75: return '<span class="badge badge-hot">🔥 HOT</span>'
    elif score >= 65: return '<span class="badge badge-warm">⚡ WARM</span>'
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
        ("Industry", m.score.industry_alignment), ("Stage", m.score.stage_compatibility),
        ("Geography", m.score.geography_preference), ("Pedigree", m.score.founder_track_record),
        ("Traction", m.score.startup_traction), ("Growth", m.score.growth_velocity),
        ("Brand", m.score.brand_positioning), ("Comms", m.score.communication_style),
        ("Social Proof", m.score.social_proof), ("Response", m.score.investor_response_behavior),
        ("Portfolio", m.score.portfolio_similarity), ("Reputation", m.score.reputation_score),
        ("Relationship", m.score.relationship_proximity), ("Conversion", m.score.conversion_likelihood),
    ]

    scores_html = "".join(
        f'<div class="score-row"><div class="score-label">{n}</div>{score_bar(v, 80)}</div>'
        for n, v in dims
    )
    intros = "".join(f"<li class='intro-item'>→ {p}</li>" for p in m.warm_intro_pathways)

    return f'''
<div class="match-card" data-score="{sc}" data-investor="{m.investor.firm}" data-founder="{m.founder.company}" data-fcountry="{f_country}" data-icountry="{i_country}" data-uid="{uid}">
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
        <p><strong>{m.founder.name}</strong> — {m.founder.role}<br>{m.founder.background[:200]}<br><br><strong>Traction:</strong> {m.founder.traction[:200]}<br><strong>Brand:</strong> {m.founder.brand_positioning[:150]}<br><strong>Location:</strong> {m.founder.location}</p>
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

def render_page(view="all", entity_id=None, top_n=30):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    if view == "founder" and entity_id and entity_id in founder_map:
        f = founder_map[entity_id]
        matches = find_top_matches_for_founder(f, investors, top_n=top_n)
        page_title = f"Top {len(matches)} Investors for {f.company}"
        show_entity = "investor"
    elif view == "investor" and entity_id and entity_id in investor_map:
        inv = investor_map[entity_id]
        matches = find_top_matches_for_investor(inv, founders, top_n=top_n)
        page_title = f"Top {len(matches)} Founders for {inv.firm}"
        show_entity = "founder"
    else:
        matches = find_top_matches(founders, investors, top_n=top_n)
        page_title = f"Top {len(matches)} Matches"
        show_entity = "both"

    founder_opts = "".join(
        f'<option value="{f.id}" {"selected" if entity_id == f.id else ""}>{f.company} ({f.name[:20]})</option>'
        for f in sorted(founders, key=lambda x: x.company)
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
    hot = sum(1 for m in matches if m.total_score >= 75)
    warm = sum(1 for m in matches if 65 <= m.total_score < 75)

    # Build saved matches data for JS
    saved_data = json.dumps({match_uid(m): {"f": m.founder.company, "i": m.investor.firm, "s": m.total_score}
                             for m in find_top_matches(founders, investors, top_n=100)})

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

[data-theme="geeky"]{{
  --bg:#000;--bg2:#001100;--card:#001a00;--border:#00ff4133;
  --accent:#00ff41;--accent2:#39ff14;--text:#00ff41;--muted:#00aa2a;--dim:#005500;
  --bar-bg:#003300;--header-bg:linear-gradient(135deg,#000,#001a00);
  --btn-bg:#001a00;--btn-border:#00ff4133;--btn-active-bg:#00ff41;--btn-active-text:#000;
  --input-bg:#001a00;--input-border:#00ff4133;
  --badge-hot-bg:rgba(255,0,0,.2);--badge-hot-color:#ff0040;
  --badge-warm-bg:rgba(255,255,0,.15);--badge-warm-color:#ffff00;
  --badge-good-bg:rgba(0,255,65,.15);--badge-good-color:#00ff41;
  --email-bg:#000a00;--footer-color:#005500;--save-color:#ffff00;
  font-family:'VT323',monospace!important;
}}
[data-theme="geeky"] body,[data-theme="geeky"] *{{font-family:'VT323',monospace!important}}
[data-theme="geeky"] .match-card{{border:1px solid #00ff4133;text-shadow:0 0 5px #00ff4133}}
[data-theme="geeky"] .match-card:hover{{border-color:#00ff41;box-shadow:0 0 15px #00ff4122}}
[data-theme="geeky"] .match-name{{text-shadow:0 0 10px #00ff4155}}
[data-theme="geeky"] .match-score{{text-shadow:0 0 15px currentColor;font-size:28px!important}}
[data-theme="geeky"] .stat-num{{text-shadow:0 0 10px var(--accent)}}
[data-theme="geeky"] .logo{{background:linear-gradient(135deg,#00ff41,#39ff14);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:none;animation:glitch 2s infinite}}
[data-theme="geeky"] .email-draft{{border:1px solid #00ff4133;background:#000a00}}
[data-theme="geeky"] .match-card{{text-shadow:none}}
[data-theme="geeky"] .badge{{border:1px solid currentColor}}
[data-theme="geeky"] .details{{background:#000a00}}
[data-theme="geeky"] .save-btn{{color:var(--save-color);text-shadow:0 0 10px var(--save-color)}}
@keyframes glitch{{0%,100%{{transform:translate(0)}}20%{{transform:translate(-2px,2px)}}40%{{transform:translate(2px,-2px)}}60%{{transform:translate(-1px,1px)}}80%{{transform:translate(1px,-1px)}}}}

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
[data-theme="geeky"] .btn-theme:last-of-type{{animation:glitch 3s infinite}}
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
.footer{{text-align:center;padding:20px;color:var(--footer-color);font-size:11px;border-top:1px solid var(--border)}}
.page-title{{font-size:16px;font-weight:600;margin-bottom:16px}}
.saved-count{{position:absolute;top:-6px;right:-6px;background:var(--save-color);color:#000;border-radius:50%;width:18px;height:18px;font-size:10px;font-weight:700;display:flex;align-items:center;justify-content:center}}
.refresh-badge{{display:inline-block;padding:3px 8px;border-radius:6px;background:rgba(34,197,94,.15);color:#22c55e;font-size:10px;font-weight:600;margin-left:8px;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.5}}}}
@media(max-width:768px){{.details-grid,.scores-grid{{grid-template-columns:1fr}}.header-inner{{flex-direction:column;gap:12px}}.controls{{flex-direction:column}}}}
</style></head><body>

<div class="header">
<div class="header-inner">
<div>
<div class="logo">🤖 AI Venture Intelligence</div>
<div class="subtitle">Many-to-Many · {len(founders)} founders · {len(investors)} investors · {len(founders)*len(investors)} pairs · Last updated: {last_updated} <span class="refresh-badge">🔄 Auto-refreshes every 48h</span></div>
</div>
<div class="stats">
<div class="stat"><div class="stat-num">{len(matches)}</div><div class="stat-label">Matches</div></div>
<div class="stat"><div class="stat-num">{hot}</div><div class="stat-label">🔥 Hot</div></div>
<div class="stat"><div class="stat-num">{warm}</div><div class="stat-label">⚡ Warm</div></div>
<div class="stat"><div class="stat-num">{avg_score:.0f}</div><div class="stat-label">Avg</div></div>
</div></div></div>

<div class="controls">
<button class="btn btn-theme" id="btn-dark" onclick="setTheme('dark')">🌙 Dark</button>
<button class="btn btn-theme" id="btn-geeky" onclick="setTheme('geeky')">👾 Geeky</button>

<button class="btn" id="btn-all" onclick="window.location.href='/'">All Matches</button>
<button class="btn" id="btn-founder" onclick="showSelect('founder')">By Founder</button>
<button class="btn" id="btn-investor" onclick="showSelect('investor')">By Investor</button>
<button class="btn" id="btn-saved" onclick="filterSaved()" style="position:relative">⭐ Saved <span class="saved-count" id="saved-count" style="display:none">0</span></button>

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
<option value="all">All</option><option value="hot">🔥 Hot (75+)</option><option value="warm">⚡ Warm (65-74)</option><option value="good">✓ Good (55-64)</option></select>
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
  document.getElementById('btn-dark').classList.toggle('active',t==='dark');
  document.getElementById('btn-geeky').classList.toggle('active',t==='geeky');
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
  const n=Object.keys(getSaved()).length;
  const el=document.getElementById('saved-count');
  el.style.display=n>0?'flex':'none';
  el.textContent=n;
}}
// Init save buttons
(function(){{
  const s=getSaved();
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
  window.location.href='/?view='+(isF?'founder':'investor')+'&id='+v;
}}

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
    c.style.display=(m==='all')?'':(m==='hot'&&s>=75)?'':(m==='warm'&&s>=65&&s<75)?'':(m==='good'&&s>=55&&s<65)?'':'none';
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
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        path = parsed.path
        if path == "/" or path == "":
            view = params.get("view", ["all"])[0]
            entity_id = params.get("id", [None])[0]
            top_n = int(params.get("top", [30])[0])
            if view in ("founder", "investor") and entity_id:
                html = render_page(view=view, entity_id=entity_id, top_n=top_n)
            else:
                html = render_page(view="all", top_n=top_n)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode())
        elif path == "/api/matches":
            matches = find_top_matches(founders, investors, top_n=30)
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
