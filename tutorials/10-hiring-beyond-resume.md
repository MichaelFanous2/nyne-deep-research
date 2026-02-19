# Tutorial 10: Hiring — Beyond the Resume

> **Broad appeal — everyone hires.**

## What You're Showing

Resumes tell you what someone did. Deep research tells you who someone is. Run deep research on a candidate. Personal Life & Hobbies, Social Graph, Interest Clusters. Culture fit based on real interests and values, not interview performance. Key Relationships — who do they surround themselves with?

## Setup Before Recording

- Pick a real or hypothetical candidate (someone with a public presence)
- Have their email and/or LinkedIn
- Know what role/culture you're hiring for (so you can show the fit analysis)

## Demo Script

### Step 1: Set the Scene

```
I'm hiring for a [role] on my team. I have a candidate — [Name]. Their resume looks great. But resumes are marketing documents. I want to know who this person actually is. Let me run deep research.
```

### Step 2: Run Deep Research

```
python deep_research.py --email "{email}" --linkedin "{linkedin}" --output candidate.md
```

### Step 3: What the Resume Didn't Tell You

Walk through the dossier:

**Personal Life & Hobbies:**
```
"The resume says 'Senior Engineer at [Company].' The dossier says they volunteer at a coding bootcamp for underrepresented communities, they do competitive bouldering, and they're building a side project in Rust. This tells me they're a builder and a giver — not just an employee."
```

**Interest Clusters:**
```
"Tech: they follow Rust accounts, systems programming, performance optimization. Not just surface-level 'I like coding.' Causes: education equity, DEI in tech. Personal: rock climbing, craft beer, board games. This is a full human being."
```

**Psychographic Profile:**
```
"Archetype: builder-educator. Values depth over breadth. Communicates directly. Dislikes corporate jargon. This tells me more about culture fit than any interview question."
```

### Step 4: Culture Fit Analysis

```
My team values: [list your real team values — e.g., ownership, curiosity, directness, mission-driven]. Based on this dossier, how does this candidate align with our culture? Where are they a strong fit? Where might there be friction?
```

Let Claude do a real analysis against your team values.

### Step 5: Social Graph — Who Do They Surround Themselves With?

```
Look at their Key Relationships and Social Graph. Who do they surround themselves with? What does that tell us about the kind of professional they are?
```

Show how their connections reveal:
- Mentors and influences
- Peer group caliber
- Community involvement
- Industry connections

### Step 6: Better Interview Questions

```
Based on this dossier, give me 5 interview questions that go beyond the resume. Questions that probe their real values, motivations, and fit — based on what we now know about them.
```

Examples:
- "You volunteer at a coding bootcamp — what drives that?"
- "You're building a side project in Rust while working in Python at your day job. What drew you to Rust?"
- "Your profile suggests you value directness. How do you handle giving tough feedback?"

### Step 7: The Hiring Decision Framework

```
Give me a one-page hiring brief on this candidate:
- Culture fit score (with evidence)
- Strengths beyond the resume
- Potential concerns
- Best interview approach
- Questions to probe deeper
```

## Punchline

> "Hire the person, not the resume."

## Key Moments to Emphasize

- The gap between what the resume says and what the dossier reveals
- The culture fit analysis being evidence-based (not gut feel)
- The Social Graph revealing who they surround themselves with
- The interview questions being specific and insightful (not generic "tell me about yourself")
- The shift from evaluating interview performance to understanding the whole person
