import pytest
import requests
from src.db_client import DBClient
from src.config import BASE_URL


@pytest.mark.parametrize("fields, status_code", [
    ((), 400),
    (("refillId",), 400),
    (("bonusPacketId",), 400),
    (("refillId","bonusPacketId","one_feild"), 200),
    (("refillId", "bonusPacketId", "one_feild","two_feild"), 200)
])
def test_fields(
        fields,
        status_code: int,
        create_refill: str,
        token_header: dict[str, str],
        database_client: DBClient,
) -> None:
    all_values = {
        "refillId": create_refill,
        "bonusPacketId": 50001,
        "one_feild": None,
        "two_feild": None
    }
    database_client.update(
        "UPDATE refill SET status = 0 WHERE id = %s",
        (create_refill,)
    )

    body = {key: all_values[key] for key in fields}
    response = requests.put(
        f"{BASE_URL}/api/v1/bonus/packets/refill",
        json=body,
        headers=token_header,
        timeout=10
    )
    assert response.status_code == status_code
    json_body = response.json()
    if status_code == 400:
        assert json_body["code"]== "VALIDATION"
        assert json_body["message"] == "Validation failed"
    else:
        assert json_body == []