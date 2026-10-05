import pytest
import requests

from src.config import BASE_URL

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("authorized, expected_code", [(True, 200), (False, 401)])
def test_auth(authorized: bool, expected_code: int, create_user_and_refill) -> None:
    """Корректное пополнение; меняется только заголовок авторизации."""
    user, refill_id = create_user_and_refill(0)
    token = user.jwt_header if authorized else {"Authorization": ""}
    response = requests.put(
        f"{BASE_URL}/api/v1/bonus/packets/refill",
        json={"refillId": refill_id, "bonusPacketId": 50001},
        headers=token,
        timeout=10,
    )
    assert response.status_code == expected_code
    data = response.json()
    if authorized:
        assert data == []
    else:
        assert data["code"] == 401
        assert data["message"] == "JWT Token not found"
