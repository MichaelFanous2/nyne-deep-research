#!/usr/bin/env python3
"""
Nyne Deep Research
==================
Comprehensive person intelligence by combining multiple Nyne.ai API endpoints
with LLM-powered dossier generation.

This tool aggregates data from:
1. Person Enrichment (demographics, career, social profiles, posts)
2. Person Interactions (who they follow on Twitter/X)
3. Person Article Search (press mentions, podcasts, interviews)

Then uses an LLM (Gemini, OpenAI, or Anthropic) to generate an intelligent dossier.

Usage:
    python deep_research.py --email "john@company.com"
    python deep_research.py --linkedin "https://linkedin.com/in/johndoe"
    python deep_research.py --email "john@company.com" --output dossier.md

Environment Variables Required:
    NYNE_API_KEY        - Your Nyne.ai API key
    NYNE_API_SECRET     - Your Nyne.ai API secret

    Plus ONE of the following LLM API keys (for dossier generation):
    GEMINI_API_KEY      - Google Gemini API key (recommended)
    OPENAI_API_KEY      - OpenAI API key
    ANTHROPIC_API_KEY   - Anthropic API key

Get your Nyne.ai API keys at: https://nyne.ai
"""

import argparse
import json
import os
import sys
import time
import warnings
import requests

# Suppress deprecation warning from google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, Any
from dataclasses import dataclass

# Try to load dotenv, but don't fail if not installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv is optional

# ============================================================================
# CONFIGURATION
# ============================================================================

