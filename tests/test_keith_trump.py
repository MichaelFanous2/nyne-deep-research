"""
Live test: Simulate Keith's opinion on Trump.
Uses deep research on linkedin.com/in/keith + simulation mode.

Run:  python tests/test_keith_trump.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from deep_research import research_person

QUESTION = "What does this person think about Donald Trump?"
LINKEDIN = "https://www.linkedin.com/in/keith"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "keith_trump_simulation.md")


def main():
    print("=" * 60)
    print("SIMULATION: Keith's opinion on Trump")
    print("=" * 60)
    print(f"  LinkedIn: {LINKEDIN}")
    print(f"  Question: {QUESTION}")
    print()

    start = time.time()
    result = research_person(
        linkedin_url=LINKEDIN,
        question=QUESTION,
        verbose=True
    )
    elapsed = time.time() - start

    simulation = result.get("simulation")
    if not simulation:
        print("\n⚠ No simulation generated. Check API keys and data availability.")
        sys.exit(1)

    # Save output
    with open(OUTPUT_FILE, "w") as f:
        f.write(f"# Simulation: Keith's Opinion on Trump\n\n")
        f.write(f"**LinkedIn:** {LINKEDIN}\n")
        f.write(f"**Question:** {QUESTION}\n")
        f.write(f"**Generated in:** {elapsed:.1f}s\n\n")
        f.write(f"---\n\n")
        f.write(simulation)

    print(f"\n{'=' * 60}")
    print(f"✓ Simulation complete ({elapsed:.1f}s, {len(simulation)} chars)")
    print(f"  Saved to: {OUTPUT_FILE}")
    print(f"{'=' * 60}\n")

    # Print a preview
    preview_lines = simulation.split("\n")[:30]
    print("--- PREVIEW (first 30 lines) ---\n")
    print("\n".join(preview_lines))
    print("\n--- END PREVIEW ---")


if __name__ == "__main__":
    main()
