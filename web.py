#!/usr/bin/env python3
"""AI Venture Relationship Intelligence — Web UI (many-to-many, zero dependencies)."""
import sys
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import load_investors, load_founders
from src.matcher import (
    find_top_matches,
    find_top_matches_for_founder,
    find_top_matches_for_investor,
    get_all_matches_matrix,
)

# ── Load data once ──
investors = load_investors()
founders = load_founders()
investor_map = {i.id: i for i in investors}
founder_map = {f.id: f for f in founders}


def score_bar(val, width=100):
    color = "#22c55e" if val >= 75 else "#eab308" if val >= 55 else "#ef4444"
    return f'<div style="display:flex;align-items:center;gap:6px"><div style="width:{width}px;height:6px;background:#1e1e2e;border-radius:3px;overflow:hidden"><div style="width:{val}%;height:100%;background:{color};border-radius:3px"></div></div><span style="font-size:12px;color:#94a3b8">{val:.0f}</span></div>'


def badge(score):
    if score >= 75:
        return '<span style="padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600;background:rgba(239,68,68,.15);color:#ef4444">🔥 HOT</span>'
    elif score >= 65:
        return '<span style="padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600;background:rgba(234,179,8,.15);color:#eab308">⚡ WARM</span>'
    else:
        return '<span style="padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600;background:rgba(34,197,94,.15);color:#22c55e">✓ GOOD</span>'


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


def render_match_card(m, idx, show_entity="both"):
    sc = m.total_score
    sc_col = score_color(sc)

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
        f'<div style="display:flex;align-items:center;gap:8px;font-size:12px">'
        f'<div style="width:100px;color:#64748b;text-align:right;flex-shrink:0">{n}</div>'
        f'{score_bar(v, 80)}</div>'
        for n, v in dims
    )

    intros = "".join(f"<li style='font-size:12px;color:#64748b;padding:2px 0'>→ {p}</li>" for p in m.warm_intro_pathways)

    return f'''
<div class="match-card" data-score="{sc}" data-investor="{m.investor.firm}" data-founder="{m.founder.company}" style="background:#12121a;border:1px solid #1e1e2e;border-radius:12px;margin-bottom:12px;overflow:hidden">
  <div onclick="this.nextElementSibling.classList.toggle('open')" style="display:flex;justify-content:space-between;align-items:center;padding:16px 20px;cursor:pointer">
    <div style="font-size:13px;font-weight:700;color:#6366f1;min-width:35px">#{idx}</div>
    <div style="flex:1">
      <div style="font-size:15px;font-weight:600">{title}</div>
      <div style="color:#64748b;font-size:12px;margin-top:3px">{sub}</div>
    </div>
    <div style="display:flex;align-items:center;gap:10px">
      {badge(sc)}
      <div style="font-size:24px;font-weight:700;color:{sc_col};min-width:45px;text-align:right">{sc:.0f}</div>
    </div>
  </div>
  <div class="details" style="display:none;border-top:1px solid #1e1e2e;padding:20px;background:#0d0d14">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
      <div>
        <h4 style="font-size:12px;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:10px">🏢 Founder</h4>
        <p style="font-size:13px;line-height:1.6"><strong>{m.founder.name}</strong> — {m.founder.role}<br>{m.founder.background[:200]}<br><br><strong>Traction:</strong> {m.founder.traction[:200]}<br><strong>Brand:</strong> {m.founder.brand_positioning[:150]}</p>
      </div>
      <div>
        <h4 style="font-size:12px;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:10px">💰 Investor</h4>
        <p style="font-size:13px;line-height:1.6"><strong>{m.investor.name}</strong> — {m.investor.firm}<br>{m.investor.type} · {m.investor.check_size}<br><br><strong>Focus:</strong> {', '.join(m.investor.ai_focus)}<br><strong>Stages:</strong> {', '.join(m.investor.stage_focus)}<br><strong>Speed:</strong> {m.investor.decision_speed}</p>
      </div>
    </div>
    <div style="margin-top:16px">
      <h4 style="font-size:12px;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:10px">📊 Score Breakdown</h4>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">{scores_html}</div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:16px">
      <div>
        <h4 style="font-size:12px;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:10px">🎯 Intelligence</h4>
        <p style="font-size:13px;line-height:1.6"><strong>Meeting Acceptance:</strong> {m.meeting_acceptance_likelihood:.0f}%<br><strong>Investment Probability:</strong> {m.investment_probability:.0f}%<br><strong>Timing:</strong> {m.best_timing}<br><strong>Style:</strong> {m.ideal_communication_style}</p>
      </div>
      <div>
        <h4 style="font-size:12px;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:10px">🔗 Warm Intro Pathways</h4>
        <ul style="list-style:none;padding:0">{intros}</ul>
      </div>
    </div>
    <div style="margin-top:16px">
      <h4 style="font-size:12px;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:8px">📧 Draft Email</h4>
      <div style="background:#0a0a12;border:1px solid #1e1e2e;border-radius:8px;padding:14px;font-size:12px;line-height:1.6;color:#64748b;white-space:pre-wrap;font-family:monospace;max-height:180px;overflow-y:auto">{email_draft(m)}</div>
    </div>
  </div>
</div>'''


