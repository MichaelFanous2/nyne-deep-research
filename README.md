# Nyne Deep Research

Comprehensive person intelligence. Given an email or LinkedIn URL, Nyne Deep Research builds an evidence-based dossier on any person — their interests, values, personality, relationships, and how they think.

---

## What It Does

Nyne Deep Research aggregates data from multiple sources and runs 13 parallel AI analyses to produce a comprehensive intelligence profile. The output reads like a briefing from someone who truly knows this person.

**Standard Mode:** Full 12-section dossier — identity, personality, career, interests, relationships, conversation starters, and approach strategy.

**Simulation Mode:** Ask "How would this person respond to [question]?" and get a predicted response in their voice, backed by evidence and a confidence assessment.

---

## Best Practices

> **For best results, always provide BOTH email AND LinkedIn URL when available.**

| Input | Data Quality | What You Get |
|-------|--------------|--------------|
| Email only | Good | Basic enrichment, may discover additional profiles |
| LinkedIn only | Good | Profile data, posts, may find email |
| **Email + LinkedIn** | **Best** | **Highest match confidence, all data sources, fastest** |

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/yourrepo/nyne-deep-research.git
cd nyne-deep-research
pip install -r requirements.txt

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 3. Run research
python deep_research.py \
  --email "ceo@company.com" \
  --linkedin "https://linkedin.com/in/ceo-profile" \
  --output dossier.md
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required - Nyne.ai credentials
NYNE_API_KEY=your_key_here
NYNE_API_SECRET=your_secret_here

# At least one LLM key (for dossier generation)
GEMINI_API_KEY=your_gemini_key      # Recommended
OPENAI_API_KEY=your_openai_key      # Alternative
ANTHROPIC_API_KEY=your_anthropic_key # Alternative
```

### Getting API Keys

| Service | URL | Notes |
|---------|-----|-------|
| Nyne.ai | https://nyne.ai | Required for person data. See [API docs](https://api.nyne.ai/documentation) |
| Google Gemini | https://aistudio.google.com/apikey | Recommended LLM (fast, cheap) |
| OpenAI | https://platform.openai.com/api-keys | Alternative LLM |
| Anthropic | https://console.anthropic.com/ | Alternative LLM |

---

## Usage

### Standard Dossier

```bash
# Full dossier on a person
python deep_research.py \
  --email "john@company.com" \
  --linkedin "https://linkedin.com/in/johndoe" \
  --output dossier.md

# Raw JSON data (no AI analysis)
python deep_research.py --email "john@company.com" --json --output data.json

# Specify LLM provider
python deep_research.py --email "john@company.com" --llm openai
```

### Simulation Mode

Ask how someone would respond to a specific question:

```bash
# Single person
python deep_research.py \
  --email "ceo@company.com" \
  --question "What do they think about AI replacing jobs?" \
  --output simulation.md

# The output includes:
# 1. AT A GLANCE — sentiment, short answer, confidence, key drivers
# 2. SIMULATED RESPONSE — first-person dialogue in their voice
# 3. CONFIDENCE ASSESSMENT — what we're sure about vs. speculative
# 4. INTELLIGENCE BRIEF — supporting evidence
# 5. PSYCHOGRAPHIC REASONING — why they think this way
# 6. CONVERSATION PLAYBOOK — how to bring this up with them
```

### Batch Simulation

Run the same question across a list of people:

```bash
# From a CSV
python deep_research.py \
  --batch people.csv \
  --question "How would they react to a cold pitch about our AI startup?" \
  --batch-output results/

# From a plain text file
python deep_research.py \
  --batch emails.txt \
  --question "What do they think about AI?" \
  --batch-output results/
```

**Output:**
- `results/_summary.csv` — Spreadsheet with name, sentiment, and short answer for each person
- `results/_summary.md` — Markdown table with links to individual reports
- `results/Person_Name.md` — Full simulation for each person

**CSV format:**
```csv
email,linkedin
ceo@company1.com,https://linkedin.com/in/ceo1
vp@company2.com,https://linkedin.com/in/vp2
```

Optional columns: `twitter`, `instagram`

**TXT format** (one email or LinkedIn URL per line):
```
ceo@company1.com
https://linkedin.com/in/vp2
partner@vcfirm.com
# Lines starting with # are ignored
```

### Python API

```python
from deep_research import research_person