NYNE_API_KEY = os.getenv("NYNE_API_KEY")
NYNE_API_SECRET = os.getenv("NYNE_API_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

NYNE_BASE_URL = "https://api.nyne.ai"

# Following cache file path (pre-fetched data)
FOLLOWING_CACHE_FILE = "/Users/michaelfanous/deep_research_test/nyne-deep-research/following_cache.json"

# Global cache (loaded once)
_following_cache = None


def load_following_cache() -> Dict:
    """Load the following cache file. Returns empty dict if not found."""
    global _following_cache
    if _following_cache is not None:
        return _following_cache

    if os.path.exists(FOLLOWING_CACHE_FILE):
        try:
            with open(FOLLOWING_CACHE_FILE) as f:
                _following_cache = json.load(f)
                return _following_cache
        except Exception:
            pass

    _following_cache = {}
    return _following_cache


def normalize_linkedin_username(url: str) -> str:
    """Extract LinkedIn username from URL."""
    if not url:
        return ""
    import re
    url = url.lower().strip().split("?")[0].rstrip("/")
    match = re.search(r'linkedin\.com/in/([^/]+)', url)
    return match.group(1) if match else ""


def lookup_following_from_cache(email: str = None, linkedin_url: str = None,
                                 twitter_url: str = None, instagram_url: str = None) -> Dict:
    """
    Look up following data from pre-fetched cache.
    Returns dict with 'twitter' and 'instagram' keys, each containing cached data or None.
    """
    cache = load_following_cache()
    if not cache:
        return {"twitter": None, "instagram": None}

    result = {"twitter": None, "instagram": None}

    # Try to find by email first
    if email:
        email_key = email.lower().strip()
        entry = cache.get("by_email", {}).get(email_key)
        if entry:
            # Found by email - now get Twitter/Instagram data
            cached_twitter_url = entry.get("twitter_url", "").lower() if entry.get("twitter_url") else ""
            cached_instagram_url = entry.get("instagram_url", "").lower() if entry.get("instagram_url") else ""

            if cached_twitter_url:
                twitter_entry = cache.get("by_twitter", {}).get(cached_twitter_url)
                if twitter_entry and twitter_entry.get("following"):
                    result["twitter"] = twitter_entry["following"]

            if cached_instagram_url:
                instagram_entry = cache.get("by_instagram", {}).get(cached_instagram_url)
                if instagram_entry and instagram_entry.get("following"):
                    result["instagram"] = instagram_entry["following"]

    # Try LinkedIn if email didn't find everything
    if linkedin_url and (result["twitter"] is None or result["instagram"] is None):
        linkedin_username = normalize_linkedin_username(linkedin_url)
        if linkedin_username:
            entry = cache.get("by_linkedin", {}).get(linkedin_username)
            if entry:
                cached_twitter_url = entry.get("twitter_url", "").lower() if entry.get("twitter_url") else ""
                cached_instagram_url = entry.get("instagram_url", "").lower() if entry.get("instagram_url") else ""

                if result["twitter"] is None and cached_twitter_url:
                    twitter_entry = cache.get("by_twitter", {}).get(cached_twitter_url)
                    if twitter_entry and twitter_entry.get("following"):
                        result["twitter"] = twitter_entry["following"]

                if result["instagram"] is None and cached_instagram_url:
                    instagram_entry = cache.get("by_instagram", {}).get(cached_instagram_url)
                    if instagram_entry and instagram_entry.get("following"):
                        result["instagram"] = instagram_entry["following"]

    # Direct lookup by Twitter URL if provided
    if result["twitter"] is None and twitter_url:
        twitter_key = twitter_url.lower().strip()
        twitter_entry = cache.get("by_twitter", {}).get(twitter_key)
        if twitter_entry and twitter_entry.get("following"):
            result["twitter"] = twitter_entry["following"]

    # Direct lookup by Instagram URL if provided
    if result["instagram"] is None and instagram_url:
        instagram_key = instagram_url.lower().strip()
        instagram_entry = cache.get("by_instagram", {}).get(instagram_key)
        if instagram_entry and instagram_entry.get("following"):
            result["instagram"] = instagram_entry["following"]

    return result


def check_setup():
    """Check if environment is configured and show setup instructions if not."""
    env_file_exists = os.path.exists(".env")
    has_nyne_keys = NYNE_API_KEY and NYNE_API_SECRET
    has_llm_key = GEMINI_API_KEY or OPENAI_API_KEY or ANTHROPIC_API_KEY

    if has_nyne_keys:
        return True  # All good

    # Show setup instructions
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                    SETUP REQUIRED                                ║
╚══════════════════════════════════════════════════════════════════╝

Welcome to Nyne Deep Research! Before you can use this tool, you need
to configure your API keys.

STEP 1: Create your .env file
─────────────────────────────
    cp .env.example .env

STEP 2: Get your Nyne.ai API keys
─────────────────────────────────
    Visit: https://nyne.ai
    Add to .env:
        NYNE_API_KEY=your_key_here
        NYNE_API_SECRET=your_secret_here

STEP 3: Get an LLM API key (for dossier generation)
───────────────────────────────────────────────────
    Choose ONE:
    • Gemini (recommended): https://aistudio.google.com/apikey
    • OpenAI: https://platform.openai.com/api-keys
    • Anthropic: https://console.anthropic.com/

    Add to .env:
        GEMINI_API_KEY=your_key_here

STEP 4: Run again
─────────────────
    python deep_research.py --email "someone@company.com"

""")
    if not env_file_exists:
        print("    TIP: No .env file found. Run: cp .env.example .env\n")

    return False


def get_headers() -> Optional[Dict[str, str]]:
    """Get API headers with authentication. Returns None if credentials missing."""
    if not NYNE_API_KEY or not NYNE_API_SECRET:
        return None
    return {
        "X-API-Key": NYNE_API_KEY,
        "X-API-Secret": NYNE_API_SECRET,
        "Content-Type": "application/json"
    }


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class ResearchInput:
    """Input for deep research - at least one identifier required."""
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    twitter_url: Optional[str] = None
    instagram_url: Optional[str] = None
    name: Optional[str] = None
    company: Optional[str] = None


@dataclass
class ResearchResults:
    """Container for all research data."""
    enrichment: Optional[Dict] = None
    following_twitter: Optional[Dict] = None
    following_instagram: Optional[Dict] = None
    articles: Optional[Dict] = None
    errors: Optional[Dict] = None


@dataclass
class QuestionContext:
    """Context derived from analyzing a simulation question."""
    question: str
    cluster_priorities: Dict[str, str]  # cluster_name -> "critical"/"useful"/"skip"
    specific_signals: list  # what to look for in following data
    additional_focus: str  # extra instructions to inject into cluster prompts
    enrichment_focus: list  # which enrichment fields matter most


# ============================================================================
# NYNE.AI API FUNCTIONS
# ============================================================================

def submit_enrichment(input_data: ResearchInput, headers: Dict) -> Optional[str]:
    """
    Submit person enrichment request.
    Returns request_id or None if failed.
    """
    payload = {
        "newsfeed": ["all"],
        "ai_enhanced_search": True
    }

    if input_data.email:
        payload["email"] = input_data.email
    if input_data.linkedin_url:
        payload["social_media_url"] = input_data.linkedin_url

    try:
        response = requests.post(
            f"{NYNE_BASE_URL}/person/enrichment",
            headers=headers,
            json=payload,
            timeout=30
        )
        data = response.json()
        if data.get("success") and data.get("data", {}).get("request_id"):
            return data["data"]["request_id"]
    except Exception:
        pass
    return None


def submit_following(social_url: str, headers: Dict, max_results: int = 500) -> Optional[str]:
    """
    Submit request to get who someone follows on Twitter/X or Instagram.
    Returns request_id or None if failed.

    Note: Instagram only supports 'following' type (not followers or replies).
    """
    if not social_url:
        return None

    try:
        response = requests.post(
            f"{NYNE_BASE_URL}/person/interactions",
            headers=headers,
            json={
                "type": "following",
                "social_media_url": social_url,
                "max_results": max_results
            },
            timeout=30
        )
        data = response.json()
        if data.get("success") and data.get("data", {}).get("request_id"):
            return data["data"]["request_id"]
    except Exception:
        pass
    return None


def submit_article_search(name: str, company: str, headers: Dict) -> Optional[str]:
    """
    Submit article search request.
    Returns request_id or None if failed.
    """
    if not name or not company:
        return None

    try:
        response = requests.post(
            f"{NYNE_BASE_URL}/person/articlesearch",
            headers=headers,
            json={
                "name": name,
                "company": company,
                "sort": "recent",
                "limit": 15
            },
            timeout=30
        )
        data = response.json()
        if data.get("success") and data.get("data", {}).get("request_id"):
            return data["data"]["request_id"]
    except Exception:
        pass
    return None


def poll_result(endpoint: str, request_id: str, headers: Dict,
                max_attempts: int = 60, delay: int = 5) -> Optional[Dict]:
    """
    Poll for async result.
    Returns result data or None if failed/timeout.
    """
    for _ in range(max_attempts):
        try:
            response = requests.get(
                f"{NYNE_BASE_URL}{endpoint}",
                headers=headers,
                params={"request_id": request_id},
                timeout=30
            )
            data = response.json()

            if not data.get("success"):
                return None

            result_data = data.get("data", {})
            status = result_data.get("status", "")

            if status == "completed":
                return result_data
            elif status == "failed":
                return None

            time.sleep(delay)
        except Exception:
            time.sleep(delay)

    return None


# ============================================================================
# MAIN RESEARCH FUNCTION
# ============================================================================

def deep_research(input_data: ResearchInput, verbose: bool = True) -> ResearchResults:
    """
    Execute deep research on a person using all available Nyne.ai endpoints.
    Gracefully handles missing data - never throws errors.
    Uses pre-fetched cache when available to skip live API calls.
    """
    results = ResearchResults(errors={})
    request_ids = {}

    # Check cache for pre-fetched following data
    cached_following = lookup_following_from_cache(
        email=input_data.email,
        linkedin_url=input_data.linkedin_url,
        twitter_url=input_data.twitter_url,
        instagram_url=input_data.instagram_url
    )
    cache_twitter_hit = cached_following.get("twitter") is not None
    cache_instagram_hit = cached_following.get("instagram") is not None


    # Apply cached data immediately
    if cache_twitter_hit:
        results.following_twitter = cached_following["twitter"]
    if cache_instagram_hit:
        results.following_instagram = cached_following["instagram"]

    # Check for API credentials
    headers = get_headers()
    if not headers:
        if verbose:
            print("⚠ Missing NYNE_API_KEY or NYNE_API_SECRET")
            print("  Set these environment variables or create a .env file")
            print("  Get your API keys at: https://nyne.ai")
        return results

    if verbose:
        print("=" * 60)
        print("NYNE DEEP RESEARCH")
        print("=" * 60)

    # -------------------------------------------------------------------------
    # PHASE 1: Submit requests
    # -------------------------------------------------------------------------
    if verbose:
        print("\n[1/3] Submitting API requests...")

    # Enrichment
    req_id = submit_enrichment(input_data, headers)
    if req_id:
        request_ids["enrichment"] = req_id
        if verbose:
            print("  ✓ Enrichment request submitted")
    elif verbose:
        print("  - Enrichment: skipped (no valid input)")

    # Twitter and/or Instagram following (for psychographics)
    # Skip if already have cached data
    if input_data.twitter_url and not results.following_twitter:
        req_id = submit_following(input_data.twitter_url, headers)
        if req_id:
            request_ids["following_twitter"] = req_id
            if verbose:
                print("  ✓ Social following request submitted")

    if input_data.instagram_url and not results.following_instagram:
        req_id = submit_following(input_data.instagram_url, headers)
        if req_id:
            request_ids["following_instagram"] = req_id
            if verbose:
                print("  ✓ Social following request submitted")

    # Article search
    if input_data.name and input_data.company:
        req_id = submit_article_search(input_data.name, input_data.company, headers)
        if req_id:
            request_ids["articles"] = req_id
            if verbose:
                print("  ✓ Article search submitted")

    if not request_ids:
        if verbose:
            print("\n  No requests submitted. Check your input.")
        return results

    # -------------------------------------------------------------------------
    # PHASE 2: Poll for results
    # -------------------------------------------------------------------------
    if verbose:
        print(f"\n[2/3] Waiting for {len(request_ids)} API results...")

    endpoint_map = {
        "enrichment": "/person/enrichment",
        "following_twitter": "/person/interactions",
        "following_instagram": "/person/interactions",
        "articles": "/person/articlesearch"
    }

    def poll_task(key: str, req_id: str) -> tuple:
        result = poll_result(endpoint_map[key], req_id, headers)
        return key, result

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(poll_task, key, req_id): key
            for key, req_id in request_ids.items()
        }

        for future in as_completed(futures):
            try:
                key, result = future.result()
                if result:
                    setattr(results, key, result)
                    if verbose:
                        print(f"  ✓ {key}: completed")
                elif verbose:
                    print(f"  - {key}: no data")
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # PHASE 3: Extract additional data from enrichment
    # -------------------------------------------------------------------------
    if results.enrichment:
        result_data = results.enrichment.get("result", {})

        # Extract name if not provided
        if not input_data.name:
            first = result_data.get("firstname", "")
            last = result_data.get("lastname", "")
            if first and last:
                input_data.name = f"{first} {last}"

        # Extract company if not provided
        if not input_data.company:
            careers = result_data.get("careers_info", [])
            if careers:
                input_data.company = careers[0].get("company_name", "")

        # Submit article search if we now have name/company
        if input_data.name and input_data.company and "articles" not in request_ids:
            if verbose:
                print(f"\n  → Found: {input_data.name} @ {input_data.company}")
                print("  → Fetching articles...")

            req_id = submit_article_search(input_data.name, input_data.company, headers)
            if req_id:
                result = poll_result("/person/articlesearch", req_id, headers)
                if result:
                    results.articles = result
                    if verbose:
                        print("  ✓ Article search: completed")

        # Extract Twitter and Instagram from enrichment if not already provided
        social_profiles = result_data.get("social_profiles", {})

        # Try Twitter if not already fetched
        if "following_twitter" not in request_ids and not results.following_twitter:
            twitter = social_profiles.get("twitter", {})
            twitter_url = twitter.get("url")

            if twitter_url:
                if verbose:
                    print(f"  → Found social profile")

                # Check cache first with the discovered Twitter URL
                cache_check = lookup_following_from_cache(twitter_url=twitter_url)
                if cache_check.get("twitter"):
                    results.following_twitter = cache_check["twitter"]
                else:
                    if verbose:
                        print("  → Fetching following list...")
                    req_id = submit_following(twitter_url, headers)
                    if req_id:
                        result = poll_result("/person/interactions", req_id, headers)
                        if result:
                            results.following_twitter = result
                            if verbose:
                                print("  ✓ Following list: completed")

        # Try Instagram if not already fetched
        if "following_instagram" not in request_ids and not results.following_instagram:
            instagram = social_profiles.get("instagram", {})
            instagram_url = instagram.get("url")

            if instagram_url:
                if verbose:
                    print(f"  → Found social profile")

                # Check cache first with the discovered Instagram URL
                cache_check = lookup_following_from_cache(instagram_url=instagram_url)
                if cache_check.get("instagram"):
                    results.following_instagram = cache_check["instagram"]
                else:
                    if verbose:
                        print("  → Fetching following list...")
                    req_id = submit_following(instagram_url, headers)
                    if req_id:
                        result = poll_result("/person/interactions", req_id, headers)
                        if result:
                            results.following_instagram = result
                            if verbose:
                                print("  ✓ Following list: completed")

    if verbose:
        print("\n[3/3] Research complete!")
        print("=" * 60)

    return results


# ============================================================================
# LLM DOSSIER GENERATION
# ============================================================================

DOSSIER_PROMPT = '''You are an elite intelligence analyst creating the most comprehensive dossier ever written on this person. Go DEEP. Leave no stone unturned.

RULES:
1. EVERY insight MUST cite specific evidence [e.g., "follows @handle (450K followers)", "posted on Dec 15: '...'"]
2. Use EXACT quotes, dates, follower counts, company names - be obsessively specific
3. Find the "creepy good" insights - patterns that show you did real research
4. Analyze their Twitter AND Instagram following lists thoroughly - cluster accounts, find unexpected follows
5. Cross-reference their posts with who they follow to infer deeper meaning
6. Note low-follower accounts they follow - these reveal personal relationships

WRITE A DEEPLY RESEARCHED DOSSIER WITH THESE SECTIONS:

## 1. IDENTITY SNAPSHOT
Full name, nicknames, current role, company, location, age estimate, languages. Include personal details like where they live if available.

## 2. CAREER DNA
Complete career trajectory with dates. For EACH role, explain:
- What they actually did (not just title)
- Why they likely made this move
- What skills/relationships they gained
Their "superpower" - what makes them uniquely valuable

## 3. PSYCHOGRAPHIC PROFILE
Analyze their Twitter/Instagram following to understand WHO they are:
- Core archetypes (Builder, Investor, Operator, Intellectual, etc.)
- Values and motivations (inferred from follows)
- Professional tribe and community affiliations
- CLUSTER ANALYSIS: Group the accounts they follow into categories with specific handles:
  - VCs & Investors: @handle1, @handle2...
  - Founders & Operators: ...
  - AI/Tech Researchers: ...
  - Media & Journalists: ...
  - Sports/Entertainment: ...
  - Personal/Friends: ...

## 4. HIDDEN INTERESTS & HOBBIES
Find the UNEXPECTED follows that reveal who they are outside work:
- Sports teams, athletes they follow
- Musicians, comedians, entertainers
- Niche interests (gaming, cooking, fitness, etc.)
- Low-follower accounts (<1000) - these are often personal friends or early relationships
Be specific with handles and why each is notable.

## 5. KEY INFLUENCERS (Top 20)
The 20 most notable/influential accounts they follow:
| Handle | Name | Followers | Why They Follow Them |
For each, explain the likely relationship or reason for following.

## 6. CONTENT ANALYSIS
From their LinkedIn posts and tweets:
- Topics they post about most
- Tone and communication style
- Recent wins they've celebrated (with dates and details)
- Frustrations or complaints they've expressed
- Opinions they've stated publicly
Include EXACT QUOTES from their posts.

## 7. CONVERSATION STARTERS (20+)
Highly specific hooks based on:
- Specific posts they made (with dates)
- Unusual accounts they follow
- Career transitions
- Hidden interests
- Recent news about their company
Each starter should feel like you KNOW them.

## 8. "CREEPY GOOD" INSIGHTS
The insights that make them think "how did they know that?":
- Patterns in who they follow
- Connections between their posts and follows
- Personal details buried in the data
- Things most people would miss

## 9. SUMMARY: How to Connect With This Person
A brief synthesis: what they care about, how they think, and the best angle to approach them.

---

HERE IS ALL THE RAW DATA TO ANALYZE:
{data}

Now write the most thorough dossier possible. Be exhaustive. Go deep.'''


# ============================================================================
# QUESTION ANALYZER PROMPT (Phase 0 for simulation mode)
# ============================================================================

QUESTION_ANALYZER_PROMPT = '''You are analyzing a question that someone wants to simulate asking a specific person.
Your job is to determine what data and analysis clusters are most relevant to predicting how this person would respond.

QUESTION: {question}

Respond in EXACTLY this JSON format (no markdown, no code fences, just raw JSON):
{{
    "cluster_priorities": {{
        "sports_fitness": "critical" or "useful" or "skip",
        "entertainment_culture": "critical" or "useful" or "skip",
        "causes_values": "critical" or "useful" or "skip",
        "personal_network": "critical" or "useful" or "skip",
        "hidden_interests": "critical" or "useful" or "skip"
    }},
    "specific_signals": [
        "list of specific types of accounts/follows to look for",
        "e.g. political commentators, programming language accounts, remote work advocates"
    ],
    "additional_focus": "A paragraph of additional analysis instructions to inject into the critical cluster prompts. Be specific about what sub-topics, opinions, or signals to extract that would help answer this question.",
    "enrichment_focus": [
        "list of enrichment fields that matter most",
        "e.g. posts, career_history, volunteering, articles, social_profiles"
    ]
}}

EXAMPLES:

Question: "What does this person think about Trump?"
→ causes_values: critical, hidden_interests: useful, entertainment_culture: skip, sports_fitness: skip
→ specific_signals: ["political commentators", "news outlets", "political figures", "partisan media", "political satire accounts"]
→ additional_focus: "Look for political orientation signals: which news outlets do they follow (Fox News vs MSNBC vs AP)? Do they follow any political figures, PACs, or advocacy organizations? Look for signals of libertarian, progressive, conservative, or centrist leanings. Check for political satire accounts which reveal orientation."

Question: "What does this person think about Rust vs Python?"
→ causes_values: skip, hidden_interests: useful, entertainment_culture: skip, sports_fitness: skip
→ specific_signals: ["programming language accounts", "developer tools", "tech thought leaders", "open source projects", "software engineering blogs"]
→ additional_focus: "Focus on technology preferences: which programming languages, frameworks, and developer tools appear in their follows? Do they follow Rust evangelists or Python data science accounts? Look for signals of systems programming vs scripting preferences, strong typing vs dynamic typing philosophy."

Question: "How would this person react to a cold outreach about our AI startup?"
→ causes_values: useful, hidden_interests: useful, entertainment_culture: skip, sports_fitness: skip
→ specific_signals: ["AI companies", "startup founders", "VC accounts", "sales/marketing accounts", "cold email tools"]
→ additional_focus: "Analyze their relationship to AI and startups: are they an AI optimist or skeptic? Do they follow AI companies or thought leaders? Have they posted about being pitched? Look for signals about how they feel about cold outreach, sales emails, and unsolicited pitches."

Now analyze the given question and return the JSON.'''


# ============================================================================
# BATCH ANALYSIS PROMPTS
# ============================================================================

BATCH_ANALYSIS_PROMPT = '''You are a behavioral psychologist analyzing WHO someone really is based on who they follow.

PERSON CONTEXT:
Name: {person_name}
Role: {person_role}
Company: {person_company}

ANALYZE THESE {batch_size} ACCOUNTS THEY FOLLOW (Batch {batch_num} of {total_batches}):
Format: @handle | Name | Followers | Bio

{batch_data}

For EACH account, categorize and analyze:
1. **Category** - Be specific:
   - Professional: VC, Founder, Tech Executive, AI Researcher
   - Personal Interest: Sports (which sport?), Fitness, Food/Restaurants, Travel, Fashion, Art, Music
   - Entertainment: Comedy, Celebrities, TV Shows, Movies, Gaming
   - Hobbies: Photography, Cooking, Golf, Running, Cycling, Hiking, Cars
   - Causes: Philanthropy, Climate, Health, Education, Charity
   - Personal Connection: Family member? College friend? Former colleague?

2. **What this reveals about them personally** - Go beyond the obvious:
   - Does this suggest a hobby they actively participate in?
   - A passion they might not talk about professionally?
   - A hidden side of their personality?
   - Childhood interests? Geographic ties?

3. **Personal insight** - The "getting to know them" angle:
   - Would you expect someone in their role to follow this?
   - What does this say about their personality/values?
   - How might this inform a personal conversation?

4. **Low-follower accounts** (<5000 followers) - These are GOLD for personal insights:
   - Likely personal friends, family, or niche interests
   - What does their bio reveal about the relationship?

BATCH SUMMARY:
- **Personal interests discovered** (hobbies, sports, entertainment)
- **Unexpected/surprising follows** (things you wouldn't expect)
- **Personality indicators** (introvert/extrovert, serious/playful, etc.)
- **Life outside work** (family, causes, communities)
- **Conversation hooks** for getting to know them personally (not professionally)

Focus on the HUMAN behind the professional. What makes them tick?'''

# ============================================================================
# CLUSTER ANALYSIS PROMPTS - Run in parallel for deep interest mapping
# ============================================================================

SPORTS_FITNESS_CLUSTER_PROMPT = '''You are analyzing someone's Twitter/social following list to understand their SPORTS & FITNESS interests.

PERSON: {person_name} ({person_role} at {person_company})

HERE IS EVERYONE THEY FOLLOW:
{all_following}

YOUR TASK: Find ALL sports and fitness related accounts and analyze them.

## CYCLING
List every cycling-related account they follow:
- Pro cyclists, cycling teams
- Cycling media/publications
- Local bike shops, cycling clubs
- Cycling apps (Strava, etc.)
- Cycling events/races

**Accounts Found:** [list all handles]
**Analysis:** Are they a casual rider or serious cyclist? Do they race? Road or mountain?
**Evidence-based conclusion:** "Follows X, Y, Z therefore..."

## GOLF
List every golf-related account:
- Pro golfers, PGA Tour
- Golf courses, country clubs
- Golf media, equipment brands
- Golf podcasts/personalities

**Accounts Found:** [list all handles]
**Analysis:** Do they play? What's their likely skill level? Member of clubs?

## RUNNING/MARATHON
- Running accounts, marathon organizers
- Running apps, coaches
- Track and field

**Accounts Found:** [list all handles]
**Analysis:** Casual jogger or marathon runner?

## TEAM SPORTS
### Basketball/NBA
**Accounts Found:** [list all handles]
**Analysis:** Which teams? Player or just fan?

### Football/NFL
**Accounts Found:** [list all handles]
**Analysis:** Fantasy player? Which teams?

### Baseball/MLB
**Accounts Found:** [list all handles]

### Soccer
**Accounts Found:** [list all handles]

## OTHER SPORTS
- Tennis, F1, Surfing, Skiing, etc.
**Accounts Found:** [list all handles]

## FITNESS/GYM
- Fitness influencers, gyms, trainers
- CrossFit, yoga, pilates
- Nutrition/diet accounts

**Accounts Found:** [list all handles]
**Analysis:** How fitness-focused are they?

## FINAL SPORTS PROFILE
Based on all the above, write a comprehensive sports/fitness profile:
- Which sports do they ACTIVELY PARTICIPATE in vs just watch?
- Estimated activity level (couch potato / weekend warrior / serious athlete)
- Best sports-related conversation starters
- Specific accounts to reference in conversation'''

ENTERTAINMENT_CULTURE_CLUSTER_PROMPT = '''You are analyzing someone's following list to understand their ENTERTAINMENT & CULTURE tastes.

PERSON: {person_name} ({person_role} at {person_company})

HERE IS EVERYONE THEY FOLLOW:
{all_following}

YOUR TASK: Find ALL entertainment and culture accounts and analyze their tastes.

## MUSIC
List ALL music-related accounts:
- Artists/bands they follow (list genre for each)
- Music venues, festivals
- Music industry people, labels
- Music streaming/discovery accounts
- DJs, producers

**Accounts Found:** [list all with genre]
**Music Taste Profile:** What genres? Mainstream or indie? Do they likely attend concerts?
**Conversation hooks:** Specific artists or venues to mention

## COMEDY
- Comedians they follow
- Comedy shows, podcasts
- Humor/satire accounts

**Accounts Found:** [list all handles]
**Humor Style:** Dry? Sarcastic? Political satire? Absurdist?

## TV & FILM
- Actors, directors
- TV shows, streaming services
- Film critics, movie accounts
- Entertainment news

**Accounts Found:** [list all handles]
**Viewing Habits:** What shows might they watch? Binge-watcher?

## PODCASTS
- Podcast hosts they follow
- Podcast networks
- Audio content creators

**Accounts Found:** [list all handles]
**Podcast Preferences:** Business? Comedy? True crime? Interview shows?

## BOOKS & READING
- Authors they follow
- Book reviewers, literary accounts
- Publishers, bookstores

**Accounts Found:** [list all handles]
**Reading Profile:** Fiction or non-fiction? What genres?

## FOOD & RESTAURANTS
- Chefs, restaurants
- Food critics, food media
- Cooking accounts
- Food delivery, reservation apps

**Accounts Found:** [list all handles]
**Foodie Level:** Casual eater or serious foodie? Fine dining or casual? Cuisine preferences?

## GAMING
- Game studios, esports
- Gaming personalities
- Specific games

**Accounts Found:** [list all handles]

## FINAL ENTERTAINMENT PROFILE
Comprehensive summary of their entertainment tastes:
- What do they do for fun?
- Cultural sophistication level
- Entertainment conversation starters with specific references'''

CAUSES_VALUES_CLUSTER_PROMPT = '''You are analyzing someone's following list to understand their VALUES, CAUSES, and PHILANTHROPIC INTERESTS.

PERSON: {person_name} ({person_role} at {person_company})

HERE IS EVERYONE THEY FOLLOW:
{all_following}

YOUR TASK: Analyze their follows to understand what causes and values matter to them. Focus on philanthropy, community, and personal values - NOT political analysis.

## PHILANTHROPY & CHARITY
- Charitable organizations they follow
- Nonprofit leaders
- Philanthropic foundations
- Volunteering organizations

**Accounts Found:** [list all]
**Causes They Support:** What charitable causes do they care about?

## EDUCATION & YOUTH
- Schools, universities they follow
- Education nonprofits
- Youth mentorship programs
- Scholarship organizations

**Accounts Found:** [list all]
**Education Focus:** Do they support education causes?

## HEALTH & WELLNESS CAUSES
- Health charities
- Mental health advocates
- Medical research organizations
- Wellness communities

**Accounts Found:** [list all]

## ENVIRONMENT & SUSTAINABILITY
- Environmental organizations
- Climate tech companies
- Sustainability advocates
- Conservation groups

**Accounts Found:** [list all]

## ENTREPRENEURSHIP & INNOVATION
- Startup ecosystem accounts
- Incubators, accelerators
- Entrepreneurship education
- Innovation communities

**Accounts Found:** [list all]

## SPIRITUAL / MINDFULNESS
- Meditation, mindfulness accounts
- Spiritual leaders
- Wellness retreats
- Philosophy accounts

**Accounts Found:** [list all]
**Mindfulness Profile:** Do they follow wellness/mindfulness content?

## LOCAL COMMUNITY
- Local news outlets
- Community organizations
- Local businesses, events
- City/neighborhood accounts

**Accounts Found:** [list all]
**Community Engagement:** How connected are they to their local community?

## VALUES SUMMARY
Based on all the above:
- Core values they hold
- Causes they likely care deeply about
- Community involvement level
- Good conversation topics around shared values'''

PERSONAL_NETWORK_CLUSTER_PROMPT = '''You are analyzing someone's following list to map their PERSONAL NETWORK and RELATIONSHIPS.

PERSON: {person_name} ({person_role} at {person_company})

HERE IS EVERYONE THEY FOLLOW:
{all_following}

YOUR TASK: Find accounts that reveal PERSONAL relationships (not just professional).

## LOW-FOLLOWER ACCOUNTS (<3000 followers)
These are likely real personal connections. For EACH one:

**Handle | Follower Count | Bio | Likely Relationship**
(List ALL accounts with <3000 followers)

For each, infer the relationship type:
- College friend (check if same school mentioned)
- Former colleague (check company mentions)
- Family member (same last name?)
- Childhood friend
- Hobby buddy
- Neighbor/local friend
- Unknown personal connection

## FORMER COLLEAGUES
Based on their career history, find people from:
- Loopt
- Shopkick
- Dropbox
- Greylock
- Script Capital/122 West
- South Park Commons

**Accounts Found from each company:** [list]

## STANFORD NETWORK
- Stanford alumni they follow
- Stanford professors, programs
- Stanford sports, organizations

**Accounts Found:** [list all]
**Stanford Involvement Level:** Casual alum or deeply connected?

## FAMILY INDICATORS
- Accounts with same last name
- "Family" or parenting accounts
- Children's content (suggests they have kids)
- Spouse/partner indicators

**Evidence of Family:** [list any evidence]
**Family Status Assessment:** Married? Kids? Close family ties?

## INNER CIRCLE
Based on interaction patterns and low-follower accounts, who are likely their closest friends?

**Probable Inner Circle:** [list 5-10 most likely close personal connections with evidence]

## RELATIONSHIP MAP SUMMARY
- Who are their real friends (not just professional contacts)?
- What communities do they belong to personally?
- Family situation insights
- Best personal connections to reference or ask about'''

HIDDEN_INTERESTS_CLUSTER_PROMPT = '''You are looking for SURPRISING and UNEXPECTED follows that reveal hidden sides of this person.

PERSON: {person_name} ({person_role} at {person_company})

HERE IS EVERYONE THEY FOLLOW:
{all_following}

YOUR TASK: Find the follows that DON'T FIT their professional profile. What do these reveal?

## UNEXPECTED FOLLOWS
List accounts that seem surprising for a {person_role}:

For each unexpected follow:
**Handle:**
**Why it's unexpected:**
**What it might reveal:**

## NICHE INTERESTS
Accounts related to very specific hobbies or interests:
- Unusual hobbies
- Niche communities
- Obscure interests

**Accounts Found:** [list all]
**What these reveal about them:**

## QUIRKY/FUN FOLLOWS
- Humor accounts
- Meme accounts
- Weird or absurdist content
- Parody accounts

**Accounts Found:** [list all]
**Sense of Humor Profile:**

## GUILTY PLEASURES
- Reality TV
- Celebrity gossip
- Pop culture they might not admit to
- "Lowbrow" entertainment

**Accounts Found:** [list all]

## BOT/UTILITY FOLLOWS
- Weather bots
- News bots
- Local alert accounts
- Utility accounts

**Accounts Found:** [list all]
**What these reveal:** (e.g., earthquake bot = cares about local SF events)

## ASPIRATIONAL FOLLOWS
Accounts they follow that suggest who they WANT to be:
- Lifestyle accounts
- Successful people in different fields
- Dream destinations, experiences

**Accounts Found:** [list all]
**Aspirational Profile:** What life do they aspire to?

## CREEPY-GOOD INSIGHTS
The most surprising discoveries that would make them think "how did you know that?":

1. [Insight with evidence]
2. [Insight with evidence]
3. [Insight with evidence]
4. [Insight with evidence]
5. [Insight with evidence]

## HIDDEN INTERESTS SUMMARY
The complete picture of who this person is BEYOND their professional identity:
- Secret hobbies
- Personality quirks
- Unexpected passions
- Things they probably don't talk about at work'''

SYNTHESIS_PROMPT = '''You are creating a COMPLETE profile of this person - not just their professional life, but WHO THEY ARE as a human being.

You have access to:
1. Their full profile/enrichment data (including social profiles like Strava, Pinterest, etc.)
2. Detailed analyses of EVERY account they follow (analyzed in batches)
3. DEEP CLUSTER ANALYSES - specialized analyses of their interests by category
4. Articles and press mentions
5. Personal details (location, family connections)

YOUR TASK: Create the most comprehensive dossier that would help someone truly KNOW this person - their passions, quirks, what makes them laugh, what they care about, who they spend time with.

CRITICAL RULE - ATTRIBUTION REQUIRED:
Every single claim or insight MUST be attributed to a specific anchor:
- An account they follow (e.g., "Follows @staborunn and @NYCMarathon, suggesting interest in running")
- A social media post they made (e.g., "Posted about hosting a Catan tournament on 12/03/2025")
- Their work history (e.g., "Spent 3 years at Morgan Stanley in payments research")
- Their bio or self-description (e.g., "Describes themselves as 'lover of life's quirks'")
- A social profile URL found (e.g., "Has a Strava account, indicating cycling/running activity")
- An article or press mention (e.g., "Featured in TechCrunch discussing fintech trends")

DO NOT make claims without citing the evidence. If you cannot point to a specific anchor, do not include the claim.
Example of GOOD: "Follows @VCBrags and @vcstarterkit - enjoys industry satire"
Example of BAD: "Probably likes hiking" (no evidence cited)

## ENRICHMENT DATA (Profile, Career, Social Profiles, Posts):
{enrichment_data}

## FOLLOWING BATCH ANALYSES:
{following_analyses}

## SPORTS & FITNESS CLUSTER ANALYSIS:
{sports_cluster}

## ENTERTAINMENT & CULTURE CLUSTER ANALYSIS:
{entertainment_cluster}

## CAUSES & POLITICS CLUSTER ANALYSIS:
{causes_cluster}

## PERSONAL NETWORK CLUSTER ANALYSIS:
{network_cluster}

## HIDDEN INTERESTS CLUSTER ANALYSIS:
{hidden_cluster}

## ARTICLES & PRESS:
{articles_data}

---

Write an EXHAUSTIVE dossier with these sections:

## 1. IDENTITY SNAPSHOT
Full name, role, company, location, age estimate, birthday if available.
Personal details: location, domain names owned.
Self-description: How do they describe themselves in their bio? What does this reveal?

**Email Addresses (list ALL found):**
- Primary email
- Work emails
- Personal emails
- All alternative emails from altemails field

**Social Profiles (list ALL with URLs):**
Include every social profile found - Twitter, LinkedIn, Instagram, Strava, Pinterest, Flickr, GitHub, Foursquare, AngelList, etc.
Format as: Platform: URL

## 2. PERSONAL LIFE & HOBBIES (CRITICAL SECTION)
This is the section that makes the dossier special. Go DEEP on:

**Active Hobbies & Sports:**
- Look at their social profiles (Strava = cycling/running, Pinterest = interests, Flickr = photography)
- Sports accounts they follow - do they PLAY or just watch?
- Fitness level/activity (marathon runner? casual gym goer? golfer?)
- Weekend activities - hiking, skiing, surfing?

**Entertainment & Culture:**
- Music tastes (who do they follow? What concerts might they attend?)
- TV shows, movies, books they might enjoy
- Comedy they like (podcasts, comedians)
- Food and restaurants (any chef follows? foodie accounts?)

**Personal Passions:**
- Causes they care about (volunteering data, activist follows)
- Communities they belong to (alumni networks, local groups)
- Religious/spiritual interests
- Creative pursuits (writing, art, photography)

**Life Outside Work:**
- Family indicators (children? pets? married?)
- Where they spend time (second homes? vacation spots?)
- Friend circles (low-follower personal accounts)
- Hometown/geographic ties

**Quirks & Personality:**
- How do they describe themselves? ("lover of life's quirks")
- Sense of humor style
- Introvert or extrovert signals?
- Morning person or night owl?

## 3. CAREER DNA
Complete trajectory with dates. For EACH role:
- What they actually did
- Why they made this move
- Key relationships formed
Their "superpower" - what makes them uniquely valuable.

## 4. PSYCHOGRAPHIC PROFILE
Based on the following analyses, explain WHO this person is:
- Core identity/archetypes (The Builder? The Mentor? The Explorer?)
- Values and beliefs (with specific evidence)
- Aspirations (who do they want to be?)
- Professional tribes they belong to

## 5. SOCIAL GRAPH ANALYSIS (BRIEF OVERVIEW)
Quick summary of their social graph:
- **Professional Network**: VCs, founders, executives
- **Personal Interest Graph**: Sports, hobbies, entertainment
- **Inner Circle**: Low-follower accounts (likely real friends/family)

## 6. INTEREST CLUSTER DEEP DIVE (CRITICAL - BE EXHAUSTIVE)
This is the most important section. For EACH interest area, provide:
1. The specific handles they follow (list ALL relevant ones)
2. Evidence-based conclusion about their level of interest
3. Whether they're a participant or just a spectator

**FORMAT FOR EACH CLUSTER:**
```
### [INTEREST NAME]
**Accounts Followed:** @handle1, @handle2, @handle3, @handle4, @handle5...
**Evidence:** [What these follows reveal]
**Conclusion:** [Casual fan / Serious enthusiast / Active participant / Professional interest]
**Conversation Angle:** [How to use this in conversation]
```

**REQUIRED CLUSTERS TO ANALYZE (if accounts exist):**

### SPORTS & FITNESS
Break down by sport:
- **Cycling**: List ALL cycling-related follows. Are they on Strava? Do they follow pro cyclists, local bike shops, cycling media?
- **Golf**: List ALL golf follows. Country clubs? Pro golfers? Golf media?
- **Basketball/NBA**: Teams, players, analysts they follow
- **Football/NFL**: Teams, players, fantasy sports?
- **Running/Marathon**: Running accounts, race organizers?
- **Other sports**: Tennis, soccer, F1, etc.

### MUSIC & ENTERTAINMENT
- **Music**: Artists, genres, venues, music industry people. What does this say about their taste?
- **Podcasts**: Which podcast hosts/shows do they follow?
- **Comedy**: Comedians, comedy shows, humor accounts
- **TV/Film**: Actors, shows, critics, streaming services
- **Gaming**: Any gaming follows?

### FOOD & LIFESTYLE
- **Restaurants/Food**: Chefs, food critics, restaurant accounts, food media
- **Travel**: Travel accounts, destinations, airlines
- **Fashion**: Brands, designers, fashion media
- **Home/Design**: Interior design, architecture

### CAUSES & VALUES
- **Philanthropy**: Charitable organizations, nonprofits they support
- **Community**: Local organizations, community involvement
- **Climate/Environment**: Environmental accounts, sustainability
- **Education**: Schools, education nonprofits, mentorship

### INTELLECTUAL INTERESTS
- **Books/Reading**: Authors, book clubs, literary accounts
- **Science**: Scientists, science communicators
- **Philosophy/Spirituality**: Thinkers, spiritual leaders
- **Self-Improvement**: Productivity, habits, mental health

### TECH INTERESTS (Beyond Work)
- **Crypto/Web3**: Which projects, founders, thought leaders?
- **AI**: Beyond work - personal interest in AI?
- **Consumer Tech**: Product Hunt, gadget reviewers
- **Specific Platforms**: Deep interest in any particular platform?

### GEOGRAPHIC TIES
- **Local Community**: Local news, local businesses, local politicians
- **Hometown**: Any accounts tied to where they grew up?
- **Other Cities**: Interest in other locations?

### PERSONAL NETWORK
- **Low-Follower Accounts (<2000 followers)**: These are likely real friends, family, or niche interests
  - List each one with their bio
  - Infer the relationship (college friend? former colleague? family?)

### UNEXPECTED/SURPRISING FOLLOWS
- Accounts that don't fit their professional profile
- What do these reveal about hidden interests?

For EACH cluster, I want to see the ACTUAL HANDLES they follow as evidence.

## 7. CONTENT & VOICE ANALYSIS
From their posts:
- Topics they care about (professional AND personal)
- Communication style and tone
- Sense of humor (examples)
- Recent wins and celebrations
- Frustrations and complaints
- Strong opinions they've stated

## 8. KEY RELATIONSHIPS (Top 25)
The 25 most important accounts they follow, with:
- Handle, name, follower count
- Nature of relationship (mentor? friend? colleague? family?)
- Why this matters for understanding them

## 9. CONVERSATION STARTERS (30+)
Divide into categories:
**Professional hooks** (5-10)
**Personal interest hooks** (10-15) - hobbies, sports, entertainment
**Shared experience hooks** (5-10) - places, schools, companies
**Current events hooks** (5) - recent posts, news about them

## 10. RECOMMENDATIONS & HOW OTHERS SEE THEM
From LinkedIn recommendations:
- How do colleagues describe them?
- What qualities do people highlight?
- Any patterns in the praise?

## 11. "CREEPY GOOD" INSIGHTS
The insights that make them think "how did they know that?":
- Non-obvious patterns (e.g., follows earthquake bot = interested in SF local news)
- Cross-referenced discoveries
- Personal details most wouldn't find
- Behavioral predictions

## 12. APPROACH STRATEGY
How to connect with this person:
- Best angle (professional vs personal)
- Shared connections to mention
- Topics that will resonate
- Personal interests to reference (shows you did your homework)
- What NOT to do

This dossier should make someone feel like they already KNOW this person before ever meeting them.

CRITICAL INSTRUCTIONS:
- You MUST include ALL 13 sections listed above. Do not skip or combine sections.
- Section 6 (Interest Cluster Deep Dive) MUST include ALL subsections (Sports, Entertainment, Causes, Tech, Geographic, Personal Network, Unexpected) with SPECIFIC HANDLES as evidence.
- Key Relationships MUST list exactly 25 accounts.
- Conversation Starters MUST include 30+ hooks divided into categories.
- Be EXHAUSTIVE. This should be 400+ lines of detailed analysis.
- Do NOT summarize or condense. Include all details from the cluster analyses.'''


# ============================================================================
# SIMULATION SYNTHESIS PROMPT (used when --question is provided)
# ============================================================================

SIMULATION_SYNTHESIS_PROMPT = '''You are simulating how a real person would respond to a specific question, based on comprehensive intelligence about them.

THE QUESTION BEING ASKED:
"{question}"

QUESTION ANALYSIS CONTEXT:
{question_context}

You have access to:
1. Their full profile/enrichment data (including social profiles)
2. Detailed analyses of their social graph and interests
3. Deep cluster analyses (specialized for this question's topic)
4. Articles and press mentions
5. Personal details (location, career, family connections)

CRITICAL RULE - PRESENT INSIGHTS NATURALLY:
You have rich data about this person. Use it to write with AUTHORITY and CONVICTION — as if you deeply know this person — but DO NOT expose the methodology. The reader should feel like they're getting intelligence from someone who truly understands this person, not a data report.

NEVER DO THIS:
- "Follows @handle, suggesting..."
- "Based on their Twitter following list..."
- "They follow 12 accounts related to..."
- "Their social media follows indicate..."
- "According to their social graph..."

INSTEAD, use natural language like:
- "Rabois is deeply embedded in the Project 2025 intellectual ecosystem"
- "He's closely connected to Trump's inner circle — Kushner, Jason Miller, Karoline Leavitt"
- "His worldview is shaped by the PayPal Mafia ethos of high-agency disruption"
- "He shows strong engagement with the anti-DEI movement and figures like Christopher Rufo"
- "He has a clear affinity towards hawkish foreign policy circles"
- "His move from SF to Miami was itself a political statement"
- "He's plugged into the DOGE orbit through connections to James Burnham and Russ Vought"

Good framing words: "engagement with", "affinity towards", "closely connected to", "embedded in", "aligned with", "plugged into", "drawn to", "orbits around", "resonates with"

Present insights as KNOWLEDGE, not as "we found this data point." The magic is in knowing things about someone that feel like insider understanding, not in showing your work. Save the sourcing for internal confidence — the output should read like a briefing from someone who KNOWS this person.

For your own internal reasoning, every claim must still be grounded in real evidence from the data below. But the OUTPUT should not reveal the source methodology.

## ENRICHMENT DATA (Profile, Career, Social Profiles, Posts):
{enrichment_data}

## FOLLOWING BATCH ANALYSES (focused on question-relevant signals):
{following_analyses}

## CLUSTER ANALYSES (question-relevant clusters):
{cluster_analyses_combined}

## ARTICLES & PRESS:
{articles_data}

---

CRITICAL: INSUFFICIENT SIGNAL DETECTION

Before writing the full report, evaluate whether the data contains DIRECT, SPECIFIC signal to answer this question. Apply this strict test:

1. Can you point to at least 2-3 data points that DIRECTLY relate to the specific topic of the question?
   - "They're into fitness" does NOT count as signal for "what's their favorite sock brand"
   - "They work in tech" does NOT count as signal for "what programming language do they prefer"
   - Adjacent or tangential interests are NOT sufficient — you need DIRECT relevance

2. Would a reasonable person look at the evidence and say "yeah, that clearly tells us something about this specific question"?
   - If the answer requires you to make 2+ logical leaps from the data, it's NOT enough signal
   - If you're inferring preferences from general lifestyle/personality rather than specific evidence, it's NOT enough signal

3. Are you about to write something you'd be embarrassed by if the real person read it?
   - If the answer would make the person say "where the hell did they get THAT from?", use insufficient signal
   - If the answer would make them say "yeah, that's pretty much right", proceed with the full report

THE KEY TEST: Would the person themselves say "yeah, the data you had actually DOES reveal that about me"?
If the answer is "no, you're just guessing based on my general vibe" — that's insufficient signal.

EXAMPLES OF INSUFFICIENT SIGNAL — USE THE SHORT FORMAT:
- "What's their favorite restaurant?" — unless they literally post about or engage with a specific restaurant
- "What sock brand do they prefer?" — being into fitness does NOT tell you sock preferences. Being into cycling does NOT tell you sock preferences. Being a biohacker does NOT tell you sock preferences. You need them to have MENTIONED or ENGAGED WITH a specific sock brand.
- "What car do they drive?" — being wealthy does NOT tell you their car brand
- "What's their blood type?" — obviously no signal
- "Do they prefer cats or dogs?" — unless there's direct pet-related evidence
- "What's their favorite movie?" — unless they've posted about it or engage with specific films
- ANY question about a specific product/brand preference — unless they directly engage with that specific brand or product category at a granular level

IMPORTANT: Being in an adjacent lifestyle category is NOT sufficient signal for specific product preferences.
"They're into fitness" → does NOT mean you know their shoe brand, gym, supplements, or gear preferences.
"They're into tech" → does NOT mean you know their laptop, phone, or keyboard preferences.
"They're into food" → does NOT mean you know their favorite restaurant.
You need SPECIFIC, DIRECT evidence — a post, a mention, engagement with that exact brand/entity.

EXAMPLES OF SUFFICIENT SIGNAL — USE THE FULL FORMAT:
- "What do they think about Trump?" — political follows, news diet, and public statements ARE direct signal
- "Are they into AI?" — following AI accounts, working in AI, posting about AI IS direct signal
- "Do they like cycling?" — following cycling accounts and having a Strava IS direct signal
- "How do they feel about climate change?" — following environmental orgs, posting about it IS direct signal

If there is NOT enough DIRECT signal, you MUST use the INSUFFICIENT SIGNAL format below. Do NOT hallucinate. Do NOT extrapolate from tangential data. It is FAR better to say "we don't know" than to confidently make something up from vibes.

=== INSUFFICIENT SIGNAL FORMAT ===
Use this format when data is too thin to simulate a meaningful answer:

## 1. AT A GLANCE

**Question:** "{question}"
**Sentiment:** Insufficient Data
**Short Answer:** We don't have enough signal to predict this person's stance on this topic with any confidence.
**Conviction Level:** Unknown
**Confidence:** Insufficient Data — [explain what's missing]

**What we looked for but didn't find:**
- [Specific signals that would have helped but weren't present]
- [Types of accounts, posts, or data that would be needed]

**What we CAN say:**
- [Any tangential observations, even if weak — or "Nothing relevant found"]

**How to find out:**
- [Practical suggestions — e.g., "Ask them directly", "Check their Amazon reviews", "Look at their Instagram stories"]

=== END INSUFFICIENT SIGNAL FORMAT ===
Do NOT continue to sections 2-6 if using this format. Stop after section 1.

=== FULL REPORT FORMAT ===
Use this format when you have real signal (at least moderate confidence):

Write a THOROUGH simulation report with these sections IN THIS EXACT ORDER:

## 1. AT A GLANCE
A structured, scannable summary. Fill in each field:

**Question:** "{question}"
**Sentiment:** [Strongly Positive / Positive / Leaning Positive / Neutral / Leaning Negative / Negative / Strongly Negative]
**Short Answer:** [1-2 sentence plain-English summary of their likely position]
**Conviction Level:** [Passionate / Firm / Moderate / Ambivalent / Indifferent]
**Confidence:** [High / Medium / Low] — [brief reason]
**Key Drivers:** [3-5 bullet points — the core reasons behind their stance, each one line]

This section should be instantly scannable — someone should be able to read it in 10 seconds and know the answer.

## 2. SIMULATED RESPONSE
Write out how this person would ACTUALLY respond if asked this question in a natural conversation. This should:
- Use their actual communication style and tone (formal? casual? data-driven? emotional?)
- Reference things they'd naturally reference (their interests, experiences, relationships)
- Include the nuance they'd add — most people don't give black-and-white answers
- Show what they'd push back on or qualify
- Include their likely emotional register (passionate? indifferent? cautious?)
- Be written in FIRST PERSON as if they are speaking

**Format as a realistic conversational response — not bullet points. Write it as dialogue.**

## 3. CONFIDENCE ASSESSMENT
Rate your overall confidence and break down by claim:

**What we're most sure about:**
- [Insight] — [why we're confident]

**Probable but less certain:**
- [Insight] — [reasoning]

**Educated guesses:**
- [Insight] — [what makes this speculative]

**Blind spots:**
- What we don't know that could change the picture
- What a direct conversation would reveal that data can't

## 4. INTELLIGENCE BRIEF
Present what we know about this person's relationship to the question topic, organized by confidence:

**Direct Connections:**
- Public statements, posts, or articles where they've addressed this topic
- Career experience and professional relationships directly relevant
- Known affiliations, memberships, and close connections to key figures
- Actions they've taken that reveal their position (moves, investments, public stances)

**Contextual Signals:**
- Their broader worldview, values, and intellectual circles
- Career trajectory and professional ecosystem
- Geographic, cultural, and generational context
- Patterns in their interests and social circles

**Inferred Leanings:**
- Personality traits and decision-making patterns that predict their stance
- What's conspicuously ABSENT from their world (what they avoid or reject)
- How their archetype typically responds to topics like this

REMEMBER: Write this section as an intelligence briefing — authoritative, insightful, no mention of "follows" or "following lists."

## 5. PSYCHOGRAPHIC REASONING
Based on their overall profile, explain the reasoning chain:
- Their core identity/archetype and how it relates to this question
- Their values system and how it applies here
- Their communication style and how they'd frame their answer
- Any relevant life experiences that shape their perspective
- Cognitive biases or tendencies suggested by their profile

## 6. CONVERSATION PLAYBOOK
How to actually have this conversation with them:

**Best way to bring this up:**
- Natural entry points based on their interests
- Framing that would resonate with their communication style

**What they'd engage with:**
- Follow-up questions they'd find interesting
- Angles that would draw out their real opinion

**Landmines to avoid:**
- Topics or framings that would shut them down
- Assumptions that might offend them

**Predicted follow-up questions they'd ask YOU:**
- Based on their personality and interests, what would they want to know?

This simulation should feel like talking to someone who KNOWS this person well — not a generic AI response.'''


# ============================================================================
# LLM CALL FUNCTIONS
# ============================================================================

def _call_gemini(prompt: str) -> Optional[str]:
    """Make a single Gemini API call."""
    if not GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            'gemini-2.5-flash',
            generation_config={"temperature": 0.7, "max_output_tokens": 65536}
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"    ⚠ Gemini error: {e}")
        return None


def _call_openai(prompt: str) -> Optional[str]:
    """Make a single OpenAI API call."""
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=16384
        )
        return response.choices[0].message.content
    except Exception:
        return None


def _call_anthropic(prompt: str) -> Optional[str]:
    """Make a single Anthropic API call."""
    if not ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=64000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception:
        return None


# Global backup LLM setting
_backup_llm = None

def set_backup_llm(backup: str):
    """Set the backup LLM to use when primary fails."""
    global _backup_llm
    _backup_llm = backup

def get_backup_llm() -> Optional[str]:
    """Get the current backup LLM setting."""
    global _backup_llm
    return _backup_llm

def _get_llm_caller(llm: str = "auto"):
    """Get the appropriate LLM call function."""
    if llm == "gemini" and GEMINI_API_KEY:
        return _call_gemini, "gemini"
    elif llm == "openai" and OPENAI_API_KEY:
        return _call_openai, "openai"
    elif llm == "anthropic" and ANTHROPIC_API_KEY:
        return _call_anthropic, "anthropic"
    elif llm == "auto":
        if GEMINI_API_KEY:
            return _call_gemini, "gemini"
        elif OPENAI_API_KEY:
            return _call_openai, "openai"
        elif ANTHROPIC_API_KEY:
            return _call_anthropic, "anthropic"
    return None, None

def _call_llm_with_fallback(prompt: str, primary_llm: str = "auto", backup_llm: str = None) -> Optional[str]:
    """Call LLM with automatic fallback. Gemini -> OpenAI by default."""
    # Default fallback chain: gemini -> openai -> anthropic
    fallback_order = ["gemini", "openai", "anthropic"]

    # Determine primary
    if primary_llm == "auto":
        primary_llm = "gemini" if GEMINI_API_KEY else ("openai" if OPENAI_API_KEY else "anthropic")

    # Try primary
    caller, primary_name = _get_llm_caller(primary_llm)
    if caller:
        result = caller(prompt)
        if result:
            return result

    # Primary failed - try fallbacks automatically
    for fallback in fallback_order:
        if fallback == primary_llm:
            continue  # Skip primary, already tried
        backup_caller, backup_name = _get_llm_caller(fallback)
        if backup_caller:
            print(f"    ↻ Falling back to {backup_name}...", flush=True)
            result = backup_caller(prompt)
            if result:
                return result

    return None


def _batch_following_data(following_data: Dict, batch_size: int = 75) -> list:
    """Split following data into batches."""
    interactions = following_data.get("result", {}).get("interactions", [])
    if not interactions:
        return []

    batches = []
    for i in range(0, len(interactions), batch_size):
        batches.append(interactions[i:i + batch_size])
    return batches


def _slim_following_for_llm(following_list: list) -> list:
    """
    Strip unnecessary fields from following data to reduce token usage.
    Keeps only: username, display_name, followers_count, bio, location
    """
    slim = []
    for item in following_list:
        actor = item.get("actor", {})
        slim.append({
            "handle": actor.get("username", ""),
            "name": actor.get("display_name", ""),
            "followers": actor.get("followers_count", ""),
            "bio": actor.get("bio", ""),
            "location": actor.get("location", ""),
        })
    return slim


def _following_to_compact_string(following_list: list) -> str:
    """
    Convert following list to compact string format for LLM prompts.
    Format: @handle | Name | Followers | Bio
    Much more token-efficient than JSON.
    """
    lines = []
    for item in following_list:
        actor = item.get("actor", {})
        handle = actor.get("username", "unknown")
        name = actor.get("display_name", "")
        followers = actor.get("followers_count", "?")
        bio = (actor.get("bio", "") or "").replace("\n", " ").strip()
        lines.append(f"@{handle} | {name} | {followers} followers | {bio}")
    return "\n".join(lines)


def analyze_question(question: str, llm: str = "auto", verbose: bool = True) -> Optional[QuestionContext]:
    """
    Analyze a simulation question to determine which clusters and signals matter most.
    Returns a QuestionContext that shapes the rest of the pipeline.
    """
    backup = get_backup_llm()
    prompt = QUESTION_ANALYZER_PROMPT.format(question=question)
    raw = _call_llm_with_fallback(prompt, llm, backup)
    if not raw:
        return None

    # Parse JSON response (strip markdown fences if present)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()
    if raw.startswith("json"):
        raw = raw[4:].strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        if verbose:
            print(f"  ⚠ Failed to parse question analysis JSON, using defaults")
        return QuestionContext(
            question=question,
            cluster_priorities={"sports_fitness": "useful", "entertainment_culture": "useful",
                               "causes_values": "useful", "personal_network": "useful",
                               "hidden_interests": "useful"},
            specific_signals=[],
            additional_focus="",
            enrichment_focus=["posts", "career_history", "articles"]
        )

    return QuestionContext(
        question=question,
        cluster_priorities=parsed.get("cluster_priorities", {}),
        specific_signals=parsed.get("specific_signals", []),
        additional_focus=parsed.get("additional_focus", ""),
        enrichment_focus=parsed.get("enrichment_focus", [])
    )


def generate_dossier(results: ResearchResults, llm: str = "auto", verbose: bool = True, question: Optional[str] = None) -> Optional[str]:
    """
    Generate intelligent dossier using batched LLM calls for deep analysis.
    If question is provided, runs in simulation mode with question-adaptive analysis.

    1. (Optional) Analyze the question to determine cluster priorities
    2. Batch the following lists into chunks
    3. Run concurrent LLM calls to analyze each batch
    4. Synthesize all analyses into final dossier (or simulation)
    """
    import time as _time
    _start_total = _time.time()

    def _log(msg, start_time=None):
        elapsed = ""
        if start_time:
            elapsed = f" ({_time.time() - start_time:.1f}s)"
        if verbose:
            print(f"  [{_time.strftime('%H:%M:%S')}] {msg}{elapsed}", flush=True)

    # Get LLM caller (with fallback support)
    primary_call, llm_name = _get_llm_caller(llm)
    if not primary_call:
        _log("⚠ No LLM available. Set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY")
        return None

    # Wrap with fallback support - capture backup at definition time for thread safety
    backup = get_backup_llm()
    def llm_call(prompt: str) -> Optional[str]:
        return _call_llm_with_fallback(prompt, llm, backup)

    _log(f"Using {llm_name} for deep analysis (fallback: gemini→openai→anthropic)")

    # Phase 0: Analyze question (if in simulation mode)
    question_ctx = None
    if question:
        _log(f"PHASE 0: Analyzing question for simulation mode...")
        _q_start = _time.time()
        question_ctx = analyze_question(question, llm=llm, verbose=verbose)
        if question_ctx:
            _log(f"PHASE 0 COMPLETE: Question analyzed", _q_start)
            skipped = [k for k, v in question_ctx.cluster_priorities.items() if v == "skip"]
            critical = [k for k, v in question_ctx.cluster_priorities.items() if v == "critical"]
            if skipped:
                _log(f"  Skipping clusters: {', '.join(skipped)}")
            if critical:
                _log(f"  Critical clusters: {', '.join(critical)}")
        else:
            _log(f"  ⚠ Question analysis failed, proceeding with all clusters")

    # Extract person context from enrichment
    enrichment = results.enrichment or {}
    result_data = enrichment.get("result", {})
    person_name = f"{result_data.get('firstname', '')} {result_data.get('lastname', '')}".strip() or "Unknown"
    person_role = result_data.get("headline", "Unknown")
    careers = result_data.get("careers_info", [])
    person_company = careers[0].get("company_name", "Unknown") if careers else "Unknown"

    # Collect all following data
    all_following = []
    if results.following_twitter:
        twitter_interactions = results.following_twitter.get("result", {}).get("interactions", [])
        for item in twitter_interactions:
            item["_source"] = "twitter"
        all_following.extend(twitter_interactions)
    if results.following_instagram:
        ig_interactions = results.following_instagram.get("result", {}).get("interactions", [])
        for item in ig_interactions:
            item["_source"] = "instagram"
        all_following.extend(ig_interactions)

    # Batch the following data
    batch_size = 75
    batches = [all_following[i:i + batch_size] for i in range(0, len(all_following), batch_size)] if all_following else []

    following_analyses = []

    if batches:
        _log(f"PHASE 1: Analyzing {len(all_following)} followed accounts in {len(batches)} batches...")
        _batch_start = _time.time()

        # Prepare batch prompts
        batch_prompts = []
        for i, batch in enumerate(batches):
            batch_data = _following_to_compact_string(batch)
            prompt = BATCH_ANALYSIS_PROMPT.format(
                person_name=person_name,
                person_role=person_role,
                person_company=person_company,
                batch_size=len(batch),
                batch_num=i + 1,
                total_batches=len(batches),
                batch_data=batch_data
            )
            # Inject question context into batch prompts
            if question_ctx:
                signals_str = ", ".join(question_ctx.specific_signals) if question_ctx.specific_signals else "any accounts relevant to the question"
                prompt += f'''

ADDITIONAL FOCUS FOR THIS ANALYSIS:
The goal is to understand how this person would respond to: "{question_ctx.question}"
Pay special attention to: {signals_str}
Flag any accounts that DIRECTLY relate to this topic — these are the most valuable signals.
For each flagged account, explain WHY it's relevant to the question.'''
            batch_prompts.append((i, prompt))

        # Run batch analyses concurrently
        _batch_times = {}
        def analyze_batch(args):
            idx, prompt = args
            _s = _time.time()
            result = llm_call(prompt)
            _batch_times[idx] = _time.time() - _s
            return idx, result

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(analyze_batch, bp): bp[0] for bp in batch_prompts}
            completed_count = 0

            for future in as_completed(futures):
                idx, analysis = future.result()
                elapsed = time.time() - _batch_start
                if analysis:
                    following_analyses.append((idx, analysis))
                    _log(f"  ✓ Batch {idx + 1}/{len(batches)} done ({_batch_times.get(idx, 0):.1f}s)")
                else:
                    _log(f"  ✗ Batch {idx + 1}/{len(batches)} FAILED")

        _log(f"PHASE 1 COMPLETE: {len(following_analyses)}/{len(batches)} batches", _batch_start)

        # Sort by batch index
        following_analyses.sort(key=lambda x: x[0])
        following_analyses = [a[1] for a in following_analyses]

    # =========================================================================
    # PHASE 2: Deep Cluster Analysis
    # Run 5 specialized clustering prompts in parallel
    # =========================================================================

    cluster_analyses = {
        "sports": None,
        "entertainment": None,
        "causes": None,
        "network": None,
        "hidden": None
    }

    # Map cluster keys to their priority keys in QuestionContext
    _cluster_priority_map = {
        "sports": "sports_fitness",
        "entertainment": "entertainment_culture",
        "causes": "causes_values",
        "network": "personal_network",
        "hidden": "hidden_interests"
    }

    if all_following:
        # Determine which clusters to run
        clusters_to_run = list(cluster_analyses.keys())
        if question_ctx:
            clusters_to_run = [
                c for c in clusters_to_run
                if question_ctx.cluster_priorities.get(_cluster_priority_map[c], "useful") != "skip"
            ]
            skipped_clusters = [c for c in cluster_analyses.keys() if c not in clusters_to_run]
            if skipped_clusters:
                _log(f"PHASE 2: Skipping {len(skipped_clusters)} irrelevant clusters: {', '.join(skipped_clusters)}")

        _log(f"PHASE 2: Running {len(clusters_to_run)} deep cluster analyses in parallel...")
        _cluster_start = _time.time()

        # Prepare all following data as compact string for cluster prompts (much fewer tokens)
        all_following_str = _following_to_compact_string(all_following)

        # Build question-focus suffix for critical clusters
        _question_suffix = ""
        if question_ctx and question_ctx.additional_focus:
            _question_suffix = f'''

ADDITIONAL FOCUS (this analysis is being used to simulate how this person would respond to a specific question):
Question: "{question_ctx.question}"
{question_ctx.additional_focus}
Pay extra attention to any signals that would help predict their stance on this topic.'''

        # Prepare cluster prompts
        all_cluster_prompts = {
            "sports": SPORTS_FITNESS_CLUSTER_PROMPT.format(
                person_name=person_name,
                person_role=person_role,
                person_company=person_company,
                all_following=all_following_str
            ),
            "entertainment": ENTERTAINMENT_CULTURE_CLUSTER_PROMPT.format(
                person_name=person_name,
                person_role=person_role,
                person_company=person_company,
                all_following=all_following_str
            ),
            "causes": CAUSES_VALUES_CLUSTER_PROMPT.format(
                person_name=person_name,
                person_role=person_role,
                person_company=person_company,
                all_following=all_following_str
            ),
            "network": PERSONAL_NETWORK_CLUSTER_PROMPT.format(
                person_name=person_name,
                person_role=person_role,
                person_company=person_company,
                all_following=all_following_str
            ),
            "hidden": HIDDEN_INTERESTS_CLUSTER_PROMPT.format(
                person_name=person_name,
                person_role=person_role,
                person_company=person_company,
                all_following=all_following_str
            )
        }

        # Inject question focus into critical clusters
        if question_ctx:
            for cluster_name in clusters_to_run:
                priority_key = _cluster_priority_map[cluster_name]
                if question_ctx.cluster_priorities.get(priority_key) == "critical":
                    all_cluster_prompts[cluster_name] += _question_suffix

        # Filter to only clusters we're running
        cluster_prompts = {k: v for k, v in all_cluster_prompts.items() if k in clusters_to_run}

        # Run cluster analyses concurrently
        _cluster_times = {}
        def run_cluster(args):
            cluster_name, prompt = args
            _s = _time.time()
            result = llm_call(prompt)
            _cluster_times[cluster_name] = _time.time() - _s
            return cluster_name, result

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(run_cluster, (name, prompt)): name
                      for name, prompt in cluster_prompts.items()}
            cluster_done = 0

            for future in as_completed(futures):
                cluster_name, analysis = future.result()
                elapsed = time.time() - _cluster_start
                if analysis:
                    cluster_analyses[cluster_name] = analysis
                    _log(f"  ✓ {cluster_name.capitalize()} cluster done ({_cluster_times.get(cluster_name, 0):.1f}s)")
                else:
                    _log(f"  ✗ {cluster_name.capitalize()} cluster FAILED")

        _log(f"PHASE 2 COMPLETE: {sum(1 for v in cluster_analyses.values() if v)}/5 clusters", _cluster_start)

    # =========================================================================
    # PHASE 3: Final Synthesis
    # Combine everything into the final dossier
    # =========================================================================

    enrichment_str = json.dumps(enrichment, indent=2, default=str) if enrichment else "No enrichment data"
    following_str = "\n\n---\n\n".join(following_analyses) if following_analyses else "No following data analyzed"
    articles_str = json.dumps(results.articles, indent=2, default=str) if results.articles else "No articles found"

    if question_ctx:
        # Simulation mode: use SIMULATION_SYNTHESIS_PROMPT
        _log("PHASE 3: Synthesizing simulation response...")
        _synth_start = _time.time()

        # Combine all available cluster analyses into one block
        cluster_parts = []
        for cname in ["sports", "entertainment", "causes", "network", "hidden"]:
            analysis = cluster_analyses.get(cname)
            if analysis:
                cluster_parts.append(f"### {cname.upper()} CLUSTER:\n{analysis}")
            else:
                priority_key = _cluster_priority_map.get(cname, cname)
                priority = question_ctx.cluster_priorities.get(priority_key, "useful")
                if priority == "skip":
                    cluster_parts.append(f"### {cname.upper()} CLUSTER:\n(Skipped — not relevant to question)")
                else:
                    cluster_parts.append(f"### {cname.upper()} CLUSTER:\nNo data available")

        cluster_combined = "\n\n".join(cluster_parts)

        # Build question context summary for the prompt
        q_context_str = f"""Question: {question_ctx.question}
Specific signals to look for: {', '.join(question_ctx.specific_signals) if question_ctx.specific_signals else 'general'}
Critical clusters: {', '.join(k for k, v in question_ctx.cluster_priorities.items() if v == 'critical')}
Additional focus: {question_ctx.additional_focus}"""

        synthesis_prompt = SIMULATION_SYNTHESIS_PROMPT.format(
            question=question_ctx.question,
            question_context=q_context_str,
            enrichment_data=enrichment_str,
            following_analyses=following_str,
            cluster_analyses_combined=cluster_combined,
            articles_data=articles_str
        )
    else:
        # Standard dossier mode
        _log("PHASE 3: Synthesizing final dossier...")
        _synth_start = _time.time()

        synthesis_prompt = SYNTHESIS_PROMPT.format(
            enrichment_data=enrichment_str,
            following_analyses=following_str,
            sports_cluster=cluster_analyses.get("sports") or "No sports analysis available",
            entertainment_cluster=cluster_analyses.get("entertainment") or "No entertainment analysis available",
            causes_cluster=cluster_analyses.get("causes") or "No causes analysis available",
            network_cluster=cluster_analyses.get("network") or "No network analysis available",
            hidden_cluster=cluster_analyses.get("hidden") or "No hidden interests analysis available",
            articles_data=articles_str
        )

    # Generate final output
    dossier = llm_call(synthesis_prompt)

    mode_label = "Simulation" if question_ctx else "Synthesis"
    _log(f"PHASE 3 COMPLETE: {mode_label} done", _synth_start)
    _log(f"=== TOTAL LLM TIME: {_time.time() - _start_total:.1f}s ===")

    return dossier


# Legacy functions for backwards compatibility
def generate_dossier_gemini(data: Dict) -> Optional[str]:
    """Legacy: Generate dossier using Google Gemini."""
    prompt = DOSSIER_PROMPT.format(data=json.dumps(data, indent=2, default=str))
    return _call_gemini(prompt)


def generate_dossier_openai(data: Dict) -> Optional[str]:
    """Legacy: Generate dossier using OpenAI."""
    prompt = DOSSIER_PROMPT.format(data=json.dumps(data, indent=2, default=str))
    return _call_openai(prompt)


def generate_dossier_anthropic(data: Dict) -> Optional[str]:
    """Legacy: Generate dossier using Anthropic Claude."""
    prompt = DOSSIER_PROMPT.format(data=json.dumps(data, indent=2, default=str))
    return _call_anthropic(prompt)


def _legacy_generate_dossier(results: ResearchResults, llm: str = "auto", verbose: bool = True) -> Optional[str]:
    """Legacy single-call dossier generation (not recommended)."""
    data = {}
    if results.enrichment:
        data["enrichment"] = results.enrichment
    if results.following_twitter:
        data["following_twitter"] = results.following_twitter
    if results.following_instagram:
        data["following_instagram"] = results.following_instagram
    if results.articles:
        data["articles"] = results.articles

    if not data:
        if verbose:
            print("\n⚠ No data available to generate dossier")
        return None

    if verbose:
        print("\n[LLM] Generating dossier...")

    # Try LLMs in order of preference
    generators = []
    if llm == "auto":
        generators = [
            ("gemini", generate_dossier_gemini),
            ("openai", generate_dossier_openai),
            ("anthropic", generate_dossier_anthropic)
        ]
    elif llm == "gemini":
        generators = [("gemini", generate_dossier_gemini)]
    elif llm == "openai":
        generators = [("openai", generate_dossier_openai)]
    elif llm == "anthropic":
        generators = [("anthropic", generate_dossier_anthropic)]

    for name, generator in generators:
        if verbose:
            print(f"  Trying {name}...")
        result = generator(data)
        if result:
            if verbose:
                print(f"  ✓ Generated with {name}")
            return result

    if verbose:
        print("  ⚠ No LLM available. Set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY")
    return None


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    # Check if setup is complete
    if not check_setup():
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Nyne Deep Research - Comprehensive person intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Best: provide both email AND LinkedIn
    python deep_research.py --email "ceo@company.com" --linkedin "https://linkedin.com/in/ceo"

    # Minimum: at least one identifier
    python deep_research.py --email "ceo@company.com"
    python deep_research.py --linkedin "https://linkedin.com/in/username"

    # Save to file
    python deep_research.py --email "ceo@company.com" --linkedin "https://linkedin.com/in/ceo" -o dossier.md

    # Raw JSON (no LLM)
    python deep_research.py --email "ceo@company.com" --json -o raw.json

    # Simulation mode: how would this person respond to a question?
    python deep_research.py --email "ceo@company.com" --question "What do they think about AI replacing jobs?"
    python deep_research.py --email "ceo@company.com" --question "How would they react to a cold pitch about our startup?" -o simulation.md

    # Batch simulation: same question across many people
    python deep_research.py --batch people.csv --question "What do they think about AI?" --batch-output results/
    python deep_research.py --batch emails.txt --question "How do they feel about remote work?"

Environment Variables:
    NYNE_API_KEY        Your Nyne.ai API key (required)
    NYNE_API_SECRET     Your Nyne.ai API secret (required)
    GEMINI_API_KEY      Google Gemini API key (for dossier)
    OPENAI_API_KEY      OpenAI API key (for dossier)
    ANTHROPIC_API_KEY   Anthropic API key (for dossier)

Get your Nyne.ai API keys at: https://nyne.ai
        """
    )
    parser.add_argument("--email", help="Person's email address")
    parser.add_argument("--linkedin", help="LinkedIn profile URL")
    parser.add_argument("--twitter", help="Twitter/X profile URL (for psychographics)")
    parser.add_argument("--instagram", help="Instagram profile URL (for psychographics)")
    parser.add_argument("--name", help="Person's full name (auto-extracted from enrichment)")
    parser.add_argument("--company", help="Person's company (auto-extracted from enrichment)")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of dossier")
    parser.add_argument("--llm", choices=["gemini", "openai", "anthropic", "auto"],
                       default="auto", help="LLM for dossier (default: auto)")
    parser.add_argument("--backup-llm", choices=["gemini", "openai", "anthropic"],
                       default=None, help="Backup LLM if primary fails/rate-limited (e.g., --backup-llm openai)")
    parser.add_argument("--question", help="Simulate how this person would respond to a question (enables simulation mode)")
    parser.add_argument("--batch", help="CSV or TXT file of people — runs the same --question against each person. CSV: 'email'/'linkedin' columns. TXT: one email or LinkedIn URL per line.")
    parser.add_argument("--batch-output", help="Output directory for batch results (default: batch_results/)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output")

    args = parser.parse_args()

    # Set backup LLM if provided
    if args.backup_llm:
        set_backup_llm(args.backup_llm)
        if not args.quiet:
            print(f"  Backup LLM: {args.backup_llm}")

    # ---- BATCH MODE ----
    if args.batch:
        if not args.question:
            parser.error("--batch requires --question (the question to simulate for each person)")

        import csv

        batch_dir = args.batch_output or "batch_results"
        os.makedirs(batch_dir, exist_ok=True)

        batch_file = args.batch
        rows = []

        if batch_file.endswith(".csv"):
            # CSV with headers
            with open(batch_file, newline="") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        elif batch_file.endswith(".txt"):
            # Plain text — one email or LinkedIn URL per line
            with open(batch_file) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "linkedin.com" in line:
                        rows.append({"linkedin": line})
                    else:
                        rows.append({"email": line})
        else:
            parser.error("--batch file must be .csv or .txt")

        if not rows:
            print("⚠ Batch file is empty")
            sys.exit(1)

        # Validate columns
        has_email = "email" in rows[0]
        has_linkedin = "linkedin" in rows[0]
        if not has_email and not has_linkedin:
            parser.error("Batch file must contain email addresses or LinkedIn URLs")

        print("=" * 60)
        print(f"BATCH SIMULATION: {len(rows)} people")
        print(f"Question: {args.question}")
        print(f"Output: {batch_dir}/")
        print("=" * 60)

        summary_rows = []

        for i, row in enumerate(rows):
            email = row.get("email", "").strip() or None
            linkedin = row.get("linkedin", "").strip() or None

            if not email and not linkedin:
                print(f"\n[{i+1}/{len(rows)}] ⚠ Skipping row — no email or linkedin")
                continue

            identifier = email or linkedin
            print(f"\n[{i+1}/{len(rows)}] Researching: {identifier}")

            try:
                result = research_person(
                    email=email,
                    linkedin_url=linkedin,
                    twitter_url=row.get("twitter", "").strip() or None,
                    instagram_url=row.get("instagram", "").strip() or None,
                    question=args.question,
                    llm=args.llm,
                    verbose=not args.quiet
                )

                simulation = result.get("simulation", "")
                raw_data = result.get("data", {})
                enrichment = raw_data.get("enrichment", {})
                person_result = enrichment.get("result", {})
                person_name = f"{person_result.get('firstname', '')} {person_result.get('lastname', '')}".strip() or "Unknown"

                # Save individual file
                safe_name = person_name.replace(" ", "_").replace("/", "_")[:50]
                filename = f"{safe_name}.md"
                filepath = os.path.join(batch_dir, filename)

                with open(filepath, "w") as f:
                    f.write(f"# Simulation: {person_name}\n\n")
                    f.write(f"**Email:** {email or 'N/A'}\n")
                    f.write(f"**LinkedIn:** {linkedin or 'N/A'}\n")
                    f.write(f"**Question:** {args.question}\n\n---\n\n")
                    f.write(simulation or "No simulation generated.")

                # Extract structured data from AT A GLANCE for summary
                sentiment = "Unknown"
                short_answer = ""
                if simulation:
                    for line in simulation.split("\n"):
                        if line.strip().startswith("**Sentiment:**"):
                            sentiment = line.split("**Sentiment:**")[1].strip()
                        elif line.strip().startswith("**Short Answer:**"):
                            short_answer = line.split("**Short Answer:**")[1].strip()

                summary_rows.append({
                    "name": person_name,
                    "email": email or "",
                    "linkedin": linkedin or "",
                    "sentiment": sentiment,
                    "short_answer": short_answer,
                    "file": filename
                })

                print(f"  ✓ {person_name} → {sentiment}")

            except Exception as e:
                print(f"  ✗ Error: {e}")
                summary_rows.append({
                    "name": identifier,
                    "email": email or "",
                    "linkedin": linkedin or "",
                    "sentiment": "ERROR",
                    "short_answer": str(e),
                    "file": ""
                })

        # Write summary CSV
        summary_path = os.path.join(batch_dir, "_summary.csv")
        with open(summary_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["name", "email", "linkedin", "sentiment", "short_answer", "file"])
            writer.writeheader()
            writer.writerows(summary_rows)

        # Write summary markdown
        summary_md_path = os.path.join(batch_dir, "_summary.md")
        with open(summary_md_path, "w") as f:
            f.write(f"# Batch Simulation Summary\n\n")
            f.write(f"**Question:** {args.question}\n")
            f.write(f"**People:** {len(rows)}\n")
            f.write(f"**Completed:** {len(summary_rows)}\n\n")
            f.write("| Name | Sentiment | Short Answer |\n")
            f.write("|------|-----------|-------------|\n")
            for row in summary_rows:
                f.write(f"| [{row['name']}]({row['file']}) | {row['sentiment']} | {row['short_answer'][:80]} |\n")

        print(f"\n{'=' * 60}")
        print(f"✓ BATCH COMPLETE: {len(summary_rows)}/{len(rows)} people")
        print(f"  Summary CSV: {summary_path}")
        print(f"  Summary MD:  {summary_md_path}")
        print(f"  Individual:  {batch_dir}/")
        print(f"{'=' * 60}")
        return

    # ---- SINGLE PERSON MODE ----
    if not args.email and not args.linkedin:
        parser.error("At least --email or --linkedin is required (or use --batch for batch mode)")

    input_data = ResearchInput(
        email=args.email,
        linkedin_url=args.linkedin,
        twitter_url=args.twitter,
        instagram_url=args.instagram,
        name=args.name,
        company=args.company
    )

    results = deep_research(input_data, verbose=not args.quiet)

    if args.json:
        output = json.dumps({
            "enrichment": results.enrichment,
            "following_twitter": results.following_twitter,
            "following_instagram": results.following_instagram,
            "articles": results.articles
        }, indent=2, default=str)
    else:
        output = generate_dossier(results, llm=args.llm, verbose=not args.quiet, question=args.question)
        if not output:
            output = "# No dossier generated\n\nEither no data was found or no LLM API key is configured."

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        if not args.quiet:
            print(f"\nSaved to: {args.output}")
    else:
        print("\n" + output)


