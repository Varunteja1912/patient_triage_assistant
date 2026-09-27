# Patient Note Summarizer & Triage Assistant

A small decision-support demo: paste a free-text clinical note, and an LLM
returns a structured summary, extracted symptoms, a suggested triage
urgency level, and any red-flag symptoms that need immediate human review.

> ⚠️ **This is a portfolio/demo project, not a medical device.** It is not
> clinically validated. Every response includes a disclaimer, and the
> system prompt is deliberately conservative (defaults to "Medium" urgency
> when unsure, rather than silently deprioritizing an ambiguous case).

## Why I built this

Built as a focused demo ahead of interviewing for a healthcare-software
engineering role, to show a pattern I already use in my other projects
(structured LLM output for a real decision-support use case) applied to a
healthcare-flavored problem — matching the kind of AI-assisted engineering
workflow the role calls for.

## Architecture

```
Streamlit UI  --HTTP POST-->  FastAPI backend  --API call-->  Claude (Anthropic API)
 (frontend/)                    (backend/)
```

- **Backend (`backend/main.py`)** — FastAPI service exposing a single
  `POST /triage` endpoint. It builds a strict system prompt instructing
  the model to return JSON only, matching a fixed schema (summary,
  key_symptoms, urgency, reasoning, red_flags). Response is validated
  against a Pydantic model before being returned, so a malformed LLM
  response fails loudly (502) instead of silently returning garbage to
  the UI.
- **Frontend (`frontend/app.py`)** — a single-page Streamlit app: a text
  box for the note, a submit button, and a color-coded urgency display
  (🟢/🟡/🔴). Deliberately no auth/database — the point of this demo is
  the AI-integration pattern, not the UI.

## Design decisions worth being able to explain

- **Structured JSON output, not free text** — the backend can't safely
  render arbitrary LLM prose into a UI; forcing a JSON schema means the
  frontend can render fields deterministically and validation can catch
  a bad response before it reaches a user.
- **Conservative defaults over confident guesses** — if the note is too
  vague, the model is instructed to default to "Medium" urgency and say
  so in `reasoning`, rather than confidently downgrading a case it isn't
  sure about. In a healthcare context, a false "Low" is worse than an
  unnecessary "Medium."
- **No diagnosis, ever** — the system prompt explicitly forbids
  diagnostic claims; the tool only summarizes, extracts, and flags for a
  human.
- **Environment-based API key** — the key is read from
  `ANTHROPIC_API_KEY` at runtime, never hardcoded, and `.env` is
  git-ignored.

## Known limitations (be ready to say these out loud)

- No persistence/database — nothing is stored, so there's no audit trail
  yet (a real system would need one for compliance).
- No authentication — anyone who can reach the API can call it.
- Single LLM call per note — no retrieval/RAG grounding against a
  patient's history, so it only reasons over what's in the note itself.
- No automated tests yet (would add `pytest` + mocked Anthropic client
  for the backend, and a schema-validation test for edge cases like an
  empty note or a note in another language).

## Setup

```bash
git clone <your-repo-url>
cd patient-triage-assistant
pip install -r requirements.txt
cp .env.example .env   # then add your real ANTHROPIC_API_KEY

# terminal 1
uvicorn backend.main:app --reload --port 8000

# terminal 2
streamlit run frontend/app.py
```

## Tech stack

Python, FastAPI, Pydantic, Streamlit, Anthropic API — chosen to match the
same stack already used across my other projects (Resume Matcher,
AgroNexus AI), so the pattern is consistent across my work.
