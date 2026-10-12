from unittest.mock import MagicMock


def test_user_client_is_fresh_for_every_call(mocker):
    """Two requests must never share a client, or they could share a token."""
    mocker.patch(
        "app.core.supabase_client.create_client",
        side_effect=lambda *args, **kwargs: MagicMock(),
    )
    from app.core.supabase_client import user_client

    client_a = user_client("token-a")
    client_b = user_client("token-b")

    assert client_a is not client_b
    client_a.postgrest.auth.assert_called_once_with("token-a")
    client_b.postgrest.auth.assert_called_once_with("token-b")
