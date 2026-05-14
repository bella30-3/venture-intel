# 🤖 AI Venture Relationship Intelligence Agent

> Identify the highest probability investor-founder matches based on credibility, investment behavior, relationship compatibility, startup traction, and communication patterns.

## What It Does

This agent analyzes AI founders and investors across **14 dimensions** to generate personalized match reports with:

- **Compatibility scores** (1-100) for each founder-investor pair
- **Detailed analysis** of why each match is strong
- **Risk assessment** and potential concerns
- **Meeting acceptance likelihood** and **investment probability** predictions
- **Personalized introduction email drafts** for each match
- **Warm introduction pathways** through mutual connections
- **Recommended communication style** and timing

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/venture-intel.git
cd venture-intel
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your SMTP credentials and recipients
```

### 3. Run

```bash
# Full pipeline: match → report → email
python main.py

# Match only (no email)
python main.py --match-only

# Top 5 matches only
python main.py --top 5

# Web UI (no email config needed, works standalone)
python web.py --port 8080
# Open http://localhost:8080

# Custom output path
python main.py --output my-report.md
```

## Project Structure

```
venture-intel/
├── main.py                          # Entry point — runs full pipeline
├── requirements.txt                 # Python dependencies
├── .env.example                     # Configuration template
├── .gitignore
├── README.md
│
├── src/
│   ├── __init__.py
│   ├── models.py                    # Data models (Investor, Founder, Match)
│   ├── matcher.py                   # Core matching engine (14-dimension scoring)
│   ├── report_generator.py          # Markdown & HTML report generation
│   ├── email_sender.py              # SMTP email delivery
│   └── data_loader.py               # JSON data loading
│
├── data/
│   ├── investors.json               # Investor profiles (15+ profiles)
│   └── founders.json                # Founder profiles (20+ profiles)
│
├── reports/                         # Generated daily reports
│   └── 2026-05-14-daily-digest.md
│
├── templates/                       # Email and report templates
│
└── .github/
    └── workflows/
        └── daily-report.yml         # GitHub Actions — runs daily at 9 AM UTC
```

## Scoring Dimensions

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| Industry Alignment | 15% | AI sub-sector match |
| Stage Compatibility | 12% | Check size vs. raise stage |
| Founder Track Record | 12% | Exits, big-tech pedigree, credentials |
| Startup Traction | 10% | Revenue, users, funding, pilots |
| Growth Velocity | 8% | Speed of development |
| Brand Positioning | 5% | Market positioning strength |
| Communication Style | 5% | Founder-investor compatibility |
| Social Proof | 5% | Media, endorsements, advisors |
| Investor Response | 5% | Historical response behavior |
| Portfolio Similarity | 5% | Overlap with existing portfolio |
| Reputation Score | 5% | Industry reputation |
| Relationship Proximity | 5% | Warm intro pathways |
| Conversion Likelihood | 3% | Meeting/investment probability |
| Geography | 5% | Geographic alignment |

## Adding Your Own Data

### Investors

Edit `data/investors.json`:

```json
{
  "id": "INV-016",
  "name": "Investor Name",
  "firm": "Fund Name",
  "type": "VC",
  "check_size": "$1M–$10M",
  "stage_focus": ["Seed", "Series A"],
  "ai_focus": ["AI infrastructure", "developer tools"],
  "geography": "US",
  "portfolio": ["Company A", "Company B"],
  "decision_speed": "Fast (days)",
  "communication_style": "Technical, direct",
  "response_behavior": "High for technical founders",
  "thought_leadership": "Active on Twitter, blog",
  "warm_intro_paths": ["Portfolio founders", "angels"],
  "reputation_score": 8,
  "last_activity": "2026-05 — Active investments"
}
```

### Founders

Edit `data/founders.json`:

```json
{
  "id": "FOU-021",
  "name": "Founder Name",
  "company": "Startup Name",
  "role": "CEO",
  "background": "Ex-Google, Stanford PhD",
  "stage": "Seed ($5M)",
  "ai_subsector": "AI agents for healthcare",
  "location": "San Francisco, US",
  "traction": "$5M raised, 10 enterprise pilots",
  "founder_pedigree": "Ex-Google AI, Stanford PhD in ML",
  "growth_velocity": "High",
  "brand_positioning": "Healthcare AI agent platform",
  "social_proof": "TechCrunch coverage",
  "communication_style": "Technical, healthcare-focused",
  "ideal_investor_profile": "Healthcare AI VCs",
  "warm_intro_needs": "Healthcare AI investors"
}
```

## GitHub Actions (Daily Automation)

The included GitHub Actions workflow runs every day at **9:00 AM UTC**:

1. Loads investor/founder data
2. Runs the matching engine
3. Generates the report
4. Sends email to configured recipients
5. Commits the report to the repository

### Setup Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description |
|--------|-------------|
| `SMTP_HOST` | SMTP server (e.g., `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (e.g., `587`) |
| `SMTP_USER` | Your email address |
| `SMTP_PASSWORD` | App password (not your main password) |
| `EMAIL_FROM` | Sender email |
| `EMAIL_TO` | Comma-separated recipients |

### Gmail Setup

1. Enable 2FA on your Google account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Generate a new app password for "Mail"
4. Use that password as `SMTP_PASSWORD`

### Manual Trigger

Go to **Actions → Daily AI Venture Intel Report → Run workflow**

## Extending the Agent

### Add New Data Sources

Create a new module in `src/` to fetch data from:

- Crunchbase API
- LinkedIn Sales Navigator
- Signal (NFX)
- PitchBook
- Twitter/X API

### Add AI-Enhanced Matching

The matching engine is rule-based by design (transparent, explainable). To add AI enhancement:

1. Add `openai` to `requirements.txt`
2. Create `src/ai_enhancer.py` to refine matches with GPT
3. Use the structured scores as input to generate richer rationale

### Add Web Dashboard

Create a simple Flask/Streamlit dashboard:

```bash
pip install streamlit
# Create app.py with Streamlit UI
streamlit run app.py
```

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your changes
4. Submit a pull request

---

**Built with ❤️ for the AI venture ecosystem**