def render_page(view="all", entity_id=None, top_n=20):
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Determine matches based on view
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
        page_title = f"Top {len(matches)} Matches Across All"
        show_entity = "both"

    # Build founder/investor selector lists
    founder_options = "".join(
        f'<option value="{f.id}" {"selected" if entity_id == f.id else ""}>{f.company} ({f.name[:20]})</option>'
        for f in sorted(founders, key=lambda x: x.company)
    )
    investor_options = "".join(
        f'<option value="{i.id}" {"selected" if entity_id == i.id else ""}>{i.firm}</option>'
        for i in sorted(investors, key=lambda x: x.firm)
    )

    # Match cards
    cards = "".join(render_match_card(m, idx, show_entity) for idx, m in enumerate(matches, 1))

    # Stats
    avg_score = sum(m.total_score for m in matches) / len(matches) if matches else 0
    hot_count = sum(1 for m in matches if m.total_score >= 75)
    warm_count = sum(1 for m in matches if 65 <= m.total_score < 75)

    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>🤖 AI Venture Intel</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0a0f;color:#e2e8f0;min-height:100vh}}
.open{{display:block!important}}
select,input,button{{font-family:inherit}}
</style></head><body>

<div style="background:linear-gradient(135deg,#0f0f1a,#1a1033);border-bottom:1px solid #1e1e2e;padding:20px 0">
<div style="max-width:1200px;margin:0 auto;padding:0 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px">
<div>
<div style="font-size:22px;font-weight:700;background:linear-gradient(135deg,#6366f1,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent">🤖 AI Venture Intelligence</div>
<div style="color:#64748b;font-size:12px;margin-top:2px">Many-to-Many Match Engine · {len(founders)} founders · {len(investors)} investors · {len(founders)*len(investors)} pairs analyzed · {now}</div>
</div>
<div style="display:flex;gap:20px">
<div style="text-align:center"><div style="font-size:24px;font-weight:700;color:#6366f1">{len(matches)}</div><div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:1px">Matches</div></div>
<div style="text-align:center"><div style="font-size:24px;font-weight:700;color:#ef4444">{hot_count}</div><div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:1px">🔥 Hot</div></div>
<div style="text-align:center"><div style="font-size:24px;font-weight:700;color:#eab308">{warm_count}</div><div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:1px">⚡ Warm</div></div>
<div style="text-align:center"><div style="font-size:24px;font-weight:700;color:#22c55e">{avg_score:.0f}</div><div style="font-size:10px;color:#64748b;text-transform:uppercase;letter-spacing:1px">Avg Score</div></div>
</div></div></div>

