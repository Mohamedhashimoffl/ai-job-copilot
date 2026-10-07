from api_client import api_get
import streamlit as st


def render():
    st.header("Job Matches")
    resume_id = st.session_state.get("resume_id")
    if not resume_id:
        st.warning("Upload a resume first")
        return

    r = api_get(f"/matches/{resume_id}")
    if r.status_code == 200:
        matches = r.json()
        if not matches:
            st.info("No matches found yet.")
            return

        for match in matches:
            # Fallback chain to safely catch similarity, score, or None
            raw_score = match.get("similarity") or match.get("score") or 0.0

            try:
                score_val = float(raw_score)
                score_display = f"{score_val:.2f}"
            except (ValueError, TypeError):
                score_display = "N/A"

            title = match.get("title", "Job Match")

            with st.expander(f"{title} — Score: {score_display}"):
                st.write(match)
    else:
        st.error(f"Failed to fetch matches: {r.text}")
