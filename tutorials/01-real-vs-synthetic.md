# Tutorial 1: Real vs. Synthetic — The Simulation Showdown

> **The differentiator demo. Record this first.**

## What You're Showing

Side-by-side comparison: same meeting simulated with a generic AI persona vs. a Nyne-powered real persona. The synthetic gives bland, safe answers. The Nyne version references real opinions, pushes back on things they'd actually push back on, catches a landmine the synthetic misses.

## Setup Before Recording

- Pick a real person you have permission to demo (ideally someone with an active Twitter/X presence)
- Have their email and LinkedIn URL ready
- Have Claude Code open and ready

## Demo Script

### Step 1: Create the Synthetic Persona

Show what most AI simulation tools give you — a generic profile.

```
I want to simulate a meeting with a Tech VP. Create a generic system prompt for someone like this:
- Tech VP, 40s, based in SF
- Works at a mid-stage startup
- General interest in AI and engineering leadership
```

Claude will generate a bland, generic persona. Let it respond. Point out how generic it is.

### Step 2: Run a Quick Conversation with the Synthetic

```
Now role-play as this persona. I'm going to pitch you an AI-powered developer tool.

"Hi, thanks for taking the time. We've built an AI-powered code review platform that helps engineering teams ship faster. Would love to walk you through how it works."
```

**What to highlight:** The synthetic gives polite, generic responses. No real pushback. No personality. Could be anyone.

### Step 3: Now Run Deep Research on the Real Person

```
python deep_research.py --email "{their_email}" --linkedin "{their_linkedin}" --output dossier.md
```

Wait for the dossier to generate. Walk through the key sections:
- **Personal Life & Hobbies** — real interests, not guesses
- **Psychographic Profile** — how they actually think
- **Interest Cluster Deep Dive** — specific handles they follow
- **Warnings & Landmines** — things that would derail a meeting

### Step 4: Build the Real Persona

```
Now take this dossier and create a system prompt for simulating a meeting with this person. Use their actual personality, interests, communication style, and landmines. I want the AI to respond AS them.
```

Claude will build a rich, evidence-based persona from the dossier.

### Step 5: Run the Same Conversation

```
Same pitch. Role-play as this person based on the dossier.

"Hi, thanks for taking the time. We've built an AI-powered code review platform that helps engineering teams ship faster. Would love to walk you through how it works."
```

**What to highlight:**
- They push back on "AI-powered" because the dossier shows they hate that buzzword
- They reference something specific from their real experience
- They ask a pointed technical question the synthetic never would have
- A landmine gets caught that the synthetic completely missed

### Step 6: The Side-by-Side Reveal

Scroll up and show both conversations side by side. Point out:
- Synthetic: polite, generic, could be anyone
- Nyne: specific, opinionated, catches landmines, feels like a real person

## Punchline

> "Synthetic personas are guessing. Nyne knows."

## Key Moments to Emphasize

- The synthetic giving a bland "that sounds interesting" response
- The Nyne version pushing back with a specific objection rooted in real data
- The landmine that only shows up in the real persona
- The dossier evidence — actual handles, actual posts, actual opinions
