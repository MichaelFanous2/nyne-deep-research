# Nyne Deep Research

Comprehensive person intelligence tool that combines multiple data sources into a single, actionable dossier.

---

## Best Practices for Agents

> **For best results, always provide BOTH email AND LinkedIn URL when available.**

| Input | Data Quality | What You Get |
|-------|--------------|--------------|
| Email only | Good | Basic enrichment, may find social profiles |
| LinkedIn only | Good | Profile data, posts, may find email |
| **Email + LinkedIn** | **Best** | **Highest match confidence, all data sources, fastest** |

**Key guidance for AI agents:**
1. **Always try to get LinkedIn URL** - It's the richest source of career/education data
2. **Email improves match accuracy** - Especially for common names
3. **Twitter or Instagram unlocks psychographics** - Pass via `--twitter` or `--instagram`
4. **Name/Company are auto-extracted** - No need to pass these manually

---

## For Claude Code & AI Agents

### Extracting More Data from Raw Response

When you run with `--json` flag, the raw response contains a `social_profiles` object with URLs to many platforms. You can fetch these for additional context:

```json
"social_profiles": {
  "twitter": { "url": "https://twitter.com/username", "followers": 5000 },
  "strava": { "url": "https://www.strava.com/athletes/12345" },
  "pinterest": { "url": "https://pinterest.com/username" },
  "flickr": { "url": "https://flickr.com/people/username" },
  "github": { "url": "https://github.com/username" },
  "foursquare": { "url": "https://foursquare.com/user/12345" },
  "angellist": { "url": "https://angel.co/username" }
}
```

**What you can do with these:**
| Profile | What to Fetch | Insights Gained |
|---------|---------------|-----------------|
| **Strava** | Activity feed | Cycling/running habits, fitness level, routes |
| **Pinterest** | Boards & pins | Personal interests, aesthetics, hobbies |
| **Flickr** | Photo albums | Photography interests, travel history |
| **GitHub** | Repos, contributions | Technical skills, side projects, open source |
| **Foursquare** | Check-ins | Favorite restaurants, travel patterns |
| **AngelList** | Investments, roles | Startup involvement, investment thesis |

### Workflow for Maximum Depth

```
1. Run deep_research.py with --json to get raw data
2. Parse social_profiles from the response
3. For each profile URL found:
   - Fetch the page (WebFetch or browser)
   - Extract relevant data (activities, posts, interests)
4. Feed additional context back into analysis
```

### Key Fields in Raw Response

The enrichment response includes rich data you can use:

```
result.social_profiles    → URLs to 20+ platforms
result.newsfeed          → Recent LinkedIn posts with full text
result.recommendations   → LinkedIn recommendations (how others see them)
result.volunteering      → Causes they care about
result.interests         → Skills, companies, keywords
result.automobiles       → Vehicle ownership (yes, really)
result.address           → Location data
result.birthday          → Birth date if available
```

---

## What It Does

Given an email and/or LinkedIn URL, this tool:

1. **Enriches** the person's profile (name, career, education, social profiles, recent posts)
2. **Analyzes** who they follow on Twitter/X and Instagram (psychographic profiling)
3. **Searches** for articles, podcasts, and press mentions
4. **Runs deep cluster analysis** - 5 parallel LLM calls to cluster followed accounts by:
   - Sports & Fitness (cycling, golf, basketball, etc.)
   - Entertainment & Culture (music, comedy, food, podcasts)
   - Causes & Politics (political leanings, social causes)
   - Personal Network (low-follower friends, family, colleagues)
   - Hidden Interests (unexpected follows, guilty pleasures)
5. **Generates** an AI-powered dossier with evidence-based insights

### How It Works

```
API Calls (3)           LLM Calls (13)                    Output (1)
─────────────           ──────────────                    ──────────
Enrichment    ────┐
Following     ────┼───► 7 Batch Analyses (75 accounts each)
Articles      ────┘     5 Cluster Analyses (parallel)    ───► dossier.md
                        1 Final Synthesis
```

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/yourrepo/nyne-deep-research.git
cd nyne-deep-research
pip install -r requirements.txt

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# 3. Run research (ideally with BOTH email and LinkedIn)
python deep_research.py \
  --email "ceo@company.com" \
  --linkedin "https://linkedin.com/in/ceo-profile" \
  --output dossier.md
```

## Installation

### Requirements
- Python 3.8+
- Nyne.ai API credentials
- At least one LLM API key (for dossier generation)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install requests python-dotenv google-generativeai
```

