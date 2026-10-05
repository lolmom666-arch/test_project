import pytest
import requests
from src.config import BASE_URL

pytestmark = pytest.mark.integration


@pytest.mark.parametrize(
    "refill_id, refill_status, expected_code, expected_message",
    [
        ("valid", 0, 200, None),
        ("valid", 1, 200, None),
        ("valid", 2, 400, "refill_status_not_allowed"),
        ("valid", 3, 400, "refill_status_not_allowed"),
        (None, None, 400, "Invalid request"),
        ("-1000", None, 400, "refill_not_found"),
        ("", None, 400, "Validation failed"),
    ],
)
def test_field_refill_id(
        refill_id: int | str | None,
        refill_status: int | None,
        expected_code: int,
        expected_message: str | None,
        create_user_and_refill,
        request,
) -> None:
    """Проверка поля refillId."""
    if refill_id == "valid":
        assert refill_status is not None
        user, refill_id = create_user_and_refill(refill_status)
    else:
        user = request.getfixturevalue("create_user")

    response = requests.put(
        f"{BASE_URL}/api/v1/bonus/packets/refill",
        json={"refillId": refill_id, "bonusPacketId": 50001},
        headers=user.jwt_header,
        timeout=10,
    )

    assert response.status_code == expected_code
    data = response.json()

    if expected_code == 200:
        assert data == []
    else:
        assert data["message"] == expected_message
