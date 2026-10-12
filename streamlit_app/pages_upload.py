import streamlit as st
from api_client import api_post, error_text


def render():
    st.header("Upload Resume")

    msg = st.session_state.pop("upload_msg", None)
    if msg:
        st.success(msg)

    file = st.file_uploader("Choose a PDF or text resume", type=["pdf", "txt"])
    if file and st.button("Upload"):
        files = {"file": (file.name, file.getvalue(), file.type)}
        with st.spinner("Reading and indexing your resume..."):
            r = api_post("/resumes/upload", files=files)
        if r.status_code == 200:
            data = r.json()
            st.session_state["pending_resume"] = data["resume_id"]
            st.session_state["upload_msg"] = (
                f"Uploaded: {data['char_count']} characters, "
                f"{data.get('chunk_count', 0)} chunks. It's now your active resume."
            )
            st.rerun()
        else:
            st.error(f"Upload failed: {error_text(r)}")
