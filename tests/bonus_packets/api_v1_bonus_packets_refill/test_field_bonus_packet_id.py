import pytest
import requests

from src.db_client import DBClient
from src.config import BASE_URL

pytestmark = pytest.mark.integration


def _read_state(database_client: DBClient, refill_id: str) -> tuple[list[tuple], list[tuple]]:
    """Все опции пополнения, включая записи с другим packetId."""
    options = database_client.select(
        "SELECT id, value FROM user_selected_option WHERE entity_id = %s ORDER BY id",
        (refill_id,),
    )
    additional = database_client.select(
        "SELECT id, name, value FROM refill_additional_data WHERE refill_id = %s ORDER BY id",
        (refill_id,),
    )
    return options, additional


@pytest.mark.parametrize("project, bonus_packet_id, expected_code, expected_message", [
    ("MOSTBET", "valid_bonus_packet_id", 200, None),
    (None, "missing_bonus_packet_id", 400, "bonus_packet_not_found"),
    ("MWL", 50000, 200, None),
    ("MWL", 50001, 200, None),
    (None, "act", 400, "Invalid request"),
    (None, "", 400, "Invalid request"),
    (None, None, 400, "Invalid request"),
])
def test_field_bonus_packet_id(
        project: str | None,
        bonus_packet_id: int | str | None,
        expected_code: int,
        expected_message: str | None,
        create_user_and_refill,
        database_client: DBClient,
        request,
) -> None:
    user, refill_id = create_user_and_refill(0)
    if bonus_packet_id in ("valid_bonus_packet_id", "missing_bonus_packet_id"):
        bonus_packet_id = request.getfixturevalue(bonus_packet_id)
    before = _read_state(database_client, refill_id)
    response = requests.put(
        f"{BASE_URL}/api/v1/bonus/packets/refill",
        json={"refillId": refill_id, "bonusPacketId": bonus_packet_id},
        headers=user.jwt_header,
        timeout=10,
    )
    assert response.status_code == expected_code
    after = _read_state(database_client, refill_id)
    if project is None:
        assert response.json()["message"] == expected_message
        assert after == before, "Запрос с ошибкой изменил данные бонусного пакета"
        return

    assert response.json() == []
    options, additional = after
    if project == "MOSTBET":
        matching = database_client.select(
            "SELECT id FROM user_selected_option "
            "WHERE entity_id = %s AND JSON_EXTRACT(value, '$.packetId') = %s",
            (refill_id, bonus_packet_id),
        )
        assert matching, "Выбранный пакет не записан в user_selected_option"
    else:
        assert options == before[0], "MWL-запрос изменил user_selected_option"

    assert len(additional) == 3, f"Ожидалось 3 записи, получено {len(additional)}"
    data = {name: value for _, name, value in additional}
    assert len(data) == len(additional), "Имена дополнительных данных повторяются"
    assert data["bonus_package_id"] == str(bonus_packet_id)
    assert data["bonus_package_source"] == project
