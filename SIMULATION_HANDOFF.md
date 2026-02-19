# Simulation API — Build Instructions

Hey! Here's everything you need to turn the simulation feature into an API endpoint.

---

## What We Built

We added a "simulation mode" to deep research. Instead of generating a generic dossier, you ask a specific question about a person and the system predicts how they'd respond — with a structured sentiment score, a first-person simulated response in their voice, confidence ratings, and a conversation playbook.

It works today as a CLI tool and Python function. Your job is to wrap it in an API.

---

## Step 1: Understand What Exists

Everything lives in one file: `deep_research.py`

The function you're wrapping:

```python
from deep_research import research_person

result = research_person(
    email="ceo@startup.com",
    linkedin_url="https://linkedin.com/in/ceo",
    question="What do they think about AI replacing jobs?",
    llm="auto",
    verbose=False
)

# result["simulation"] = markdown string with the full simulation
# result["data"] = raw enrichment/social/article data
```

That's it. One function call. It handles all data collection, LLM analysis, and output formatting internally.

---

## Step 2: Read the Full Spec

Open `SIMULATION_API_SPEC.md` in this repo. It has:
- Exact request/response schemas
- All structured fields you can parse from the output
- Pipeline internals (what happens under the hood, timing, costs)
- Suggested API design for both single and batch endpoints
- A Python regex helper for parsing structured fields from the markdown output
- Test files you can run to verify everything works

---

## Step 3: Build Two Endpoints

### `POST /v1/simulate`

**Request:**
```json
{
  "email": "ceo@startup.com",
  "linkedin_url": "https://linkedin.com/in/ceo",
  "twitter_url": null,
  "instagram_url": null,
  "question": "What do they think about AI?",
  "llm": "auto"
}
```

**Validation:**
- At least one of `email` or `linkedin_url` required
- `question` is required, non-empty

**Backend:** Call `research_person()` with those params. Parse the markdown output to extract structured fields.

**Response:**
```json
{
  "person": {
    "name": "Keith Rabois",
    "title": "Managing Partner",
    "company": "Khosla Ventures"
  },
  "at_a_glance": {
    "sentiment": "Strongly Positive",
    "short_answer": "Views AI as the most important...",
    "conviction_level": "Passionate",
    "confidence": "High",
    "is_sufficient_signal": true,
    "key_drivers": ["...", "..."]
  },
  "simulated_response": "Look, you have to...",
  "raw_markdown": "## 1. AT A GLANCE\n..."
}
```

The `at_a_glance` fields are parsed from the markdown. There's a parsing helper in the spec doc. `raw_markdown` is the full simulation output as-is for frontend rendering.

**Important:** When `sentiment` is `"Insufficient Data"`, there won't be a `simulated_response`. The system correctly detects when it can't answer a question (e.g., "What's their favorite sock brand?") and returns an honest "we don't know" instead of hallucinating.

### `POST /v1/simulate/batch`

**Request:**
```json
{
  "people": [
    {"email": "ceo@company1.com", "linkedin_url": "https://linkedin.com/in/ceo1"},
    {"email": "vp@company2.com"},
    {"linkedin_url": "https://linkedin.com/in/founder3"}
  ],
  "question": "How would they react to a cold pitch about our AI startup?",
  "llm": "auto"
}
```

**Backend:** Loop through `people`, call `research_person()` for each. Collect results.

**Response:**
```json
{
  "results": [
    {
      "person": {"name": "...", "title": "...", "company": "..."},
      "at_a_glance": {"sentiment": "Positive", "short_answer": "...", ...},
      "simulated_response": "...",
      "raw_markdown": "..."
    },
    ...
  ],
  "summary": {
    "total": 3,
    "completed": 3,
    "failed": 0,
    "sentiment_distribution": {"Strongly Positive": 1, "Positive": 1, "Neutral": 1}
  }
}
```

---

## Step 4: Key Things to Know

### Timing
Each simulation takes **2-3 minutes**. Most of that is Nyne.ai API calls + 10-14 parallel LLM calls. Consider:
- Making the endpoint async (return a job ID, poll for results)
- Or using webhooks for batch mode
- Caching: if the same person is simulated with different questions, the raw data collection can be reused — only the LLM analysis needs to rerun

