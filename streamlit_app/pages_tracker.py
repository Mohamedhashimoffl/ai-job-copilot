import streamlit as st
from api_client import api_get, api_patch, error_text

STATUSES = ["draft", "applied", "interview", "rejected", "offer"]


def render():
    st.header("Application Tracker")

    fr = api_get("/applications/needs-followup")
    if fr.status_code == 200 and fr.json():
        st.subheader("Needs a follow-up")
        for a in fr.json():
            job = a.get("job_postings") or {}
            st.warning(
                f"**{job.get('title', 'Unknown')}** at {job.get('company') or '—'}: "
                f"{a['status']} for {a['days_waiting']} days "
                f"(nudge after {a['followup_threshold']})"
            )

    status_filter = st.selectbox("Filter by status", ["All"] + STATUSES)
    params = {} if status_filter == "All" else {"status": status_filter}
    r = api_get("/applications", params=params)
    if r.status_code != 200:
        st.error(f"Couldn't load applications: {error_text(r)}")
        return

    apps = r.json()
    if not apps:
        st.info(
            "Nothing here yet. Add jobs from the Matches page or let the agent do it."
        )
        return

    for a in apps:
        job = a.get("job_postings") or {}
        title = job.get("title", "Unknown")
        company = job.get("company") or "—"
        url = job.get("source_url")
        current = a["status"] if a["status"] in STATUSES else STATUSES[0]

        with st.container(border=True):
            c1, c2, c3 = st.columns([4, 2, 1])

            link = f" · [job link]({url})" if url else ""
            c1.markdown(f"**{title}** at {company}{link}")
            if a.get("applied_at"):
                c1.caption(f"Applied {str(a['applied_at'])[:10]}")

            new_status = c2.selectbox(
                "Status",
                STATUSES,
                index=STATUSES.index(current),
                key=f"status_{a['id']}",
                label_visibility="collapsed",
            )
            if c3.button(
                "Update", key=f"update_{a['id']}", disabled=(new_status == current)
            ):
                ur = api_patch(f"/applications/{a['id']}", json={"status": new_status})
                if ur.status_code == 200:
                    st.rerun()
                else:
                    st.error(error_text(ur))