For alternative LLM providers:
```bash
pip install openai      # For OpenAI
pip install anthropic   # For Anthropic Claude
```

## Configuration

### Environment Variables

Create a `.env` file in the project root (or set these as environment variables):

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

## Usage

### Command Line

```bash
# IDEAL: Provide both email AND LinkedIn for best results
python deep_research.py \
  --email "john@company.com" \
  --linkedin "https://linkedin.com/in/johndoe" \
  --output dossier.md

# Minimum: At least email or LinkedIn required
python deep_research.py --email "john@company.com"
python deep_research.py --linkedin "https://linkedin.com/in/johndoe"

# With Twitter for psychographics (if you have it)
python deep_research.py \
  --email "john@company.com" \
  --linkedin "https://linkedin.com/in/johndoe" \
  --twitter "https://twitter.com/johndoe" \
  --output dossier.md

# Get raw JSON data (no LLM processing)
python deep_research.py --email "john@company.com" --json --output data.json

# Specify LLM provider
python deep_research.py --email "john@company.com" --llm openai

# Quiet mode (no progress output)
python deep_research.py --email "john@company.com" -q -o dossier.md
```

### Python API

```python
from deep_research import research_person

# IDEAL: Provide both email AND LinkedIn
result = research_person(
    email="ceo@startup.com",
    linkedin_url="https://linkedin.com/in/founder"
)
print(result['dossier'])

# With Twitter for psychographics
result = research_person(
    email="ceo@startup.com",
    linkedin_url="https://linkedin.com/in/founder",
    twitter_url="https://twitter.com/founder"
)

# Access raw data
print(result['data']['enrichment'])   # Profile, career, education, posts
print(result['data']['following'])     # Twitter psychographics
print(result['data']['articles'])      # Press mentions

# Skip dossier generation (just get data)
result = research_person(
    email="ceo@startup.com",
    generate_dossier_flag=False
)
```

## Output

### Dossier (Default)

The tool generates a comprehensive markdown dossier with 13 sections:

1. **Identity Snapshot** - Name, role, location, age, personal details (address, phone, car)
2. **Personal Life & Hobbies** - Active hobbies, entertainment tastes, causes, family indicators
3. **Career DNA** - Complete trajectory with insights for each role, their "superpower"
4. **Psychographic Profile** - Archetypes, values, beliefs, political leanings
5. **Social Graph Analysis** - Overview of professional network, personal interests, inner circle
6. **Interest Cluster Deep Dive** - Evidence-based analysis with specific handles:
   - Sports & Fitness (which sports, participant vs spectator)
   - Music & Entertainment (genres, artists, podcasts)
   - Causes & Politics (political figures, social causes)
   - Intellectual Interests (books, self-improvement)
   - Tech Interests (crypto, AI, consumer tech)
   - Geographic Ties (local community, hometown)
   - Personal Network (low-follower friends, family)
   - Unexpected/Surprising Follows
7. **Content & Voice Analysis** - Topics, communication style, recent wins/frustrations
8. **Key Relationships (Top 25)** - Most important accounts with relationship context
9. **Conversation Starters (30+)** - Professional hooks, personal interest hooks, shared experiences
10. **Recommendations & How Others See Them** - Patterns from LinkedIn recommendations
11. **Warnings & Landmines** - Sensitive topics, career sore spots, political hot buttons
12. **"Creepy Good" Insights** - Non-obvious patterns, cross-referenced discoveries
13. **Approach Strategy** - Best angle, shared connections, topics to reference

### Raw JSON (--json flag)

```json
{
  "enrichment": {
    "result": {
      "firstname": "John",
      "lastname": "Doe",
      "headline": "CEO at Acme Inc",
      "summary": "...",
      "careers_info": [...],
      "schools_info": [...],
      "social_profiles": {...},
      "newsfeed": [...]
    }
  },
  "following": {
    "result": {
      "interactions": [
        {
          "actor": {
            "username": "elonmusk",
            "display_name": "Elon Musk",
            "bio": "...",
            "followers_count": "180000000"
          },
          "relationship_type": "following"
        }
      ]
    }
  },
  "articles": {
    "result": {
      "articles": [
        {
          "title": "...",
          "url": "...",
          "source": "TechCrunch",
          "date": "2024-01-15"
        }
      ]
    }
  }
}
```

## What Each Input Unlocks

