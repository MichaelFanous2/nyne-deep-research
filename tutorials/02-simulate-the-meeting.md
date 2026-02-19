# Tutorial 2: Simulate the Meeting Before It Happens

> **The flagship use case.**

## What You're Showing

Run deep research on a target, feed the dossier into Claude as a system prompt, and role-play the full meeting. Surface objections you didn't expect, shared interests you didn't know about, and rapport angles that feel natural — because they're based on real data.

## Setup Before Recording

- Pick a real meeting target (someone you're actually going to meet, or a well-known figure)
- Have their email and/or LinkedIn URL
- Know what you'd pitch or discuss with them

## Demo Script

### Step 1: Set the Scene

```
I have a meeting with [Name] at [Company] tomorrow. They're [title]. I want to simulate this meeting before it happens so I'm fully prepared. Let me run deep research first.
```

### Step 2: Run Deep Research

```
python deep_research.py --email "{email}" --linkedin "{linkedin}" --output dossier.md
```

As it runs, narrate what's happening:
- "Enriching their profile across 50+ platforms..."
- "Pulling their Twitter following list for psychographic analysis..."
- "Searching for articles and press mentions..."
- "Running 13 LLM calls to cluster and analyze everything..."

### Step 3: Walk Through the Dossier

Open the dossier and highlight the "holy shit" sections:

- **Personal Life & Hobbies** — "They're a competitive cyclist who follows @staborunn. They do woodworking on weekends."
- **Psychographic Profile** — "Their archetype is analytical-pragmatist. They value data over stories."
- **Interest Cluster Deep Dive** — "Look at this — they follow 12 cycling accounts, 8 jazz accounts, and 3 accounts related to education nonprofits."
- **Conversation Starters** — "30 ready-to-use openers organized by category."
- **Warnings & Landmines** — "They've posted about hating AI hype. Do NOT lead with 'AI-powered.'"
- **Approach Strategy** — "Best angle: lead with data, be direct, reference cycling casually."

### Step 4: Build the Simulation

```
Take this dossier and become this person for a meeting simulation. Respond as they would — use their communication style, reference their real interests and opinions, push back where they would push back, and flag any landmines I step on.

I'm going to pitch [your product/idea]. Let's run the meeting.
```

### Step 5: Run the Full Meeting

Have a real back-and-forth. Let the simulation:
- Push back on something based on a real opinion from the dossier
- Reference a specific interest naturally
- Catch you stepping on a landmine
- Ask questions the real person would actually ask

**Go for at least 5-6 exchanges** to show depth.

### Step 6: Debrief

```
Great. Now break character and give me a meeting prep summary:
1. What objections should I expect?
2. What rapport angles worked best?
3. What landmines did I hit or almost hit?
4. What's my best opening line for the real meeting?
```

## Punchline

> "You've already had the meeting before walking in the room."

## Key Moments to Emphasize

- The dossier revealing something surprising (a hobby, a strong opinion, a connection)
- The simulation pushing back in a way a generic AI never would
- A landmine being caught before it happens in real life
- The debrief producing actionable meeting prep
