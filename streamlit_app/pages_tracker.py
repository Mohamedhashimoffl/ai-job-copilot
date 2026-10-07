import streamlit as st
from api_client import api_get


def render():
    st.header("Application Tracker")

    col1, col2 = st.columns(2)
    with col1:
        status_filter = st.selectbox(
            "Filter by status",
            ["All", "draft", "applied", "interview", "rejected", "offer"],
        )

    params = {} if status_filter == "All" else {"status": status_filter}
    r = api_get("/applications", params=params)
    if r.status_code == 200:
        for app in r.json():
            job = app.get("job_postings", {})
            st.write(
                f"**{job.get('title', 'Unknown')}** at {job.get('company', '—')} — `{app['status']}`"
            )
