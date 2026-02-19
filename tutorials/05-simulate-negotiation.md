# Tutorial 5: Simulate the Negotiation

> **High-stakes, immediately useful.**

## What You're Showing

You're about to negotiate a deal. Practice against a realistic simulation of the other side. Deep research the counterparty. Feed the dossier into Claude. The AI pushes back realistically based on their actual personality, priorities, and communication style.

## Setup Before Recording

- Pick a negotiation scenario (partnership deal, contract renewal, salary negotiation, M&A)
- Have the counterparty's email/LinkedIn
- Know what you want out of the negotiation

## Demo Script

### Step 1: Set the Scene

```
I'm negotiating a [deal type] with [Name] at [Company] next Thursday. I need to practice against someone who actually thinks like them — not a generic adversary. Let me start with deep research.
```

### Step 2: Run Deep Research

```
python deep_research.py --email "{email}" --linkedin "{linkedin}" --output counterparty.md
```

### Step 3: Extract Negotiation-Relevant Intel

Focus on these dossier sections:

**Psychographic Profile:**
```
"Analytical, risk-averse, values precision over speed. They'll want data. They'll want time to think. Don't pressure for a same-day close."
```

**Content & Voice Analysis:**
```
"Their LinkedIn posts are methodical, data-heavy. They never use superlatives. They distrust bold claims. Match their tone — measured, evidence-based."
```

**Warnings & Landmines:**
```
"They've posted about being burned by vendors who over-promised. They hate aggressive sales tactics. If I push too hard, they'll shut down."
```

**Interest Clusters:**
```
"They follow cost-optimization accounts, frugality content. Price sensitivity is real — I need to lead with value, not features."
```

### Step 4: Build the Negotiation Strategy

```
Based on this dossier, help me build a negotiation strategy. I want [your goal]. What's my best approach given their personality, priorities, and communication style? What are they likely to push back on? What leverage do I have?
```

### Step 5: Run the Negotiation Simulation

```
Now become this person for a negotiation simulation. Use their communication style, priorities, and personality from the dossier. Push back where they would push back. Don't make it easy.

I'll start: "Thanks for making time for this. I wanted to discuss the terms of [the deal]..."
```

Run a full negotiation — at least 6-8 exchanges. Let the simulation:
- Stall on pricing (because dossier shows cost-consciousness)
- Request more data (because they're analytical)
- Push back on timeline (because they're risk-averse)
- Respond to rapport attempts based on real interests

### Step 6: Debrief and Strategy Adjustment

```
Break character. Give me a negotiation prep sheet:
1. Their likely priorities (ranked)
2. Where they'll push back hardest
3. My best concession to offer
4. The line I shouldn't cross
5. Best opening position
```

## Punchline

> "You've already heard their objections before they say them."

## Key Moments to Emphasize

- The psychographic profile directly informing negotiation strategy
- The simulation pushing back in a personality-specific way (not generic "I need a better price")
- The dossier catching a communication style mismatch before it happens
- The debrief producing a concrete, actionable negotiation playbook
