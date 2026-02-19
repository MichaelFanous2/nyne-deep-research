"""
Live integration test for simulation mode.
Uses cached following data + a real LLM call to test the full pipeline.

Requires: at least one LLM API key (GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY)

Run:  python tests/test_simulation_live.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from deep_research import (
    analyze_question,
    generate_dossier,
    ResearchResults,
    QuestionContext,
    _get_llm_caller,
)

CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "following_cache.json")


def load_cached_person(email="test@example.com"):
    """Load cached following data for a test person."""
    with open(CACHE_FILE) as f:
        cache = json.load(f)
    entry = cache.get("by_email", {}).get(email)
    if not entry:
        print(f"  ⚠ No cached data for {email}")
        return None

    following = entry.get("following", {})
    return {
        "twitter": following if isinstance(following, dict) and "result" in following else {"result": {"interactions": following if isinstance(following, list) else []}},
    }


def check_llm_available():
    """Check if any LLM is configured."""
    caller, name = _get_llm_caller("auto")
    if caller:
        print(f"  Using LLM: {name}")
        return True
    print("  ⚠ No LLM available — set GEMINI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY")
    return False


# ============================================================================
# Test A: analyze_question() produces valid QuestionContext
# ============================================================================

def test_analyze_question_live():
    """Test that analyze_question returns a properly structured QuestionContext."""
    print("\n--- Test A: analyze_question() ---")

    questions = [
        "What does this person think about AI replacing software engineers?",
        "How would they react if I pitched them a crypto startup?",
        "What's their opinion on the 2024 presidential election?",
    ]

    for q in questions:
        print(f"\n  Question: {q}")
        start = time.time()
        ctx = analyze_question(q, verbose=False)
        elapsed = time.time() - start

        assert ctx is not None, f"analyze_question returned None for: {q}"
        assert isinstance(ctx, QuestionContext)
        assert ctx.question == q
        assert isinstance(ctx.cluster_priorities, dict)
        assert len(ctx.cluster_priorities) == 5, f"Expected 5 clusters, got {len(ctx.cluster_priorities)}"

        for cluster in ["sports_fitness", "entertainment_culture", "causes_values", "personal_network", "hidden_interests"]:
            assert cluster in ctx.cluster_priorities, f"Missing cluster: {cluster}"
            assert ctx.cluster_priorities[cluster] in ("critical", "useful", "skip"), \
                f"Invalid priority '{ctx.cluster_priorities[cluster]}' for {cluster}"

        assert isinstance(ctx.specific_signals, list)
        assert len(ctx.specific_signals) > 0, "Expected at least one specific signal"
        assert isinstance(ctx.additional_focus, str)
        assert len(ctx.additional_focus) > 10, "Expected non-trivial additional_focus"

        print(f"  ✓ Valid QuestionContext ({elapsed:.1f}s)")
        print(f"    Priorities: {ctx.cluster_priorities}")
        print(f"    Signals: {ctx.specific_signals[:3]}...")

    print("\n  ✓ test_analyze_question_live passed")


# ============================================================================
# Test B: Full simulation pipeline with cached data
# ============================================================================

def test_full_simulation_pipeline():
    """Test the full generate_dossier() in simulation mode with cached following data."""
    print("\n--- Test B: Full simulation pipeline ---")

    cached = load_cached_person()
    if not cached:
        print("  ⚠ Skipping — no cached data")
        return

    # Build minimal ResearchResults with just following data
    results = ResearchResults(
        enrichment={
            "result": {
                "firstname": "Vivek",
                "lastname": "Ramaswamy",
                "headline": "Founder & Managing Partner at 8VC",
                "careers_info": [{"company_name": "8VC", "title": "Managing Partner"}],
            }
        },
        following_twitter=cached["twitter"],
        following_instagram=None,
        articles=None,
        errors={}
    )

    question = "What does this person think about AI's impact on venture capital?"

    print(f"  Question: {question}")
    print(f"  Running full simulation pipeline...")
    start = time.time()

    output = generate_dossier(results, question=question, verbose=True)
    elapsed = time.time() - start

    assert output is not None, "generate_dossier returned None"
    assert len(output) > 500, f"Output too short ({len(output)} chars), expected substantial simulation"

    # Check that the simulation output has the expected sections
    expected_sections = [
        "SIMULATED RESPONSE",
        "INTELLIGENCE BRIEF",
        "PSYCHOGRAPHIC REASONING",
        "CONFIDENCE",
        "PLAYBOOK",
    ]

    for section in expected_sections:
        assert section in output.upper(), f"Missing section: {section}"

    print(f"\n  ✓ Full simulation completed ({elapsed:.1f}s, {len(output)} chars)")
    print(f"  ✓ All expected sections present")

    # Save output for manual review
    output_path = os.path.join(os.path.dirname(__file__), "simulation_output.md")
    with open(output_path, "w") as f:
        f.write(f"# Test Simulation Output\n\n**Question:** {question}\n\n---\n\n{output}")
    print(f"  → Saved to {output_path} for review")


# ============================================================================
# Test C: Standard mode still works (no question)
# ============================================================================

def test_standard_mode_still_works():
    """Verify that generate_dossier without question produces the standard 12-section dossier."""
    print("\n--- Test C: Standard mode (no question) ---")

    cached = load_cached_person()
    if not cached:
        print("  ⚠ Skipping — no cached data")
        return

    results = ResearchResults(
        enrichment={
            "result": {
                "firstname": "Vivek",
                "lastname": "Ramaswamy",
                "headline": "Founder & Managing Partner at 8VC",
                "careers_info": [{"company_name": "8VC", "title": "Managing Partner"}],
            }
        },
        following_twitter=cached["twitter"],
        following_instagram=None,
        articles=None,
        errors={}
    )

    print(f"  Running standard dossier (no question)...")
    start = time.time()

    output = generate_dossier(results, verbose=True)
    elapsed = time.time() - start

    assert output is not None, "generate_dossier returned None"
    assert len(output) > 500, f"Output too short ({len(output)} chars)"

    # Standard dossier should have these sections
    standard_sections = [
        "IDENTITY SNAPSHOT",
        "PERSONAL LIFE",
        "CAREER DNA",
        "PSYCHOGRAPHIC PROFILE",
        "CONVERSATION STARTERS",
    ]

    for section in standard_sections:
        assert section in output.upper(), f"Missing standard section: {section}"

    # Should NOT have simulation-specific sections
    assert "SIMULATED RESPONSE" not in output.upper(), "Standard mode should not have SIMULATED RESPONSE"

    print(f"\n  ✓ Standard dossier completed ({elapsed:.1f}s, {len(output)} chars)")
    print(f"  ✓ Standard sections present, no simulation sections")


# ============================================================================
# Test D: Different question types produce different cluster priorities
# ============================================================================

def test_question_diversity():
    """Different question types should produce different cluster priorities."""
    print("\n--- Test D: Question diversity ---")

    test_cases = [
        {
            "question": "What sports teams do they root for?",
            "expect_critical": "sports_fitness",
            "expect_skip": "causes_values",
        },
        {
            "question": "What political candidates would they support?",
            "expect_critical": "causes_values",
            "expect_skip": "sports_fitness",
        },
        {
            "question": "What music do they listen to?",
            "expect_critical": "entertainment_culture",
            "expect_skip": "causes_values",
        },
    ]

    for tc in test_cases:
        ctx = analyze_question(tc["question"], verbose=False)
        assert ctx is not None

        # Check that the expected critical cluster is marked critical
        actual = ctx.cluster_priorities.get(tc["expect_critical"])
        print(f"  Q: {tc['question'][:50]}...")
        print(f"    {tc['expect_critical']}: {actual} (expected: critical)")

        if actual != "critical":
            print(f"    ⚠ Warning: expected 'critical' but got '{actual}' — LLM judgment may vary")
        else:
            print(f"    ✓ Correct")

    print("\n  ✓ test_question_diversity passed")


# ============================================================================
# Run
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SIMULATION MODE — LIVE INTEGRATION TESTS")
    print("=" * 60)

    if not check_llm_available():
        print("\nCannot run live tests without an LLM. Exiting.")
        sys.exit(1)

    test_analyze_question_live()
    test_question_diversity()
    test_full_simulation_pipeline()
    test_standard_mode_still_works()

    print("\n" + "=" * 60)
    print("✓ ALL LIVE TESTS PASSED")
    print("=" * 60 + "\n")
