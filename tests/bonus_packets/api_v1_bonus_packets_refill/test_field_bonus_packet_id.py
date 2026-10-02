import pytest
import requests
from src.one_click import User
from src.db_client import DBClient
from src.config import BASE_URL


@pytest.mark.parametrize(
    "project, bonus_packet_id, expected_code, expected_message, create_refill", [
        ("MOSTBET", "valid_bonus_packet_id", 200, [], 0),
        (None, 49999, 400, "bonus_packet_not_found", 0),
        ("MWL", 50000, 200, [], 0),
        ("MWL", 50001, 200, [], 0),
        (None, "act", 400, "Invalid request", 0),
        (None, "", 400, "Invalid request", 0),
        (None, None, 400, "Invalid request", 0),
    ], indirect=["create_refill"])
def test_field_bonus_packet_id(
        project: str | None,
        bonus_packet_id: int | str | None,
        expected_code: int,
        expected_message: str | None,
        create_refill: str | None,
        token_header: dict[str, str],
        database_client: DBClient,
        valid_bonus_packet_id: int,
) -> None:
    """Проверка поля bonusPacketId."""
    if bonus_packet_id == "valid_bonus_packet_id":
        bonus_packet_id = valid_bonus_packet_id

    response = requests.put(
        f"{BASE_URL}/api/v1/bonus/packets/refill",
        json={"refillId": create_refill, "bonusPacketId": bonus_packet_id},
        headers=token_header,
        timeout=10
    )
    user_options = database_client.select(
        "SELECT id FROM user_selected_option "
        "WHERE entity_id = %s AND JSON_EXTRACT(value, '$.packetId') = %s",
        (create_refill, bonus_packet_id),
    )
    additional = database_client.select(
        "SELECT name, value FROM refill_additional_data WHERE refill_id = %s",
        (create_refill,),
    )
    data_additional = dict(additional)

    assert response.status_code == expected_code
    if project is not None:
        assert response.json() == expected_message
        assert user_options if project == "MOSTBET" else not user_options
        assert len(additional) == 3, f"Ожидалось 3 записи, получено {len(additional)}"
        assert data_additional["bonus_package_id"] == str(bonus_packet_id)
        assert data_additional["bonus_package_source"] == project
    else:
        assert response.json()["message"] == expected_message
        assert not user_options