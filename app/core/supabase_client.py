import os

from supabase import create_client

# Used ONLY for auth calls (signup, login, checking a token). It never touches
# user data, so it is safe for every request to share it.
auth_client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def user_client(token: str):
    """Build a fresh database client that acts as one specific user.

    A new one is created for every request, so two requests never share a
    token. Row Level Security applies to everything this client does.
    """
    client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    client.postgrest.auth(token)
    return client
