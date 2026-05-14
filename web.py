#!/usr/bin/env python3
"""AI Venture Relationship Intelligence — Web UI (zero dependencies)."""
import sys
import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_loader import load_investors, load_founders
from src.matcher import find_top_matches, calculate_match_score

# ── Load data once ──
investors = load_investors()
founders = load_founders()


def score_bar_html(val):
    filled = int(val / 10)
    color = "#22c55e" if val >= 75 else "#eab308" if val >= 55 else "#ef4444"
    return f'<div style="display:flex;align-items:center;gap:6px"><div style="width:100px;height:6px;background:#1e1e2e;border-radius:3px;overflow:hidden"><div style="width:{val}%;height:100%;background:{color};border-radius:3px"></div></div><span style="font-size:12px;color:#94a3b8">{val:.0f}</span></div>'


def email_draft(m):
    f, i = m.founder, m.investor
    return f"""Subject: {f.company} — {f.brand_positioning[:60]} × {i.firm}'s {i.focus_areas_display} Thesis

Hi {i.firm} Team,

I'm reaching out because I see strong alignment between {i.firm} and {f.company}.

{f.company} ({f.stage}) is building {f.ai_subsector}.
- {f.brand_positioning}
- {f.traction[:150]}
- Founder: {f.founder_pedigree[:150]}

Given {i.firm}'s focus on {i.focus_areas_display} and portfolio ({', '.join(i.portfolio[:3])}), this is a compelling fit.

Would you be open to a conversation with {f.name}?

Best,
[Your Name]"""


def render_page():
    matches = find_top_matches(founders, investors, top_n=10)
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    cards_html = ""
    for idx, m in enumerate(matches, 1):
        score = m.total_score
        badge_cls = "hot" if score >= 75 else "warm" if score >= 65 else "good"
        badge_label = "Hot" if score >= 75 else "Warm" if score >= 65 else "Good"
        score_cls = "#22c55e" if score >= 75 else "#eab308" if score >= 65 else "#ef4444"

        dims = [
            ("Industry Alignment", m.score.industry_alignment),
            ("Stage Compatibility", m.score.stage_compatibility),
            ("Geography", m.score.geography_preference),
            ("Founder Pedigree", m.score.founder_track_record),
            ("Traction", m.score.startup_traction),
            ("Growth Velocity", m.score.growth_velocity),
            ("Brand Positioning", m.score.brand_positioning),
            ("Communication", m.score.communication_style),
            ("Social Proof", m.score.social_proof),
            ("Response Behavior", m.score.investor_response_behavior),
            ("Portfolio Match", m.score.portfolio_similarity),
            ("Reputation", m.score.reputation_score),
            ("Relationship", m.score.relationship_proximity),
            ("Conversion", m.score.conversion_likelihood),
        ]

        scores_html = ""
        for name, val in dims:
            scores_html += f'<div style="display:flex;align-items:center;gap:8px;font-size:13px"><div style="width:140px;color:#64748b;text-align:right;flex-shrink:0">{name}</div>{score_bar_html(val)}</div>'

        intros_html = "".join(f"<li style='font-size:13px;color:#64748b;padding:3px 0'>→ {p}</li>" for p in m.warm_intro_pathways)

        cards_html += f'''
<div class="match-card" data-score="{score}" data-investor="{m.investor.firm}" data-founder="{m.founder.company}" style="background:#12121a;border:1px solid #1e1e2e;border-radius:12px;margin-bottom:16px;overflow:hidden;transition:border-color .2s">
  <div onclick="this.nextElementSibling.classList.toggle('open')" style="display:flex;justify-content:space-between;align-items:center;padding:20px 24px;cursor:pointer">
    <div style="font-size:14px;font-weight:700;color:#6366f1;min-width:40px">#{idx}</div>
    <div style="flex:1">
      <div style="font-size:16px;font-weight:600">{m.founder.company} ↔ {m.investor.firm}</div>
      <div style="color:#64748b;font-size:13px;margin-top:4px">{m.founder.name} · {m.founder.stage} · {m.founder.ai_subsector[:60]}</div>
    </div>
    <div style="display:flex;align-items:center;gap:12px">
      <span style="padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600;text-transform:uppercase;background:rgba({'239,68,68' if badge_cls=='hot' else '234,179,8' if badge_cls=='warm' else '34,197,94'},.15);color:{score_cls}">{badge_label}</span>
      <div style="font-size:28px;font-weight:700;color:{score_cls};min-width:50px;text-align:right">{score:.0f}</div>
    </div>
  </div>
  <div class="details" style="display:none;border-top:1px solid #1e1e2e;padding:24px;background:#0d0d14">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">
      <div>
        <h4 style="font-size:13px;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:12px">🏢 Founder</h4>
        <p style="font-size:14px;line-height:1.6"><strong>{m.founder.name}</strong> — {m.founder.role}<br>{m.founder.background[:200]}<br><br><strong>Traction:</strong> {m.founder.traction[:200]}<br><strong>Brand:</strong> {m.founder.brand_positioning[:150]}</p>
      </div>
      <div>
        <h4 style="font-size:13px;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:12px">💰 Investor</h4>
        <p style="font-size:14px;line-height:1.6"><strong>{m.investor.name}</strong> — {m.investor.firm}<br>{m.investor.type} · {m.investor.check_size}<br><br><strong>Focus:</strong> {', '.join(m.investor.ai_focus)}<br><strong>Stages:</strong> {', '.join(m.investor.stage_focus)}<br><strong>Speed:</strong> {m.investor.decision_speed}</p>
      </div>
    </div>
    <div style="margin-top:20px">
      <h4 style="font-size:13px;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:12px">📊 Score Breakdown</h4>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">{scores_html}</div>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:20px">
      <div>
        <h4 style="font-size:13px;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:12px">🎯 Match Intelligence</h4>
        <p style="font-size:14px;line-height:1.6"><strong>Meeting Acceptance:</strong> {m.meeting_acceptance_likelihood:.0f}%<br><strong>Investment Probability:</strong> {m.investment_probability:.0f}%<br><strong>Best Timing:</strong> {m.best_timing}<br><strong>Communication:</strong> {m.ideal_communication_style}</p>
      </div>
      <div>
        <h4 style="font-size:13px;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:12px">🔗 Warm Intro Pathways</h4>
        <ul style="list-style:none;padding:0">{intros_html}</ul>
      </div>
    </div>
    <div style="margin-top:20px">
      <h4 style="font-size:13px;text-transform:uppercase;letter-spacing:1px;color:#64748b;margin-bottom:8px">📧 Draft Email</h4>
      <div style="background:#0a0a12;border:1px solid #1e1e2e;border-radius:8px;padding:16px;font-size:13px;line-height:1.6;color:#64748b;white-space:pre-wrap;font-family:monospace;max-height:200px;overflow-y:auto">{email_draft(m)}</div>
    </div>
  </div>
</div>'''

    return f'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>🤖 AI Venture Intel</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0a0a0f;color:#e2e8f0;min-height:100vh}}
