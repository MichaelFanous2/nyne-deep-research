# Tutorial 8: Build a Prospect Persona Library

> **The technical integration demo — developer/API tutorial.**

## What You're Showing

Your sales team is flying blind. What if every prospect had a dossier before the first touchpoint? Show the API integration — programmatic deep research on a prospect list. Simple workflow: kick off research, get dossiers back, pull out Conversation Starters and Approach Strategy for SDRs.

## Setup Before Recording

- Have a list of 3-5 prospect emails ready
- Have Python available in Claude Code
- This is more technical — show actual code

## Demo Script

### Step 1: Set the Scene

```
My sales team has 50 prospects this week. Nobody has time to research each one. I'm going to build a simple workflow that runs deep research on a prospect list and pulls out the key sections SDRs need.
```

### Step 2: Show the Batch Script

```
Write me a Python script that:
1. Takes a CSV of prospect emails
2. Runs deep_research.py on each one
3. Saves each dossier to a prospects/ directory
4. Extracts the Conversation Starters and Approach Strategy sections into a summary file
```

Let Claude write the script. Run it on 3-5 real prospects.

### Step 3: Show the Results

Open the summary file. Walk through what each SDR gets:

```
PROSPECT: jane@startup.com
---
CONVERSATION STARTERS:
- Professional: "Your Series B must be keeping you busy — how are you scaling the eng team?"
- Personal: "I saw you're into rock climbing — have you been to Bishop?"
- Shared: "We're both Berkeley alums — did you ever take [professor]'s class?"

APPROACH STRATEGY:
- Lead with: data and specifics, not vision
- Avoid: generic AI claims, name-dropping
- Best angle: shared Berkeley connection + their focus on sustainable growth
- Tone: direct, no small talk, get to the point fast

LANDMINES:
- Don't mention their previous company (bad exit)
- Avoid "disruption" language — they've posted against it
```

### Step 4: Show the Workflow in Practice

```
I'm an SDR about to call jane@startup.com. Based on her dossier, give me a 30-second call script. What do I say when she picks up? What do I say if I get voicemail?
```

### Step 5: Show Scale

```
How long would this take for 50 prospects? Let's estimate:
- Deep research: ~60 seconds per person
- Batch of 50: ~50 minutes running in parallel
- Result: every prospect has a dossier before Monday morning
```

### Step 6: CRM Integration Concept

```
If I wanted to push these dossier summaries into our CRM (HubSpot/Salesforce), what would that integration look like? Show me a simple webhook handler.
```

Let Claude sketch the integration code.

## Punchline

> "Scale human understanding. Not just data — context."

## Key Moments to Emphasize

- The simplicity of the batch workflow (it's just a Python loop)
- The quality of extracted Conversation Starters — these are immediately usable by SDRs
- The Approach Strategy being specific and actionable (not generic "be friendly")
- The scale argument — 50 prospects, all with dossiers, before Monday
