import streamlit as st
from api_client import api_post


def render():
    st.header("Upload Resume")
    file = st.file_uploader("Choose a PDF or text resume", type=["pdf", "txt"])
    if file and st.button("Upload"):
        files = {"file": (file.name, file.getvalue(), file.type)}
        r = api_post("/resumes/upload", files=files)
        if r.status_code == 200:
            data = r.json()
            st.success(
                f"Uploaded — {data['char_count']} characters extracted, {data.get('chunk_count', 0)} chunks"
            )
            st.session_state["resume_id"] = data["resume_id"]
        else:
            st.error(f"Upload failed: {r.text}")
