"""
Test: Insufficient signal detection.
Asks a question that cannot be derived from social data.

Run:  python tests/test_keith_socks.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from deep_research import research_person

QUESTION = "What is his favorite sock brand?"
LINKEDIN = "https://www.linkedin.com/in/keith"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "keith_socks_simulation.md")


def main():
    print("=" * 60)
    print("INSUFFICIENT SIGNAL TEST: Keith's favorite sock brand")
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
        print("\n⚠ No simulation generated.")
        sys.exit(1)

    with open(OUTPUT_FILE, "w") as f:
        f.write(f"# Insufficient Signal Test: Favorite Sock Brand\n\n")
        f.write(f"**LinkedIn:** {LINKEDIN}\n")
        f.write(f"**Question:** {QUESTION}\n")
        f.write(f"**Generated in:** {elapsed:.1f}s\n\n---\n\n")
        f.write(simulation)

    print(f"\n{'=' * 60}")
    print(f"✓ Done ({elapsed:.1f}s, {len(simulation)} chars)")
    print(f"  Saved to: {OUTPUT_FILE}")
    print(f"{'=' * 60}\n")

    # Check if it detected insufficient signal
    if "Insufficient Data" in simulation:
        print("✓ PASSED: Correctly identified insufficient signal!")
    elif "SIMULATED RESPONSE" in simulation:
        print("⚠ WARNING: Generated a full simulation — may be hallucinating")

    print("\n--- FULL OUTPUT ---\n")
    print(simulation)


if __name__ == "__main__":
    main()
