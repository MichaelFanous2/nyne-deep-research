# Simulation Mode — API Specification

Technical spec for turning the simulation feature into a standalone API endpoint.

---

## Overview

Given a person identifier (email and/or LinkedIn URL) and a question, the simulation engine predicts how that person would respond. It returns a structured response with sentiment, a simulated first-person reply, confidence scoring, and supporting intelligence.

---

## Entry Point

### Python Function

```python
from deep_research import research_person

result = research_person(
    email="ceo@startup.com",                              # str | None — at least one required
    linkedin_url="https://linkedin.com/in/ceo",           # str | None — at least one required
    twitter_url="https://twitter.com/ceo",                # str | None — optional, improves quality
    instagram_url="https://instagram.com/ceo",            # str | None — optional, improves quality
    question="What do they think about AI replacing jobs?", # str — required for simulation mode
    llm="auto",                                            # "auto" | "gemini" | "openai" | "anthropic"
    verbose=False                                          # bool — log progress to stdout
)
```

### CLI Equivalent

```bash
python deep_research.py \
  --email "ceo@startup.com" \
  --linkedin "https://linkedin.com/in/ceo" \
  --question "What do they think about AI replacing jobs?" \
  --output simulation.md
```

---

## Request Schema (for the API)

```json
POST /v1/simulate

{
  "email": "ceo@startup.com",           // string | null — at least one of email/linkedin required
  "linkedin_url": "https://linkedin.com/in/ceo",  // string | null
  "twitter_url": null,                   // string | null — optional
  "instagram_url": null,                 // string | null — optional
  "question": "What do they think about AI replacing jobs?",  // string — required
  "llm": "auto"                          // "auto" | "gemini" | "openai" | "anthropic" — optional
}
```

**Validation:**
- At least one of `email` or `linkedin_url` must be provided
- `question` is required (non-empty string)

---

## Response Schema

### Return Value from `research_person()`

```python
{
    "data": {
        "enrichment": { ... },         # Raw Nyne.ai enrichment response
        "following_twitter": { ... },  # Raw Twitter engagement data
        "following_instagram": { ... }, # Raw Instagram engagement data
        "articles": { ... }            # Raw article search results
    },
    "simulation": "## 1. AT A GLANCE\n\n**Question:** ..."   # Markdown string — the full simulation output
}
```

Note: When `question` is provided, the key is `"simulation"`. Without `question`, it's `"dossier"`.

### Simulation Output Structure (Markdown)

The `simulation` field is a markdown string with these sections in order:

#### Section 1: AT A GLANCE

Always present. Two possible formats:

**When sufficient signal exists:**

```markdown
## 1. AT A GLANCE

**Question:** "What do they think about AI replacing jobs?"
**Sentiment:** Strongly Positive | Positive | Leaning Positive | Neutral | Leaning Negative | Negative | Strongly Negative
**Short Answer:** 1-2 sentence plain-English summary of their likely position.
**Conviction Level:** Passionate | Firm | Moderate | Ambivalent | Indifferent
**Confidence:** High | Medium | Low — brief reason
**Key Drivers:**
*   Bullet point 1
*   Bullet point 2
*   Bullet point 3
```