.open{{display:block!important}}
@media(max-width:768px){{.details-grid{{grid-template-columns:1fr!important}}}}
</style></head><body>

<div style="background:linear-gradient(135deg,#0f0f1a,#1a1033);border-bottom:1px solid #1e1e2e;padding:24px 0">
<div style="max-width:1200px;margin:0 auto;padding:0 24px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px">
<div>
<div style="font-size:24px;font-weight:700;background:linear-gradient(135deg,#6366f1,#8b5cf6);-webkit-background-clip:text;-webkit-text-fill-color:transparent">🤖 AI Venture Intelligence</div>
<div style="color:#64748b;font-size:13px;margin-top:2px">AI Founder ↔ Investor Match Engine · {now}</div>
</div>
<div style="display:flex;gap:24px">
<div style="text-align:center"><div style="font-size:28px;font-weight:700;color:#6366f1">{len(matches)}</div><div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px">Matches</div></div>
<div style="text-align:center"><div style="font-size:28px;font-weight:700;color:#6366f1">{len(investors)}</div><div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px">Investors</div></div>
<div style="text-align:center"><div style="font-size:28px;font-weight:700;color:#6366f1">{len(founders)}</div><div style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px">Founders</div></div>
</div></div></div>

<div style="max-width:1200px;margin:0 auto;padding:20px 24px;display:flex;gap:12px;flex-wrap:wrap;align-items:center">
<input type="text" id="search" placeholder="🔍 Search investors, founders, companies..." style="flex:1;min-width:200px;padding:8px 14px;border-radius:8px;border:1px solid #1e1e2e;background:#12121a;color:#e2e8f0;font-size:13px;outline:none">
<select id="sort" style="padding:8px 16px;border-radius:8px;border:1px solid #1e1e2e;background:#12121a;color:#e2e8f0;cursor:pointer;font-size:13px">
<option value="score">Score ↓</option><option value="score-asc">Score ↑</option><option value="investor">Investor</option><option value="founder">Founder</option></select>
<select id="filter" style="padding:8px 16px;border-radius:8px;border:1px solid #1e1e2e;background:#12121a;color:#e2e8f0;cursor:pointer;font-size:13px">
<option value="all">All</option><option value="hot">🔥 Hot (75+)</option><option value="warm">⚡ Warm (65-74)</option><option value="good">✓ Good (55-64)</option></select>
<button onclick="document.querySelectorAll('.details').forEach(d=>d.classList.add('open'))" style="padding:8px 16px;border-radius:8px;border:1px solid #1e1e2e;background:#12121a;color:#e2e8f0;cursor:pointer;font-size:13px">Expand All</button>
<button onclick="document.querySelectorAll('.details').forEach(d=>d.classList.remove('open'))" style="padding:8px 16px;border-radius:8px;border:1px solid #1e1e2e;background:#12121a;color:#e2e8f0;cursor:pointer;font-size:13px">Collapse All</button>
</div>

<div style="max-width:1200px;margin:0 auto;padding:0 24px 40px" id="matches">
{cards_html}
</div>

<div style="text-align:center;padding:24px;color:#334155;font-size:12px;border-top:1px solid #1e1e2e">
AI Venture Relationship Intelligence Agent v1.0 · {len(matches)} matches · {len(investors)} investors · {len(founders)} founders · 14-dimension scoring
</div>

<script>
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
  [...c.children].forEach((x,i)=>{{x.querySelector('div div').textContent='#'+(i+1)}});
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
        path = urlparse(self.path).path
        if path == "/" or path == "":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(render_page().encode())
        elif path == "/api/matches":
            matches = find_top_matches(founders, investors, top_n=10)
            data = [{"rank": i+1, "founder": m.founder.company, "investor": m.investor.firm, "score": m.total_score} for i, m in enumerate(matches)]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Quiet logs


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--host", type=str, default="0.0.0.0")
    args = p.parse_args()
    server = HTTPServer((args.host, args.port), Handler)
    print(f"🚀 AI Venture Intel UI → http://localhost:{args.port}")
    print(f"   {len(investors)} investors · {len(founders)} founders · {10} matches")
    print(f"   API: /api/matches")
    server.serve_forever()
