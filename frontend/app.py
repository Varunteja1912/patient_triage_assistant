"""
Patient Note Summarizer & Triage Assistant — Streamlit Frontend
-----------------------------------------------------------------
Thin UI over the FastAPI backend. Kept deliberately simple (single page,
no auth) since the point of this demo is the AI-integration pattern, not
the UI polish.
"""

import os
import requests
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Patient Note Triage Assistant", page_icon="🩺")

st.title("🩺 Patient Note Triage Assistant (Demo)")
st.caption(
    "Decision-support demo only — not a diagnostic tool. "
    "All output must be reviewed by a licensed clinician."
)

with st.form("triage_form"):
    note_text = st.text_area(
        "Paste a clinical note / patient-reported symptoms:",
        height=180,
        placeholder=(
            "e.g. 45-year-old male, sudden onset chest tightness radiating "
            "to left arm, shortness of breath started 20 minutes ago..."
        ),
    )
    submitted = st.form_submit_button("Run Triage Analysis")

if submitted:
    if not note_text.strip():
        st.warning("Please enter a note before submitting.")
    else:
        with st.spinner("Analyzing note..."):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/triage",
                    json={"note_text": note_text},
                    timeout=30,
                )
                resp.raise_for_status()
                result = resp.json()
            except requests.exceptions.RequestException as e:
                st.error(f"Request failed: {e}")
                result = None

        if result:
            urgency_color = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}
            st.subheader(f"{urgency_color.get(result['urgency'], '⚪')} Urgency: {result['urgency']}")

            st.markdown("**Summary**")
            st.write(result["summary"])

            st.markdown("**Key Symptoms**")
            st.write(", ".join(result["key_symptoms"]) or "None extracted")

            st.markdown("**Reasoning**")
            st.write(result["reasoning"])

            if result["red_flags"]:
                st.markdown("**⚠️ Red Flags — Immediate Human Review Needed**")
                for flag in result["red_flags"]:
                    st.error(flag)

            st.caption(result["disclaimer"])