**When insufficient signal (can't answer the question from data):**

```markdown
## 1. AT A GLANCE

**Question:** "What is their favorite sock brand?"
**Sentiment:** Insufficient Data
**Short Answer:** We don't have enough signal to predict this person's stance on this topic.
**Conviction Level:** Unknown
**Confidence:** Insufficient Data — explanation of what's missing

**What we looked for but didn't find:**
*   ...

**What we CAN say:**
*   ...

**How to find out:**
*   ...
```

When `Sentiment` is `Insufficient Data`, sections 2-6 are **not present**.

#### Section 2: SIMULATED RESPONSE (only when sufficient signal)

First-person dialogue written in the person's communication style and tone.

```markdown
## 2. SIMULATED RESPONSE

"Look, you have to separate the noise from the signal..."
```

#### Section 3: CONFIDENCE ASSESSMENT (only when sufficient signal)

```markdown
## 3. CONFIDENCE ASSESSMENT

**What we're most sure about:**
*   [Insight] — [why]

**Probable but less certain:**
*   [Insight] — [reasoning]

**Educated guesses:**
*   [Insight] — [why speculative]

**Blind spots:**
*   What we don't know
```

#### Section 4: INTELLIGENCE BRIEF (only when sufficient signal)

```markdown
## 4. INTELLIGENCE BRIEF

**Direct Connections:**
*   ...

**Contextual Signals:**
*   ...

**Inferred Leanings:**
*   ...
```

#### Section 5: PSYCHOGRAPHIC REASONING (only when sufficient signal)

Narrative explanation of their worldview and why they'd respond this way.

#### Section 6: CONVERSATION PLAYBOOK (only when sufficient signal)

```markdown
## 6. CONVERSATION PLAYBOOK

**Best way to bring this up:**
*   ...

**What they'd engage with:**
*   ...

**Landmines to avoid:**
*   ...

**Predicted follow-up questions they'd ask YOU:**
*   ...
```

---

## Structured Fields for API Parsing

If building a JSON API, parse the following fields from the AT A GLANCE section:

| Field | Type | Values | Notes |
|-------|------|--------|-------|
| `sentiment` | string | `Strongly Positive`, `Positive`, `Leaning Positive`, `Neutral`, `Leaning Negative`, `Negative`, `Strongly Negative`, `Insufficient Data` | Primary signal |
| `short_answer` | string | Free text, 1-2 sentences | Human-readable summary |
| `conviction_level` | string | `Passionate`, `Firm`, `Moderate`, `Ambivalent`, `Indifferent`, `Unknown` | How strongly they hold this view |
| `confidence` | string | `High`, `Medium`, `Low`, `Insufficient Data` | Our confidence in the prediction |
| `is_sufficient_signal` | boolean | Derived: `true` if sentiment != `Insufficient Data` | Whether we could answer the question |

**Regex parsing hint** (for extracting structured fields from markdown):

```python
import re

def parse_at_a_glance(simulation_md: str) -> dict:
    """Extract structured fields from simulation markdown."""
    result = {}
    for line in simulation_md.split("\n"):
        line = line.strip()
        if line.startswith("**Sentiment:**"):
            result["sentiment"] = line.split("**Sentiment:**")[1].strip()
        elif line.startswith("**Short Answer:**"):
            result["short_answer"] = line.split("**Short Answer:**")[1].strip()
        elif line.startswith("**Conviction Level:**"):
            result["conviction_level"] = line.split("**Conviction Level:**")[1].strip()
        elif line.startswith("**Confidence:**"):
            result["confidence"] = line.split("**Confidence:**")[1].strip().split(" — ")[0]
    result["is_sufficient_signal"] = result.get("sentiment") != "Insufficient Data"
    return result
```

---

## Pipeline Internals

### Phases

| Phase | What Happens | LLM Calls | Time |
|-------|-------------|-----------|------|
| **0. Question Analysis** | Analyzes the question to determine which data clusters matter and which to skip | 1 | ~8-12s |
| **1. Data Collection** | Nyne.ai API calls for enrichment, social data, articles | 0 (API only) | ~30-80s |
| **2. Batch Analysis** | Analyzes social graph in batches of 75, with question-focused injection | 5-7 | ~20-40s |
| **3. Cluster Analysis** | Deep analysis by category (sports, entertainment, causes, network, hidden). Irrelevant clusters are skipped based on Phase 0. | 3-5 | ~20-25s |
| **4. Synthesis** | Combines all analyses into the simulation output using SIMULATION_SYNTHESIS_PROMPT | 1 | ~20s |
| **Total** | | 10-14 | ~2-3 min |

### Question-Adaptive Behavior

Phase 0 produces a `QuestionContext` that controls the rest:

```python
@dataclass
class QuestionContext:
    question: str
    cluster_priorities: Dict[str, str]   # "critical" | "useful" | "skip"
    specific_signals: list               # e.g. ["political commentators", "news outlets"]
    additional_focus: str                # extra prompt instructions for critical clusters
    enrichment_focus: list               # which enrichment fields matter most
```

**Cluster priority map:**

| Cluster Key | What It Analyzes |
|-------------|-----------------|
| `sports_fitness` | Sports teams, fitness, cycling, running, gym |
| `entertainment_culture` | Music, comedy, TV, podcasts, food, gaming |
| `causes_values` | Philanthropy, politics, education, environment |
| `personal_network` | Low-follower accounts, former colleagues, family |
| `hidden_interests` | Surprising or unexpected interests |

- `"critical"` clusters get extra question-focused prompt injection
- `"useful"` clusters run normally
- `"skip"` clusters are not executed (saves tokens + latency)

### Insufficient Signal Detection

The synthesis prompt includes strict rules for detecting when a question can't be answered from available data. The key test: **does the data contain DIRECT, SPECIFIC evidence, or are we extrapolating from vibes?**

Examples that trigger insufficient signal:
- "What's their favorite sock brand?" — lifestyle interests don't tell you specific brand preferences
- "What car do they drive?" — wealth signals don't tell you car brand
- "Do they prefer cats or dogs?" — no direct pet-related evidence

Examples that have sufficient signal:
- "What do they think about Trump?" — political connections, news diet, public stances
- "Are they into cycling?" — sports-related connections and activity profiles
- "How would they react to a cold pitch?" — their relationship to startups, sales, AI

---

## Dependencies

### External APIs

| API | Purpose | Required |
|-----|---------|----------|
| Nyne.ai (`NYNE_API_KEY` + `NYNE_API_SECRET`) | Person enrichment, social data, article search | Yes |
| Gemini / OpenAI / Anthropic (one key required) | All LLM analysis calls | Yes (at least one) |

### Python Packages

```
requests>=2.28.0
python-dotenv>=1.0.0
google-generativeai>=0.3.0   # if using Gemini
openai>=1.0.0                # if using OpenAI
anthropic>=0.18.0            # if using Anthropic
```

---

## Key Functions to Expose

| Function | Purpose | Signature |
|----------|---------|-----------|
| `research_person()` | Full pipeline — data collection + simulation | See entry point above |
| `deep_research()` | Data collection only (no LLM analysis) | `deep_research(input: ResearchInput) -> ResearchResults` |
| `generate_dossier()` | LLM analysis only (pass existing data) | `generate_dossier(results: ResearchResults, question: str) -> str` |
| `analyze_question()` | Question analysis only (Phase 0) | `analyze_question(question: str) -> QuestionContext` |

For the API, `research_person()` is the main entry point. The others are useful if you want to separate data collection from analysis (e.g., cache the data and re-run simulations with different questions).

---

## Tests

### Unit Tests (no API keys needed)

```bash
python tests/test_question_context.py
```

8 tests covering:
- `QuestionContext` dataclass creation
- Prompt formatting (question analyzer + simulation synthesis)
- `generate_dossier()` signature accepts `question` param
- Cluster skipping logic (skip/useful/critical)
- Batch prompt question injection
- JSON parsing resilience (handles markdown fences from LLM)
- Standard mode unchanged (no question = original behavior)

### Live Integration Tests (requires API keys)

```bash
python tests/test_simulation_live.py
```

4 tests:
- `analyze_question()` returns valid `QuestionContext` for multiple question types
- Question diversity — different questions produce different cluster priorities
- Full simulation pipeline with cached data
- Standard dossier mode still works

### End-to-End Tests (requires API keys)

```bash
# Sufficient signal test
python tests/test_keith_trump.py
# Output: tests/keith_trump_simulation.md

# Insufficient signal test
python tests/test_keith_socks.py
# Output: tests/keith_socks_simulation.md — should return "Insufficient Data"
```

---

## Suggested API Design

```
POST /v1/simulate
  → Request: { email, linkedin_url, question, ... }
  → Response: {
      person: { name, title, company },
      at_a_glance: {
        sentiment: "Strongly Positive",
        short_answer: "...",
        conviction_level: "Firm",
        confidence: "High",
        confidence_reason: "...",
        key_drivers: ["...", "..."],
        is_sufficient_signal: true
      },
      simulated_response: "Look, you have to...",   // first-person dialogue
      confidence_assessment: { ... },
      intelligence_brief: { ... },
      psychographic_reasoning: "...",
      conversation_playbook: { ... },
      raw_markdown: "## 1. AT A GLANCE\n..."        // full markdown for rendering
    }

POST /v1/simulate/batch
  → Request: { people: [{ email, linkedin_url }, ...], question: "..." }
  → Response: {
      results: [
        { person: {...}, at_a_glance: {...}, simulated_response: "...", ... },
        ...
      ],
      summary: {
        total: 10,
        completed: 9,
        sentiment_distribution: { "Strongly Positive": 3, "Positive": 4, ... }
      }
    }
```

---

## File Map

```
deep_research.py                    # Everything lives here
├── QuestionContext (dataclass)      # Line ~253 — question analysis result
├── QUESTION_ANALYZER_PROMPT        # Line ~694 — Phase 0 prompt
├── SIMULATION_SYNTHESIS_PROMPT     # Line ~1405 — Phase 4 prompt (with insufficient signal detection)
├── analyze_question()              # Line ~1693 — Phase 0 function
├── generate_dossier(..., question)  # Line ~1738 — Main pipeline (question-aware)
├── research_person(..., question)   # Line ~2480 — Programmatic API
└── main()                          # Line ~2225 — CLI with --question and --batch

tests/
├── test_question_context.py        # Unit tests (no API keys)
├── test_simulation_live.py         # Integration tests (requires keys)
├── test_keith_trump.py             # E2E: sufficient signal test
└── test_keith_socks.py             # E2E: insufficient signal test
```