# ============================================================================
# PROGRAMMATIC API
# ============================================================================

def research_person(
    email: str = None,
    linkedin_url: str = None,
    twitter_url: str = None,
    instagram_url: str = None,
    name: str = None,
    company: str = None,
    generate_dossier_flag: bool = True,
    llm: str = "auto",
    verbose: bool = False,
    question: str = None
) -> Dict[str, Any]:
    """
    Programmatic API for deep research.

    Example:
        from deep_research import research_person
        result = research_person(email="ceo@startup.com")
        print(result['dossier'])

        # Simulation mode:
        result = research_person(email="ceo@startup.com", question="What do they think about AI?")
        print(result['simulation'])
    """
    input_data = ResearchInput(
        email=email,
        linkedin_url=linkedin_url,
        twitter_url=twitter_url,
        instagram_url=instagram_url,
        name=name,
        company=company
    )

    results = deep_research(input_data, verbose=verbose)

    output = {
        "data": {
            "enrichment": results.enrichment,
            "following_twitter": results.following_twitter,
            "following_instagram": results.following_instagram,
            "articles": results.articles
        }
    }

    if generate_dossier_flag:
        result = generate_dossier(results, llm=llm, verbose=verbose, question=question)
        if question:
            output["simulation"] = result
        else:
            output["dossier"] = result

    return output


if __name__ == "__main__":
    main()
