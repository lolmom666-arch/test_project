import pytest
import requests
from typing import Any
from src.db_client import DBClient
from src.config import BASE_URL


@pytest.mark.parametrize("fields, expected_code, create_refill", [
    ((), 400, None),
    (("refillId",), 400, 0),
    (("bonusPacketId",), 400, None),
    (("refillId", "bonusPacketId", "one_field"), 200, 0),
    (("refillId", "bonusPacketId", "one_field", "two_field"), 200, 0)
], indirect=["create_refill"])
def test_fields(
        fields,
        expected_code: int,
        create_refill: str | None,
        token_header: dict[str, str],
        database_client: DBClient,
) -> None:
    all_values = {
        "refillId": create_refill,
        "bonusPacketId": 50001,
        "one_field": None,
        "two_field": None
    }
    body: dict[str, Any] = {key: all_values[key] for key in fields}
    response = requests.put(
        f"{BASE_URL}/api/v1/bonus/packets/refill",
        json=body,
        headers=token_header,
        timeout=10
    )
    assert response.status_code == expected_code
    json_body = response.json()
    if expected_code == 400:
        assert json_body["code"] == "VALIDATION"
        assert json_body["message"] == "Validation failed"
    else:
        assert json_body == []