| Input | What It Unlocks | Why It Matters |
|-------|-----------------|----------------|
| **Email** | Match verification, work history, contact info | Confirms identity, especially for common names |
| **LinkedIn URL** | Full career history, education, posts, bio | Richest professional data source |
| **Twitter URL** | Who they follow (psychographics), tweets | Reveals interests, values, hidden hobbies |
| **Instagram URL** | Who they follow (psychographics) | Alternative to Twitter for following analysis |

### Auto-Discovery

The tool automatically extracts additional data from enrichment:

```
Email/LinkedIn → Enrichment → Extracts Name + Company → Article Search
                           → Finds Twitter URL → Following List (psychographics)
```

You don't need to pass `--name` or `--company` - they're extracted automatically from the enrichment response. Those flags only exist for edge cases where you want to search articles without doing enrichment first.

## API Reference

See [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for detailed documentation of all data fields.

### Nyne.ai Endpoints Used

| Endpoint | Purpose | Key Fields |
|----------|---------|------------|
| `POST /person/enrichment` | Person profile data | name, career, education, social, posts |
| `POST /person/interactions` | Twitter following list | who they follow, follower counts |
| `POST /person/articlesearch` | Press/podcast mentions | articles, interviews, media |

All endpoints are async - you submit a request and poll for results.

## Error Handling

The tool gracefully handles missing data:

- Missing API credentials: Shows helpful message with links
- Failed API calls: Skips that data source, continues with others
- No Twitter found: Skips psychographic analysis
- No articles found: Skips press section
- No LLM key: Returns raw data without dossier

No crashes - always returns whatever data is available.

## Examples

### Sales Research (Best Practice)

```bash
# Research a prospect - provide email + LinkedIn for best results
python deep_research.py \
  --email "vp-engineering@target-company.com" \
  --linkedin "https://linkedin.com/in/vp-engineering" \
  --output prospect_research.md
```

### Investor Research (Best Practice)

```bash
# Research a VC before a pitch - LinkedIn + email if you have it
python deep_research.py \
  --linkedin "https://linkedin.com/in/vc-partner" \
  --email "partner@vcfirm.com" \
  --output investor_dossier.md
```

### Batch Processing

```python
import csv
from deep_research import research_person

with open('leads.csv') as f:
    for row in csv.DictReader(f):
        # Pass email + linkedin when available
        result = research_person(
            email=row.get('email'),
            linkedin_url=row.get('linkedin_url'),
            twitter_url=row.get('twitter_url'),  # Optional
            generate_dossier_flag=False  # Just get data
        )
        # Process result...
```

## LLM Configuration

### Auto-Selection (Default)
The tool automatically selects an LLM based on which API keys are available:

```
Priority: Gemini → OpenAI → Anthropic
```

Just set whichever API key(s) you have, and the tool picks the first available.

### Force a Specific LLM
```bash
python deep_research.py --email "ceo@company.com" --llm gemini
python deep_research.py --email "ceo@company.com" --llm openai
python deep_research.py --email "ceo@company.com" --llm anthropic
```

### Supported Models

| Provider | Model | Max Output Tokens | Set via |
|----------|-------|-------------------|---------|
| **Gemini** | `gemini-3-flash-preview` | 65,536 | `GEMINI_API_KEY` |
| **OpenAI** | `gpt-4o` | 16,384 | `OPENAI_API_KEY` |
| **Anthropic** | `claude-sonnet-4` | 64,000 | `ANTHROPIC_API_KEY` |

### Changing the Model

To use a different model, edit the model name in `deep_research.py` (search for `_call_gemini`, `_call_openai`, or `_call_anthropic` functions).

### Skip LLM (Raw Data Only)
```bash
python deep_research.py --email "ceo@company.com" --json -o raw_data.json
```

## Cost Considerations

### Nyne.ai
- Check https://nyne.ai for current pricing
- See [API documentation](https://api.nyne.ai/documentation) for endpoint details
- Each research uses 1-3 API calls depending on available data

### LLM Costs (for dossier generation)

Each dossier uses **13 LLM calls**:
- 7 batch analyses (analyzing ~75 followed accounts each)
- 5 cluster analyses (sports, entertainment, causes, network, hidden interests)
- 1 final synthesis

Estimated costs per dossier:
- **Gemini 3 Flash**: ~$0.05-0.15 (recommended - fast and cheap)
- **GPT-4o**: ~$0.50-1.50 per dossier
- **Claude Sonnet**: ~$0.30-0.80 per dossier

Use `--json` flag to skip LLM costs and get raw data only.

## License

MIT License - see LICENSE file.

## Contributing

PRs welcome! Please open an issue first to discuss changes.
