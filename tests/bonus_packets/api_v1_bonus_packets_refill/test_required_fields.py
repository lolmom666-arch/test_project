import pytest
import requests

from src.config import BASE_URL

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("fields, expected_code", [
    ((), 400),
    (("refillId",), 400),
    (("bonusPacketId",), 400),
    (("refillId", "bonusPacketId"), 200),
    (("refillId", "bonusPacketId", "one_field"), 200),
    (("refillId", "bonusPacketId", "one_field", "two_field"), 200),
])
def test_fields(fields: tuple[str, ...], expected_code: int, create_user_and_refill, request) -> None:
    if "refillId" in fields:
        user, refill_id = create_user_and_refill(0)
    else:
        user = request.getfixturevalue("create_user")
        refill_id = None
    all_values = {
        "refillId": refill_id,
        "bonusPacketId": 50001,
        "one_field": None,
        "two_field": None,
    }
    response = requests.put(
        f"{BASE_URL}/api/v1/bonus/packets/refill",
        json={key: all_values[key] for key in fields},
        headers=user.jwt_header,
        timeout=10,
    )
    assert response.status_code == expected_code
    json_body = response.json()
    if expected_code == 400:
        assert json_body["code"] == "VALIDATION"
        assert json_body["message"] == "Validation failed"
    else:
        assert json_body == []
