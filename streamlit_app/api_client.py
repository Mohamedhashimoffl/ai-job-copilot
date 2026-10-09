import os
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE", "http://localhost:8000")


def get_headers():
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def login(email: str, password: str) -> tuple[bool, str]:
    try:
        r = requests.post(
            f"{API_BASE}/auth/login",
            json={"email": email, "password": password},
            timeout=90,
        )
    except requests.exceptions.RequestException:
        return (
            False,
            "Couldn't reach the server. It may still be waking up, try again in a minute.",
        )
    if r.status_code == 200:
        data = r.json()
        st.session_state["access_token"] = data["access_token"]
        st.session_state["user_id"] = data["user_id"]
        return True, ""
    return False, "Invalid credentials"


def signup(email: str, password: str) -> tuple[bool, str]:
    try:
        r = requests.post(
            f"{API_BASE}/auth/signup",
            json={"email": email, "password": password},
            timeout=90,
        )
    except requests.exceptions.RequestException:
        return (
            False,
            "Couldn't reach the server. It may still be waking up, try again in a minute.",
        )
    if r.status_code == 200:
        return True, "Account created. You can log in now."
    return (
        False,
        "Signup failed. Try a different email, or a password of 6+ characters.",
    )


def api_get(path: str, **kwargs):
    return requests.get(
        f"{API_BASE}{path}", headers=get_headers(), timeout=90, **kwargs
    )


def api_post(path: str, **kwargs):
    return requests.post(
        f"{API_BASE}{path}", headers=get_headers(), timeout=180, **kwargs
    )