<div style="max-width:1200px;margin:0 auto;padding:16px 24px;display:flex;gap:10px;flex-wrap:wrap;align-items:center;background:#0d0d14;border-bottom:1px solid #1e1e2e">
<button onclick="setView('all')" id="btn-all" class="vbtn" style="padding:7px 14px;border-radius:8px;border:1px solid {'#6366f1' if view=='all' else '#1e1e2e'};background:{'#6366f1' if view=='all' else '#12121a'};color:{'#fff' if view=='all' else '#e2e8f0'};cursor:pointer;font-size:12px;font-weight:600">All Matches</button>
<button onclick="setView('by-founder')" id="btn-founder" class="vbtn" style="padding:7px 14px;border-radius:8px;border:1px solid {'#6366f1' if view=='founder' else '#1e1e2e'};background:{'#6366f1' if view=='founder' else '#12121a'};color:{'#fff' if view=='founder' else '#e2e8f0'};cursor:pointer;font-size:12px;font-weight:600">By Founder</button>
<button onclick="setView('by-investor')" id="btn-investor" class="vbtn" style="padding:7px 14px;border-radius:8px;border:1px solid {'#6366f1' if view=='investor' else '#1e1e2e'};background:{'#6366f1' if view=='investor' else '#12121a'};color:{'#fff' if view=='investor' else '#e2e8f0'};cursor:pointer;font-size:12px;font-weight:600">By Investor</button>

<select id="entity-select" onchange="goToEntity()" style="display:{'block' if view in ('founder','investor') else 'none'};padding:7px 12px;border-radius:8px;border:1px solid #1e1e2e;background:#12121a;color:#e2e8f0;cursor:pointer;font-size:12px;min-width:250px">
<option value="">Select...</option>
{'<optgroup label="Founders">' + founder_options + '</optgroup>' if view == 'founder' else '<optgroup label="Investors">' + investor_options + '</optgroup>' if view == 'investor' else founder_options}
</select>

<input type="text" id="search" placeholder="🔍 Search..." style="flex:1;min-width:180px;padding:7px 12px;border-radius:8px;border:1px solid #1e1e2e;background:#12121a;color:#e2e8f0;font-size:12px;outline:none">
<select id="sort" style="padding:7px 12px;border-radius:8px;border:1px solid #1e1e2e;background:#12121a;color:#e2e8f0;cursor:pointer;font-size:12px">
<option value="score">Score ↓</option><option value="score-asc">Score ↑</option><option value="investor">Investor</option><option value="founder">Founder</option></select>
<select id="filter" style="padding:7px 12px;border-radius:8px;border:1px solid #1e1e2e;background:#12121a;color:#e2e8f0;cursor:pointer;font-size:12px">
<option value="all">All</option><option value="hot">🔥 Hot (75+)</option><option value="warm">⚡ Warm (65-74)</option><option value="good">✓ Good (55-64)</option></select>
<button onclick="document.querySelectorAll('.details').forEach(d=>d.classList.add('open'))" style="padding:7px 14px;border-radius:8px;border:1px solid #1e1e2e;background:#12121a;color:#e2e8f0;cursor:pointer;font-size:12px">Expand All</button>
<button onclick="document.querySelectorAll('.details').forEach(d=>d.classList.remove('open'))" style="padding:7px 14px;border-radius:8px;border:1px solid #1e1e2e;background:#12121a;color:#e2e8f0;cursor:pointer;font-size:12px">Collapse</button>
</div>

<div style="max-width:1200px;margin:0 auto;padding:16px 24px 40px">
<div style="font-size:16px;font-weight:600;margin-bottom:16px;color:#e2e8f0">{page_title}</div>
<div id="matches">{cards}</div>
</div>

<div style="text-align:center;padding:20px;color:#334155;font-size:11px;border-top:1px solid #1e1e2e">
AI Venture Intelligence v2.0 · {len(founders)} founders × {len(investors)} investors = {len(founders)*len(investors)} pairs · 14-dimension scoring · Many-to-many matching
</div>

