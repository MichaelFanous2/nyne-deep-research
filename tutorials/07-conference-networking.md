# Tutorial 7: Conference Networking — From Awkward to Authentic

> **Event-driven use case.**

## What You're Showing

500 people at a conference. Who do you actually talk to, and what do you say? Batch deep research on 10-15 speakers/attendees. Interest Cluster Deep Dive for each — find unexpected shared interests. Build a networking playbook. Conversation Starters section in action.

## Setup Before Recording

- Pick a real upcoming conference (or a recent one)
- Have a list of 5-10 speakers/attendees with emails or LinkedIn URLs
- Know your own interests (so you can show shared interest matches)

## Demo Script

### Step 1: Set the Scene

```
I'm going to [Conference Name] next week. 500 people. I don't want to wander around making small talk. I want to know exactly who to find and what to talk about. Let me batch research the speakers and key attendees.
```

### Step 2: Batch Deep Research

Run deep research on each person. Show the flow:

```
python deep_research.py --email "{speaker1_email}" --linkedin "{speaker1_linkedin}" --output speakers/speaker1.md
python deep_research.py --email "{speaker2_email}" --linkedin "{speaker2_linkedin}" --output speakers/speaker2.md
python deep_research.py --email "{speaker3_email}" --linkedin "{speaker3_linkedin}" --output speakers/speaker3.md
```

(For the demo, you can have some pre-run. Show 2-3 running live, then open the batch.)

### Step 3: Find Shared Interests Across the Batch

```
I've run deep research on 8 conference attendees. Based on their dossiers, find the shared interests between me and each person. My interests are: [your real interests — cycling, jazz, startups, whatever]. Show me the best matches.
```

Let Claude cross-reference and produce something like:

```
BEST MATCHES:
- Speaker A: Also into cycling + follows the same podcast you love
- Speaker B: Same nonprofit board interest (education equity)
- Attendee C: Both into craft coffee + they frequent your favorite roaster
- Speaker D: Shares your interest in stoic philosophy
```

### Step 4: Build the Networking Playbook

```
Build me a networking playbook for this conference. For each person, give me:
1. Who they are (one line)
2. Best shared interest to lead with
3. Opening line (from their Conversation Starters)
4. What NOT to say (from Landmines)
```

### Step 5: Show a Specific Example

Pick the best match and go deep:

```
Tell me everything I need to know about [Speaker A] for a 5-minute conversation at the coffee bar. What do I lead with? What do I avoid? How do I follow up after the conference?
```

### Step 6: Post-Conference Follow-Up

```
After the conference, I talked to [Speaker A] about cycling and [Attendee C] about coffee. Draft follow-up emails for each that reference our actual conversation and their real interests.
```

## Punchline

> "Turns forced small talk into 'Wait, you follow that too?'"

## Key Moments to Emphasize

- The batch research flow — showing scale
- The shared interest matching across multiple people
- A specific "Wait, you follow that too?" moment
- The networking playbook being immediately actionable
- Follow-up emails that reference real shared interests (not generic "great to meet you")
