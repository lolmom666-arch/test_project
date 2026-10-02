import pytest
import requests
from src.db_client import DBClient
from src.config import BASE_URL


@pytest.mark.parametrize("refill_id, create_refill, expected_code, expected_message", [
    ("valid", 0, 200, []),
    ("valid", 1, 200, []),
    ("valid", 2, 400, "refill_status_not_allowed"),
    ("valid", 3, 400, "refill_status_not_allowed"),
    (None, None, 400, "Invalid request"),
    ("-1000", None, 400, "refill_not_found"),
    ("", None, 400, "Validation failed")
], indirect=["create_refill"])
def test_field_refill_id(
        refill_id: int | str | None,
        expected_code: int,
        expected_message: str | None,
        token_header: dict[str, str],
        create_refill: int,
        database_client: DBClient,
) -> None:
    """Проверка поля refillId."""
    if refill_id == "valid":
        refill_id = create_refill
    response = requests.put(
        f"{BASE_URL}/api/v1/bonus/packets/refill",
        json={"refillId": refill_id, "bonusPacketId": 50001},
        headers=token_header,
        timeout=10)
    assert response.status_code == expected_code
    data = response.json()
    if expected_code == 200:
        assert data == []
    else:
        assert data["message"] == expected_message
