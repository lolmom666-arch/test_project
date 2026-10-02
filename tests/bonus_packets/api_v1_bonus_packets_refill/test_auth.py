import pytest
import requests
from typing import Any
from src.db_client import DBClient
from src.config import BASE_URL


@pytest.mark.parametrize("create_refill, expected_code", [
    (0, 200),
    (None, 401)
], indirect=["create_refill"])
def test_auth(
        expected_code: int,
        token_header: dict[str, str],
        database_client: DBClient,
        create_refill: str
) -> None:
    """Проверка авторизации."""
    token = {"Authorization": ""}
    if expected_code==200:
        token = token_header
    body: dict[str, Any] = {"refillId": create_refill, "bonusPacketId": 212}
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
