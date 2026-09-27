"""
Patient Note Summarizer & Triage Assistant — Backend
------------------------------------------------------
FastAPI service that accepts a free-text clinical note and returns:
  - a concise summary
  - extracted key symptoms
  - a suggested triage urgency level (Low / Medium / High)
  - the reasoning behind that urgency level
  - any red-flag symptoms that should never be auto-triaged

IMPORTANT — SCOPE & SAFETY:
This is a decision-SUPPORT demo, not a diagnostic device. It is not
validated, not clinically certified, and must never be used to make a
real triage decision without a licensed clinician reviewing the output.
The system prompt explicitly instructs the model to defer to humans on
anything ambiguous or high-risk, and every response is tagged with a
disclaimer field so a consuming UI cannot accidentally drop it.
"""

import os
import json
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import anthropic

app = FastAPI(title="Patient Note Triage Assistant", version="0.1.0")

# Allow the local Streamlit frontend to call this API during the demo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_NAME = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a clinical note triage assistant used ONLY as a \
decision-support aid for trained staff, never as a replacement for clinical \
judgment. Given a free-text patient note, respond with STRICT JSON only \
(no markdown, no prose) matching this schema:

{
  "summary": "2-3 sentence plain-language summary of the note",
  "key_symptoms": ["list", "of", "extracted", "symptoms"],
  "urgency": "Low" | "Medium" | "High",
  "reasoning": "1-3 sentences explaining why this urgency level was chosen",
  "red_flags": ["any symptoms that need immediate human clinician review, or empty list"]
}

Rules:
- If the note mentions anything potentially life-threatening (chest pain, \
severe bleeding, difficulty breathing, stroke symptoms, suicidal ideation, \
etc.), set urgency to "High" and list it under red_flags.
- Never provide a diagnosis. Only summarize, extract, and flag.
- If the note is too vague to assess, say so in reasoning and default to \
"Medium" so a human reviews it rather than it being silently deprioritized.
"""


class TriageRequest(BaseModel):
    note_text: str = Field(..., min_length=1, max_length=4000)


class TriageResponse(BaseModel):
    summary: str
    key_symptoms: list[str]
    urgency: Literal["Low", "Medium", "High"]
    reasoning: str
    red_flags: list[str]
    disclaimer: str = (
        "Demo decision-support output only. Not a diagnosis. "
        "Must be reviewed by a licensed clinician before any action is taken."
    )


def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY not set. See README for setup.",
        )
    return anthropic.Anthropic(api_key=api_key)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/triage", response_model=TriageResponse)
def triage_note(request: TriageRequest):
    client = get_client()

    try:
        message = client.messages.create(
            model=MODEL_NAME,
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": request.note_text}],
        )
    except Exception as exc:  # network/API errors surfaced cleanly to the caller
        raise HTTPException(status_code=502, detail=f"LLM call failed: {exc}")

    raw_text = "".join(
        block.text for block in message.content if getattr(block, "type", None) == "text"
    )

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        # Model didn't return clean JSON — fail loudly rather than guessing.
        raise HTTPException(
            status_code=502,
            detail="Model did not return valid JSON. Raw output logged for debugging.",
        )

    return TriageResponse(**parsed)
