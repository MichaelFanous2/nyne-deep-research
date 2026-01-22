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
import requests
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
    following: Optional[Dict] = None
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
    Submit request to get who someone follows on Twitter/X.
    Returns request_id or None if failed.
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

    # Twitter following
    if input_data.twitter_url:
        req_id = submit_following(input_data.twitter_url, headers)
        if req_id:
            request_ids["following"] = req_id
            if verbose:
                print("  ✓ Twitter following request submitted")

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
        "following": "/person/interactions",
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

        # Extract Twitter and fetch following if not already done
        if "following" not in request_ids:
            social_profiles = result_data.get("social_profiles", {})
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
                        results.following = result
                        if verbose:
                            print("  ✓ Following: completed")

    if verbose:
        print("\n[3/3] Research complete!")
        print("=" * 60)

    return results


# ============================================================================
# LLM DOSSIER GENERATION
# ============================================================================

DOSSIER_PROMPT = '''You are an elite intelligence analyst. Create an exhaustive, deeply researched dossier on this person.

RULES:
1. EVERY insight MUST be attributed to a specific data point [Source: ...]
2. Be specific - use exact quotes, dates, company names, follower counts
3. Focus on "creepy good" insights - things that show deep research
4. Include conversation starters that reference specific posts/follows/articles
5. When analyzing the "following" data, cluster the accounts they follow into categories

STRUCTURE:
## 1. IDENTITY SNAPSHOT
- Full name, nicknames, current role, locations, age estimate

## 2. CAREER DNA
- Complete trajectory with timeline
- Their "superpower" - what they're known for

## 3. PSYCHOGRAPHIC PROFILE (from Twitter Following)
- Core archetypes (Builder, Intellectual, Networker, etc.)
- Interests and values (inferred from who they follow)
- Cluster analysis: Group accounts into categories (VCs, Founders, Tech, Media, etc.)

## 4. HIDDEN INTERESTS
- Unexpected follows revealing personal interests
- Sports, music, hobbies
- Low-follower accounts (personal relationships)

## 5. KEY INFLUENCERS THEY FOLLOW
- Top 15 most notable accounts with follower counts

## 6. CONTENT ANALYSIS (from posts)
- Topics they post about
- Tone and style
- Recent wins and frustrations

## 7. CONVERSATION STARTERS
15+ specific hooks based on their follows, posts, and career

## 8. WARNINGS & LANDMINES
- Topics to avoid

## 9. "CREEPY GOOD" INSIGHTS
- Unusual patterns most people miss

HERE IS THE DATA:
{data}

Create the dossier now:'''


def generate_dossier_gemini(data: Dict) -> Optional[str]:
    """Generate dossier using Google Gemini."""
    if not GEMINI_API_KEY:
        return None
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(
            'gemini-2.0-flash',
            generation_config={"temperature": 0.7, "max_output_tokens": 32768}
        )
        prompt = DOSSIER_PROMPT.format(data=json.dumps(data, indent=2, default=str))
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        return None


def generate_dossier_openai(data: Dict) -> Optional[str]:
    """Generate dossier using OpenAI."""
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = DOSSIER_PROMPT.format(data=json.dumps(data, indent=2, default=str))
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=16000
        )
        return response.choices[0].message.content
    except Exception:
        return None


def generate_dossier_anthropic(data: Dict) -> Optional[str]:
    """Generate dossier using Anthropic Claude."""
    if not ANTHROPIC_API_KEY:
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        prompt = DOSSIER_PROMPT.format(data=json.dumps(data, indent=2, default=str))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=16000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception:
        return None


def generate_dossier(results: ResearchResults, llm: str = "auto", verbose: bool = True) -> Optional[str]:
    """
    Generate intelligent dossier using an LLM.
    Returns None if no LLM available or generation fails.
    """
    # Compile data
    data = {}
    if results.enrichment:
        data["enrichment"] = results.enrichment
    if results.following:
        data["following"] = results.following
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
    parser.add_argument("--twitter", help="Twitter/X profile URL")
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
        name=args.name,
        company=args.company
    )

    results = deep_research(input_data, verbose=not args.quiet)

    if args.json:
        output = json.dumps({
            "enrichment": results.enrichment,
            "following": results.following,
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
        name=name,
        company=company
    )

    results = deep_research(input_data, verbose=verbose)

    output = {
        "data": {
            "enrichment": results.enrichment,
            "following": results.following,
            "articles": results.articles
        }
    }

    if generate_dossier_flag:
        output["dossier"] = generate_dossier(results, llm=llm, verbose=verbose)

    return output


if __name__ == "__main__":
    main()
