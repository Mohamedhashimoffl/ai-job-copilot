import streamlit as st
from api_client import api_get, api_post, error_text


def render():
    st.header("Job Matches")
    resume_id = st.session_state.get("resume_id")
    if not resume_id:
        st.warning("Upload a resume first")
        return

    r = api_get(f"/matches/{resume_id}")
    if r.status_code != 200:
        st.error(f"Couldn't load matches: {error_text(r)}")
        return

    matches = r.json()
    if not matches:
        st.info("No matches yet. Run the agent to find jobs, or seed some sample jobs.")
        return

    st.caption(
        "Analyzing a job and writing a cover letter each use your AI quota, "
        "so they only run when you click."
    )

    for m in matches:
        job_id = m["job_id"]
        sim = m.get("similarity")
        sim_text = f"{sim:.2f}" if sim is not None else "n/a"
        title = f"{m['title']} at {m.get('company') or '—'} · similarity {sim_text}"
        with st.expander(title):
            job_actions(resume_id, job_id)


def job_actions(resume_id: str, job_id: str):
    analysis_key = f"analysis_{resume_id}_{job_id}"
    letter_key = f"letter_{resume_id}_{job_id}"

    c1, c2, c3 = st.columns(3)

    if c1.button("Analyze fit", key=f"analyze_{job_id}"):
        with st.spinner("Analyzing..."):
            ar = api_get(f"/matches/{resume_id}/analyze/{job_id}")
        if ar.status_code == 200:
            st.session_state[analysis_key] = ar.json()
        else:
            st.error(error_text(ar))

    if c2.button("Write cover letter", key=f"letter_btn_{job_id}"):
        with st.spinner("Writing..."):
            lr = api_get(f"/matches/{resume_id}/cover-letter/{job_id}")
        if lr.status_code == 200:
            st.session_state[letter_key] = lr.json()["cover_letter"]
            st.session_state.pop(f"{letter_key}_box", None)  # reset the text box
        elif lr.status_code == 404:
            st.info("Analyze this job first, then write the letter.")
        else:
            st.error(error_text(lr))

    if c3.button("Add to tracker", key=f"track_{job_id}"):
        tr = api_post("/applications", json={"job_id": job_id, "status": "draft"})
        if tr.status_code == 200:
            st.success("It's in your tracker.")
        else:
            st.error(error_text(tr))

    analysis = st.session_state.get(analysis_key)
    if analysis:
        st.metric("Fit score", f"{analysis['score']}/100")
        st.write(analysis["explanation"])
        left, right = st.columns(2)
        left.markdown("**Strengths**")
        left.markdown(
            "\n".join(f"- {s}" for s in analysis["strengths"]) or "None listed"
        )
        right.markdown("**Gaps**")
        right.markdown("\n".join(f"- {g}" for g in analysis["gaps"]) or "None listed")

    letter = st.session_state.get(letter_key)
    if letter:
        st.text_area(
            "Cover letter (edit and copy it from here)",
            value=letter,
            height=280,
            key=f"{letter_key}_box",
        )
