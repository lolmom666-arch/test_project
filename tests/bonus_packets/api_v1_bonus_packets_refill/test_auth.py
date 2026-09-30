import pytest
import requests
from src.db_client import DBClient
from src.config import BASE_URL


@pytest.mark.parametrize("use_valid_token, expected_code", [
    (True, 200),
    (False, 401)
])
def test_auth(
        use_valid_token: bool,
        expected_code: int,
        token_header: dict[str, str],
        database_client: DBClient,
        create_refill: str
) -> None:
    """Проверка авторизации."""
    token = {"Authorization": ""}
    if use_valid_token:
        token = token_header
        database_client.update(
            "UPDATE refill SET status = 0 WHERE id = %s",
            (create_refill,)
        )
    body = {"refillId": create_refill, "bonusPacketId": 212}
    response = requests.put(
        f"{BASE_URL}/api/v1/bonus/packets/refill",
        json=body,
        headers=token,
        timeout=10
    )
    assert response.status_code == expected_code
    data = response.json()
    if expected_code == 200:
        assert data == []
    else:
        assert data["code"] == 401
        assert data["message"] == "JWT Token not found"