import streamlit as st
from api_client import api_get


def resume_picker():
    """Sidebar dropdown of the user's saved resumes. Sets st.session_state['resume_id']."""
    r = api_get("/resumes")
    resumes = r.json() if r.status_code == 200 else []

    if not resumes:
        st.sidebar.info("No resume yet. Upload one on the Upload Resume page.")
        st.session_state.pop("resume_id", None)
        return

    ids = [x["id"] for x in resumes]
    labels = {
        x["id"]: f"{x.get('file_name') or 'resume'} ({str(x['uploaded_at'])[:10]})"
        for x in resumes
    }

    pending = st.session_state.pop("pending_resume", None)
    if pending in ids:
        st.session_state["resume_picker"] = pending
    elif st.session_state.get("resume_picker") not in ids:
        st.session_state["resume_picker"] = ids[0]

    st.sidebar.selectbox(
        "Active resume",
        ids,
        key="resume_picker",
        format_func=lambda i: labels[i],
    )
    st.session_state["resume_id"] = st.session_state["resume_picker"]
