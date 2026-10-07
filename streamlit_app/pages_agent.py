import streamlit as st
from api_client import api_post


def render():
    st.header("Run the Agent")
    resume_id = st.session_state.get("resume_id")
    if not resume_id:
        st.warning("Upload a resume first")
        return

    goal = st.text_area(
        "What should the agent do?",
        value="Search for backend developer remote jobs, score the top 3 against my resume, "
        "and add any with a fit score of 75 or higher to my tracker.",
    )

    if st.button("Run"):
        with st.spinner("Agent working..."):
            r = api_post(f"/matches/{resume_id}/auto-apply", params={"goal": goal})
        if r.status_code == 200:
            result = r.json()
            st.write(result.get("result", result))
            if "tool_calls_used" in result:
                st.caption(f"Tool calls used: {result['tool_calls_used']}")
        else:
            st.error(f"Agent run failed: {r.text}")
