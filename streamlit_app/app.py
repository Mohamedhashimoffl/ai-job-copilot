import streamlit as st
from api_client import login

st.set_page_config(page_title="AI Job Co-Pilot", layout="wide")

if "access_token" not in st.session_state:
    st.title("Log in")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Log in"):
        if login(email, password):
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

page = st.sidebar.radio(
    "Navigate", ["Upload Resume", "Matches", "Tracker", "Run Agent"]
)

if page == "Upload Resume":
    import pages_upload as p

    p.render()
elif page == "Matches":
    import pages_matches as p

    p.render()
elif page == "Tracker":
    import pages_tracker as p

    p.render()
elif page == "Run Agent":
    import pages_agent as p

    p.render()