# Standard dossier
result = research_person(
    email="ceo@startup.com",
    linkedin_url="https://linkedin.com/in/founder"
)
print(result['dossier'])

# Simulation mode
result = research_person(
    email="ceo@startup.com",
    question="What do they think about remote work?"
)
print(result['simulation'])

# Raw data only
result = research_person(
    email="ceo@startup.com",
    generate_dossier_flag=False
)
print(result['data'])
```

---

## Output

### Dossier (Default)

A comprehensive markdown dossier with 12 sections:

1. **Identity Snapshot** — Name, role, location, contact info, social profiles
2. **Personal Life & Hobbies** — Active hobbies, entertainment tastes, causes, family indicators
3. **Career DNA** — Complete trajectory with insights for each role
4. **Psychographic Profile** — Archetypes, values, beliefs, aspirations
5. **Social Graph Analysis** — Professional network, personal interests, inner circle
6. **Interest Cluster Deep Dive** — Evidence-based analysis across sports, entertainment, causes, tech, and more
7. **Content & Voice Analysis** — Topics, communication style, humor, opinions
8. **Key Relationships (Top 25)** — Most important connections with context
9. **Conversation Starters (30+)** — Professional, personal, and shared-experience hooks
10. **Recommendations** — How others describe them
11. **"Creepy Good" Insights** — Non-obvious patterns and cross-referenced discoveries
12. **Approach Strategy** — Best angle, topics to reference, what NOT to do

### Simulation Output

When using `--question`, the output is restructured:

1. **At a Glance** — Sentiment, short answer, conviction level, confidence rating, key drivers
2. **Simulated Response** — First-person dialogue in their communication style
3. **Confidence Assessment** — What's high-confidence vs. speculative
4. **Intelligence Brief** — Supporting evidence organized by signal strength
5. **Psychographic Reasoning** — Why they'd think this way
6. **Conversation Playbook** — How to bring this up, what to avoid, predicted follow-ups

**Insufficient Signal Detection:** If the question can't be answered from available data (e.g., "What's their favorite sock brand?"), the system detects this and returns an honest "insufficient data" response instead of hallucinating.

---

## What Each Input Unlocks

| Input | What It Provides |
|-------|-----------------|
| **Email** | Identity verification, work history, contact info |
| **LinkedIn URL** | Career history, education, posts, bio, recommendations |
| **Twitter URL** | Psychographic profiling, interest mapping, personality signals |
| **Instagram URL** | Alternative psychographic profiling |

The tool automatically discovers additional profiles from the initial enrichment — you don't need to manually provide all social URLs.

---

## LLM Configuration

### Auto-Selection (Default)
```
Priority: Gemini → OpenAI → Anthropic
```

### Supported Models

| Provider | Model | Notes |
|----------|-------|-------|
| **Gemini** | `gemini-3-flash-preview` | Recommended — fast and cheap |
| **OpenAI** | `gpt-4o` | Alternative |
| **Anthropic** | `claude-sonnet-4` | Alternative |

### Cost Estimates

Each dossier runs **13 parallel AI analyses**:

- **Gemini**: ~$0.05-0.15 per dossier (recommended)
- **GPT-4o**: ~$0.50-1.50 per dossier
- **Claude Sonnet**: ~$0.30-0.80 per dossier

Simulation mode may use fewer analyses (irrelevant clusters are skipped), reducing cost.

Use `--json` to skip AI analysis entirely and get raw data only.

---

## Error Handling

The tool gracefully handles missing data:

- Missing API credentials → helpful setup message
- Failed API calls → skips that source, continues with others
- No social profiles found → skips psychographic analysis
- No articles found → skips press section
- No LLM key → returns raw data without dossier

No crashes — always returns whatever data is available.

---

## License

MIT License — see LICENSE file.

## Contributing

PRs welcome! Please open an issue first to discuss changes.