### Costs Per Simulation
- Nyne.ai: 1-3 API calls per person
- Gemini (recommended): ~$0.05-0.15 per simulation
- OpenAI: ~$0.50-1.50 per simulation

### Environment Variables Needed
```
NYNE_API_KEY=...
NYNE_API_SECRET=...
GEMINI_API_KEY=...        # recommended
OPENAI_API_KEY=...        # alternative/fallback
ANTHROPIC_API_KEY=...     # alternative/fallback
```

### The Insufficient Signal Feature
This is important for the API. When someone asks a question we can't answer from the data (e.g., specific product preferences, personal minutiae), the system returns `"sentiment": "Insufficient Data"` instead of making something up. Your API should handle this as a distinct response type — it's a feature, not an error.

---

## Step 5: Test It

Run these before and after your changes to make sure nothing broke:

```bash
# Unit tests — no API keys needed, runs instantly
python tests/test_question_context.py

# Live tests — needs API keys, takes a few minutes
python tests/test_simulation_live.py

# End-to-end: sufficient signal (political question)
python tests/test_keith_trump.py
# → Output: tests/keith_trump_simulation.md

# End-to-end: insufficient signal (sock brand question)
python tests/test_keith_socks.py
# → Output: tests/keith_socks_simulation.md (should say "Insufficient Data")
```

---

## Step 6: Parsing Helper

Copy this into your API code to extract structured fields from the markdown:

```python
def parse_simulation(simulation_md: str) -> dict:
    """Parse structured fields from simulation markdown output."""
    result = {
        "sentiment": None,
        "short_answer": None,
        "conviction_level": None,
        "confidence": None,
        "confidence_reason": None,
        "is_sufficient_signal": True,
        "key_drivers": [],
        "simulated_response": None,
    }

    lines = simulation_md.split("\n")
    in_drivers = False
    in_response = False
    response_lines = []

    for line in lines:
        stripped = line.strip()

        # Parse AT A GLANCE fields
        if stripped.startswith("**Sentiment:**"):
            result["sentiment"] = stripped.split("**Sentiment:**")[1].strip()
            result["is_sufficient_signal"] = result["sentiment"] != "Insufficient Data"
        elif stripped.startswith("**Short Answer:**"):
            result["short_answer"] = stripped.split("**Short Answer:**")[1].strip()
        elif stripped.startswith("**Conviction Level:**"):
            result["conviction_level"] = stripped.split("**Conviction Level:**")[1].strip()
        elif stripped.startswith("**Confidence:**"):
            conf_raw = stripped.split("**Confidence:**")[1].strip()
            if " — " in conf_raw:
                result["confidence"], result["confidence_reason"] = conf_raw.split(" — ", 1)
            else:
                result["confidence"] = conf_raw
        elif stripped.startswith("**Key Drivers:**"):
            in_drivers = True
        elif in_drivers and stripped.startswith("*"):
            result["key_drivers"].append(stripped.lstrip("* ").strip())
        elif in_drivers and not stripped.startswith("*") and stripped:
            in_drivers = False

        # Parse simulated response section
        if stripped == "## 2. SIMULATED RESPONSE":
            in_response = True
            continue
        elif in_response and stripped.startswith("## 3."):
            in_response = False
            result["simulated_response"] = "\n".join(response_lines).strip()
        elif in_response:
            response_lines.append(line)

    # Handle case where response is the last section
    if in_response and response_lines:
        result["simulated_response"] = "\n".join(response_lines).strip()

    return result
```

---

## File Map

```
deep_research.py                 ← Everything lives here
SIMULATION_API_SPEC.md           ← Full technical spec (schemas, pipeline details, tests)
SIMULATION_HANDOFF.md            ← This file (you are here)
tests/
├── test_question_context.py     ← Unit tests (run first)
├── test_simulation_live.py      ← Integration tests
├── test_keith_trump.py          ← E2E: political question (sufficient signal)
└── test_keith_socks.py          ← E2E: sock brand question (insufficient signal)
```

---

## Questions?

The spec doc (`SIMULATION_API_SPEC.md`) has the full details — pipeline phases, timing, all possible field values, and the suggested API design. Start there if you need more depth on anything.
