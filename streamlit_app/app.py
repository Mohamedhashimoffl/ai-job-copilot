import streamlit as st
from api_client import login, signup

st.set_page_config(page_title="AI Job Co-Pilot", layout="wide")

if "access_token" not in st.session_state:
    st.title("AI Job Co-Pilot")
    st.caption("First load can take about a minute while the server wakes up.")
    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

    with tab_login:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Log in"):
            ok, msg = login(email, password)
            if ok:
                st.rerun()
            else:
                st.error(msg)

    with tab_signup:
        s_email = st.text_input("Email", key="signup_email")
        s_password = st.text_input(
            "Password (6+ characters)", type="password", key="signup_password"
        )
        if st.button("Create account"):
            ok, msg = signup(s_email, s_password)
            if ok:
                st.success(msg)
            else:
                st.error(msg)

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