<script>
function setView(v){{
  if(v==='all')window.location.href='/';
  else if(v==='by-founder'){{document.getElementById('entity-select').style.display='block';document.getElementById('entity-select').innerHTML='<option value="">Select founder...</option>{founder_options}';}}
  else if(v==='by-investor'){{document.getElementById('entity-select').style.display='block';document.getElementById('entity-select').innerHTML='<option value="">Select investor...</option>{investor_options}';}}
}}
function goToEntity(){{
  const v=document.getElementById('entity-select').value;
  if(!v)return;
  const isFounder=document.getElementById('entity-select').querySelector('option[value="'+v+'"]').closest('optgroup').label==='Founders';
  window.location.href='/?view='+(isFounder?'founder':'investor')+'&id='+v;
}}
document.getElementById('search').addEventListener('input',function(q){{
  const t=q.target.value.toLowerCase();
  document.querySelectorAll('.match-card').forEach(c=>{{c.style.display=c.textContent.toLowerCase().includes(t)?'':'none'}});
}});
document.getElementById('sort').addEventListener('change',function(v){{
  const c=document.getElementById('matches'),cards=[...c.children];
  cards.sort((a,b)=>{{
    if(v.target.value==='score')return b.dataset.score-a.dataset.score;
    if(v.target.value==='score-asc')return a.dataset.score-b.dataset.score;
    if(v.target.value==='investor')return a.dataset.investor.localeCompare(b.dataset.investor);
    return a.dataset.founder.localeCompare(b.dataset.founder);
  }});
  cards.forEach(x=>c.appendChild(x));
  [...c.children].forEach((x,i)=>{{const r=x.querySelector('div div');if(r)r.textContent='#'+(i+1)}});
}});
document.getElementById('filter').addEventListener('change',function(v){{
  const m=v.target.value;
  document.querySelectorAll('.match-card').forEach(c=>{{
    const s=parseFloat(c.dataset.score);
    c.style.display=(m==='all')?'':(m==='hot'&&s>=75)?'':(m==='warm'&&s>=65&&s<75)?'':(m==='good'&&s>=55&&s<65)?'':'none';
  }});
}});
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
            data = [
                {
                    "rank": i + 1,
                    "founder": {"id": m.founder.id, "company": m.founder.company, "name": m.founder.name, "stage": m.founder.stage},
                    "investor": {"id": m.investor.id, "firm": m.investor.firm, "name": m.investor.name, "type": m.investor.type},
                    "score": m.total_score,
                }
                for i, m in enumerate(matches)
            ]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode())

        elif path == "/api/founder":
            fid = params.get("id", [None])[0]
            if fid and fid in founder_map:
                matches = find_top_matches_for_founder(founder_map[fid], investors, top_n=20)
                data = [{"rank": i+1, "investor": m.investor.firm, "score": m.total_score} for i, m in enumerate(matches)]
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data, indent=2).encode())
            else:
                self.send_response(404)
                self.end_headers()

        elif path == "/api/investor":
            iid = params.get("id", [None])[0]
            if iid and iid in investor_map:
                matches = find_top_matches_for_investor(investor_map[iid], founders, top_n=20)
                data = [{"rank": i+1, "founder": m.founder.company, "score": m.total_score} for i, m in enumerate(matches)]
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data, indent=2).encode())
            else:
                self.send_response(404)
                self.end_headers()

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--host", type=str, default="0.0.0.0")
    args = p.parse_args()
    server = HTTPServer((args.host, args.port), Handler)
    print(f"🚀 AI Venture Intel UI → http://localhost:{args.port}")
    print(f"   {len(founders)} founders × {len(investors)} investors = {len(founders)*len(investors)} pairs")
    print(f"   Views: / (all) / ?view=founder&id=FOU-001 / ?view=investor&id=INV-015")
    print(f"   API: /api/matches / /api/founder?id=... /api/investor?id=...")
    server.serve_forever()
