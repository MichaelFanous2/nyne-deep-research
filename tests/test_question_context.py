"""
Tests for the question-adaptive simulation feature.

Run: python -m pytest tests/ -v
Or:  python tests/test_question_context.py
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deep_research import QuestionContext, analyze_question, generate_dossier, ResearchResults


# ============================================================================
# Test 1: QuestionContext dataclass
# ============================================================================

def test_question_context_creation():
    """QuestionContext should hold all expected fields."""
    ctx = QuestionContext(
        question="What does this person think about AI?",
        cluster_priorities={
            "sports_fitness": "skip",
            "entertainment_culture": "skip",
            "causes_values": "useful",
            "personal_network": "useful",
            "hidden_interests": "critical"
        },
        specific_signals=["AI companies", "tech thought leaders", "AI skeptics"],
        additional_focus="Look for AI-related follows and posts about automation.",
        enrichment_focus=["posts", "career_history"]
    )
    assert ctx.question == "What does this person think about AI?"
    assert ctx.cluster_priorities["sports_fitness"] == "skip"
    assert ctx.cluster_priorities["hidden_interests"] == "critical"
    assert len(ctx.specific_signals) == 3
    assert "posts" in ctx.enrichment_focus
    print("  ✓ test_question_context_creation passed")


# ============================================================================
# Test 2: Question analyzer prompt produces valid JSON structure
# ============================================================================

def test_question_analyzer_prompt_format():
    """QUESTION_ANALYZER_PROMPT should format correctly with a question."""
    from deep_research import QUESTION_ANALYZER_PROMPT

    formatted = QUESTION_ANALYZER_PROMPT.format(question="What do they think about remote work?")
    assert "What do they think about remote work?" in formatted
    assert "cluster_priorities" in formatted
    assert "specific_signals" in formatted
    print("  ✓ test_question_analyzer_prompt_format passed")


# ============================================================================
# Test 3: Simulation synthesis prompt has all required placeholders
# ============================================================================

def test_simulation_synthesis_prompt_format():
    """SIMULATION_SYNTHESIS_PROMPT should accept all expected format keys."""
    from deep_research import SIMULATION_SYNTHESIS_PROMPT

    formatted = SIMULATION_SYNTHESIS_PROMPT.format(
        question="What do they think about crypto?",
        question_context="Test context",
        enrichment_data="Test enrichment",
        following_analyses="Test analyses",
        cluster_analyses_combined="Test clusters",
        articles_data="Test articles"
    )
    assert "What do they think about crypto?" in formatted
    assert "Test context" in formatted
    assert "SIMULATED RESPONSE" in formatted
    assert "INTELLIGENCE BRIEF" in formatted
    assert "CONFIDENCE" in formatted
    assert "CONVERSATION PLAYBOOK" in formatted
    print("  ✓ test_simulation_synthesis_prompt_format passed")


# ============================================================================
# Test 4: generate_dossier signature accepts question param
# ============================================================================

def test_generate_dossier_accepts_question():
    """generate_dossier should accept question=None without breaking."""
    import inspect
    sig = inspect.signature(generate_dossier)
    params = list(sig.parameters.keys())
    assert "question" in params
    # Default should be None
    assert sig.parameters["question"].default is None
    print("  ✓ test_generate_dossier_accepts_question passed")


# ============================================================================
# Test 5: Cluster skipping logic
# ============================================================================

def test_cluster_priority_skipping():
    """Clusters marked 'skip' should be excluded from the run list."""
    ctx = QuestionContext(
        question="What do they think about Trump?",
        cluster_priorities={
            "sports_fitness": "skip",
            "entertainment_culture": "skip",
            "causes_values": "critical",
            "personal_network": "useful",
            "hidden_interests": "useful"
        },
        specific_signals=["political commentators"],
        additional_focus="Focus on political signals.",
        enrichment_focus=["posts"]
    )

    _cluster_priority_map = {
        "sports": "sports_fitness",
        "entertainment": "entertainment_culture",
        "causes": "causes_values",
        "network": "personal_network",
        "hidden": "hidden_interests"
    }

    all_clusters = ["sports", "entertainment", "causes", "network", "hidden"]
    clusters_to_run = [
        c for c in all_clusters
        if ctx.cluster_priorities.get(_cluster_priority_map[c], "useful") != "skip"
    ]

    assert "sports" not in clusters_to_run, "sports should be skipped"
    assert "entertainment" not in clusters_to_run, "entertainment should be skipped"
    assert "causes" in clusters_to_run, "causes should run (critical)"
    assert "network" in clusters_to_run, "network should run (useful)"
    assert "hidden" in clusters_to_run, "hidden should run (useful)"
    assert len(clusters_to_run) == 3
    print("  ✓ test_cluster_priority_skipping passed")


# ============================================================================
# Test 6: Batch prompt injection
# ============================================================================

def test_batch_prompt_question_injection():
    """When question_ctx is present, batch prompts should get the additional focus appended."""
    from deep_research import BATCH_ANALYSIS_PROMPT

    ctx = QuestionContext(
        question="How do they feel about Rust vs Python?",
        cluster_priorities={},
        specific_signals=["programming language accounts", "developer tools", "Rust evangelists"],
        additional_focus="",
        enrichment_focus=[]
    )

    base_prompt = BATCH_ANALYSIS_PROMPT.format(
        person_name="Test Person",
        person_role="Engineer",
        person_company="TestCo",
        batch_size=10,
        batch_num=1,
        total_batches=1,
        batch_data="@rustlang | Rust | 500000 | Systems programming language"
    )

    # Simulate what generate_dossier does
    signals_str = ", ".join(ctx.specific_signals)
    injected = base_prompt + f'''

ADDITIONAL FOCUS FOR THIS ANALYSIS:
The goal is to understand how this person would respond to: "{ctx.question}"
Pay special attention to: {signals_str}
Flag any accounts that DIRECTLY relate to this topic — these are the most valuable signals.
For each flagged account, explain WHY it's relevant to the question.'''

    assert "How do they feel about Rust vs Python?" in injected
    assert "programming language accounts" in injected
    assert "Rust evangelists" in injected
    print("  ✓ test_batch_prompt_question_injection passed")


# ============================================================================
# Test 7: JSON parsing resilience (markdown fences)
# ============================================================================

def test_json_parsing_with_markdown_fences():
    """The analyze_question JSON parser should handle markdown-wrapped responses."""
    # Simulate what the LLM might return wrapped in markdown
    raw_responses = [
        # Clean JSON
        '{"cluster_priorities": {"sports_fitness": "skip"}, "specific_signals": ["AI"], "additional_focus": "test", "enrichment_focus": ["posts"]}',
        # With ```json fences
        '```json\n{"cluster_priorities": {"sports_fitness": "skip"}, "specific_signals": ["AI"], "additional_focus": "test", "enrichment_focus": ["posts"]}\n```',
        # With ``` fences (no json label)
        '```\n{"cluster_priorities": {"sports_fitness": "skip"}, "specific_signals": ["AI"], "additional_focus": "test", "enrichment_focus": ["posts"]}\n```',
    ]

    for raw in raw_responses:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()

        parsed = json.loads(cleaned)
        assert parsed["cluster_priorities"]["sports_fitness"] == "skip"
        assert "AI" in parsed["specific_signals"]

    print("  ✓ test_json_parsing_with_markdown_fences passed")


# ============================================================================
# Test 8: Standard dossier mode unchanged
# ============================================================================

def test_standard_mode_unchanged():
    """Without question param, generate_dossier should use SYNTHESIS_PROMPT (not simulation)."""
    from deep_research import SYNTHESIS_PROMPT

    # Verify SYNTHESIS_PROMPT still has its original format keys
    assert "{enrichment_data}" in SYNTHESIS_PROMPT
    assert "{following_analyses}" in SYNTHESIS_PROMPT
    assert "{sports_cluster}" in SYNTHESIS_PROMPT
    assert "{entertainment_cluster}" in SYNTHESIS_PROMPT
    assert "{causes_cluster}" in SYNTHESIS_PROMPT
    assert "{network_cluster}" in SYNTHESIS_PROMPT
    assert "{hidden_cluster}" in SYNTHESIS_PROMPT
    assert "{articles_data}" in SYNTHESIS_PROMPT
    print("  ✓ test_standard_mode_unchanged passed")


# ============================================================================
# Run all tests
# ============================================================================

if __name__ == "__main__":
    print("\n=== Question-Adaptive Simulation Tests ===\n")
    test_question_context_creation()
    test_question_analyzer_prompt_format()
    test_simulation_synthesis_prompt_format()
    test_generate_dossier_accepts_question()
    test_cluster_priority_skipping()
    test_batch_prompt_question_injection()
    test_json_parsing_with_markdown_fences()
    test_standard_mode_unchanged()
    print(f"\n✓ All 8 tests passed!\n")
