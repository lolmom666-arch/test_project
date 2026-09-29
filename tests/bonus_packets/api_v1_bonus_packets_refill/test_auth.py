import pytest
import requests
from src.config import BASE_URL


@pytest.mark.parametrize("jwt_token, status_code", [
    (True, 200),
    (False, 401)
])
def test_auth(jwt_token: str, status_code: int, valid_token: str, valid_body: str):
    """Проверка авторизации."""
    token = valid_token if jwt_token else ""
    headers = {"Authorization": token}
    auth = requests.put(f"{BASE_URL}/api/v1/bonus/packets/refill", json=valid_body, headers=headers, timeout=10)
    status_auth = auth.status_code
    auth_text = auth.json()
    assert status_auth == status_code
    match status_code:
        case 200:
            assert auth_text == []
        case 401:
            assert auth_text['code'] == 401
            assert auth_text['message'] == "JWT Token not found"