import requests
import streamlit as st
import os

API_BASE = os.getenv("API_BASE", "http://localhost:8000")


def get_headers():
    token = st.session_state.get("access_token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def login(email: str, password: str) -> bool:
    r = requests.post(
        f"{API_BASE}/auth/login", json={"email": email, "password": password}
    )
    if r.status_code == 200:
        data = r.json()
        st.session_state["access_token"] = data["access_token"]
        st.session_state["user_id"] = data["user_id"]
        return True
    return False


def api_get(path: str, **kwargs):
    return requests.get(f"{API_BASE}{path}", headers=get_headers(), **kwargs)


def api_post(path: str, **kwargs):
    return requests.post(f"{API_BASE}{path}", headers=get_headers(), **kwargs)
