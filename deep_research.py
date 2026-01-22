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
warnings.filterwarnings("ignore", category=FutureWarning, module="google.generativeai")
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
    """
    results = ResearchResults(errors={})
    request_ids = {}

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
    if input_data.twitter_url:
        req_id = submit_following(input_data.twitter_url, headers)
        if req_id:
            request_ids["following_twitter"] = req_id
            if verbose:
                print("  ✓ Twitter following request submitted")
    if input_data.instagram_url:
        req_id = submit_following(input_data.instagram_url, headers)
        if req_id:
            request_ids["following_instagram"] = req_id
            if verbose:
                print("  ✓ Instagram following request submitted")

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
                    print(f"  → Found Twitter: {twitter_url}")
                    print("  → Fetching following list...")

                req_id = submit_following(twitter_url, headers)
                if req_id:
                    result = poll_result("/person/interactions", req_id, headers)
                    if result:
                        results.following_twitter = result
                        if verbose:
                            print("  ✓ Following (Twitter): completed")

        # Try Instagram if not already fetched
        if "following_instagram" not in request_ids and not results.following_instagram:
            instagram = social_profiles.get("instagram", {})
            instagram_url = instagram.get("url")

            if instagram_url:
                if verbose:
                    print(f"  → Found Instagram: {instagram_url}")
                    print("  → Fetching following list...")

                req_id = submit_following(instagram_url, headers)
                if req_id:
                    result = poll_result("/person/interactions", req_id, headers)
                    if result:
                        results.following_instagram = result
                        if verbose:
                            print("  ✓ Following (Instagram): completed")

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
- Political/social leanings (if detectable)
- CLUSTER ANALYSIS: Group the accounts they follow into categories with specific handles:
  - VCs & Investors: @handle1, @handle2...
  - Founders & Operators: ...
  - AI/Tech Researchers: ...
  - Media & Journalists: ...
  - Sports/Entertainment: ...
  - Politics/Policy: ...
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

## 8. WARNINGS & LANDMINES
- Topics that might offend them
- Competitors or people they might dislike
- Sensitive career history
- Political hot buttons to avoid

## 9. "CREEPY GOOD" INSIGHTS
The insights that make them think "how did they know that?":
- Patterns in who they follow
- Connections between their posts and follows
- Personal details buried in the data
- Things most people would miss

## 10. SUMMARY: How to Connect With This Person
A brief synthesis: what they care about, how they think, and the best angle to approach them.

---

HERE IS ALL THE RAW DATA TO ANALYZE:
{data}

Now write the most thorough dossier possible. Be exhaustive. Go deep.'''


# ============================================================================
# BATCH ANALYSIS PROMPTS
# ============================================================================

BATCH_ANALYSIS_PROMPT = '''You are analyzing a batch of social media accounts that a person follows.

PERSON CONTEXT:
Name: {person_name}
Role: {person_role}
Company: {person_company}

ANALYZE THESE {batch_size} ACCOUNTS THEY FOLLOW (Batch {batch_num} of {total_batches}):
{batch_data}

For EACH account, provide:
1. Category (VC, Founder, AI/Tech, Media, Sports, Politics, Personal Friend, etc.)
2. Why this person likely follows them (relationship, shared interest, aspiration)
3. Notable insight (if any) - what does following this account reveal?
4. Follower count and verification status

Then provide a BATCH SUMMARY:
- Key themes in this batch
- Most notable/surprising follows
- Patterns you observe
- Potential conversation hooks based on these follows

Be thorough and specific. Use exact handles and follower counts.'''

SYNTHESIS_PROMPT = '''You are an elite intelligence analyst creating the DEFINITIVE dossier on this person.

You have access to:
1. Their full profile/enrichment data
2. Detailed analyses of EVERY account they follow (analyzed in batches)
3. Articles and press mentions

YOUR TASK: Synthesize all this research into the most comprehensive, insightful dossier ever written.

## ENRICHMENT DATA (Profile, Career, Posts):
{enrichment_data}

## FOLLOWING ANALYSES (Deep analysis of everyone they follow):
{following_analyses}

## ARTICLES & PRESS:
{articles_data}

---

Now write an EXHAUSTIVE dossier with these sections:

## 1. IDENTITY SNAPSHOT
Full name, role, company, location, age estimate. Include personal details (address, phone, car if available).

## 2. CAREER DNA
Complete trajectory with dates. For EACH role:
- What they actually did
- Why they made this move (infer from timing/context)
- Key relationships formed
Their "superpower" - what makes them uniquely valuable.

## 3. PSYCHOGRAPHIC DEEP DIVE
Based on the following analyses, explain WHO this person is:
- Core identity/archetypes
- Values and beliefs (with evidence)
- Aspirations (who do they want to be?)
- Political/social leanings
- Professional tribes they belong to

## 4. FOLLOWING ANALYSIS SYNTHESIS
Combine all batch analyses into:
- COMPLETE category breakdown with handles
- The most notable follows and why
- Unexpected/hidden interest follows
- Low-follower accounts (likely personal relationships)
- Patterns across all follows

## 5. CONTENT & VOICE ANALYSIS
From their posts:
- Topics they care about
- Communication style and tone
- Recent wins (with dates and quotes)
- Frustrations expressed (with quotes)
- Strong opinions they've stated

## 6. KEY RELATIONSHIPS (Top 25)
The 25 most important accounts they follow, with:
- Handle, name, follower count
- Likely nature of relationship
- Why this matters for approaching them

## 7. CONVERSATION STARTERS (25+)
Highly specific hooks referencing:
- Exact posts with dates
- Specific accounts they follow
- Career history details
- Hidden interests discovered
- Recent company news

## 8. WARNINGS & LANDMINES
- Sensitive topics
- Potential competitors/enemies
- Political hot buttons
- Career sore spots

## 9. "CREEPY GOOD" INSIGHTS
The insights that make them think "how did they know that?":
- Non-obvious patterns
- Cross-referenced discoveries
- Personal details
- Predictive insights about their behavior

## 10. APPROACH STRATEGY
How to connect with this person:
- Best angle/framing
- Shared connections to mention
- Topics that will resonate
- What to avoid

Go DEEP. Be SPECIFIC. This should be the most thorough research they've ever seen.'''


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
            'gemini-2.0-flash',
            generation_config={"temperature": 0.7, "max_output_tokens": 32768}
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return None


def _call_openai(prompt: str) -> Optional[str]:
    """Make a single OpenAI API call."""
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=16000
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
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception:
        return None


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


def _batch_following_data(following_data: Dict, batch_size: int = 75) -> list:
    """Split following data into batches."""
    interactions = following_data.get("result", {}).get("interactions", [])
    if not interactions:
        return []

    batches = []
    for i in range(0, len(interactions), batch_size):
        batches.append(interactions[i:i + batch_size])
    return batches


def generate_dossier(results: ResearchResults, llm: str = "auto", verbose: bool = True) -> Optional[str]:
    """
    Generate intelligent dossier using batched LLM calls for deep analysis.

    1. Batch the following lists into chunks
    2. Run concurrent LLM calls to analyze each batch
    3. Synthesize all analyses into final dossier
    """
    # Get LLM caller
    llm_call, llm_name = _get_llm_caller(llm)
    if not llm_call:
        if verbose:
            print("  ⚠ No LLM available. Set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY")
        return None

    if verbose:
        print(f"\n[LLM] Using {llm_name} for deep analysis...")

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
        if verbose:
            print(f"  Analyzing {len(all_following)} followed accounts in {len(batches)} batches...")

        # Prepare batch prompts
        batch_prompts = []
        for i, batch in enumerate(batches):
            batch_data = json.dumps(batch, indent=2, default=str)
            prompt = BATCH_ANALYSIS_PROMPT.format(
                person_name=person_name,
                person_role=person_role,
                person_company=person_company,
                batch_size=len(batch),
                batch_num=i + 1,
                total_batches=len(batches),
                batch_data=batch_data
            )
            batch_prompts.append((i, prompt))

        # Run batch analyses concurrently
        def analyze_batch(args):
            idx, prompt = args
            return idx, llm_call(prompt)

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(analyze_batch, bp): bp[0] for bp in batch_prompts}

            for future in as_completed(futures):
                idx, analysis = future.result()
                if analysis:
                    following_analyses.append((idx, analysis))
                    if verbose:
                        print(f"    ✓ Batch {idx + 1}/{len(batches)} analyzed")
                elif verbose:
                    print(f"    ✗ Batch {idx + 1}/{len(batches)} failed")

        # Sort by batch index
        following_analyses.sort(key=lambda x: x[0])
        following_analyses = [a[1] for a in following_analyses]

    # Prepare synthesis
    if verbose:
        print("  Synthesizing final dossier...")

    enrichment_str = json.dumps(enrichment, indent=2, default=str) if enrichment else "No enrichment data"
    following_str = "\n\n---\n\n".join(following_analyses) if following_analyses else "No following data analyzed"
    articles_str = json.dumps(results.articles, indent=2, default=str) if results.articles else "No articles found"

    synthesis_prompt = SYNTHESIS_PROMPT.format(
        enrichment_data=enrichment_str,
        following_analyses=following_str,
        articles_data=articles_str
    )

    # Generate final dossier
    dossier = llm_call(synthesis_prompt)

    if dossier and verbose:
        print("  ✓ Dossier complete!")

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
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output")

    args = parser.parse_args()

    if not args.email and not args.linkedin:
        parser.error("At least --email or --linkedin is required")

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
        output = generate_dossier(results, llm=args.llm, verbose=not args.quiet)
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
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Programmatic API for deep research.

    Example:
        from deep_research import research_person
        result = research_person(email="ceo@startup.com")
        print(result['dossier'])
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
        output["dossier"] = generate_dossier(results, llm=llm, verbose=verbose)

    return output


if __name__ == "__main__":
    main()
