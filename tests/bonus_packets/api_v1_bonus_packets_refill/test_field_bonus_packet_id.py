import pytest
import requests

from src.db_client import DBClient
from src.config import BASE_URL


@pytest.mark.parametrize("bonus_packet_id, expected_code, expected_message", [
    ("valid", 200, None),
    (49999, 400, "bonus_packet_not_found"),
    (50000, 200, None),
    (50001, 200, None),
    ("act", 400, "Invalid request"),
    ("", 400, "Invalid request"),
    (None, 400, "Invalid request"),
])
def test_field_bonus_packet_id(
        bonus_packet_id: int | str | None,
        expected_code: int,
        expected_message: str | None,
        token_header: dict[str, str],
        create_refill: int,
        database_client: DBClient,
        valid_bonus_packet_id: int,
        create_user) -> None:
    """Проверка поля bonusPacketId."""
    is_valid_case = bonus_packet_id == "valid"
    actual_bonus_packet_id = valid_bonus_packet_id if is_valid_case else bonus_packet_id
    database_client.update(
        "UPDATE refill SET status = 0 WHERE id = %s",
        (create_refill,)
    )
    body = {"refillId": create_refill, "bonusPacketId": actual_bonus_packet_id}
    response = requests.put(
        f"{BASE_URL}/api/v1/bonus/packets/refill",
        json=body,
        headers=token_header,
        timeout=10
    )
    assert response.status_code == expected_code
    data = response.json()
    if expected_code == 200:
        assert data == []
    else:
        assert data["message"] == expected_message

    # === Проверка БД ===
    # 1. user_selected_option — ищем по packetId
    target = f'packetId": {actual_bonus_packet_id}'
    user_options = database_client.select(
        "SELECT id FROM user_selected_option WHERE entity_id = %s AND JSON_EXTRACT(value, '$.packetId') = %s",
        (create_refill, actual_bonus_packet_id)
    )
    additional = database_client.select(
        "SELECT id FROM refill_additional_data WHERE refill_id = %s ORDER BY id DESC LIMIT 3",
        (create_refill,)
    )
    source = database_client.select(
        "SELECT value FROM refill_additional_data WHERE refill_id = %s AND name = 'bonus_package_source'",
        (create_refill,)
    )
    if is_valid_case:
        # MOSTBET
        assert user_options, "Запись в user_selected_option не появилась"
        assert len(additional) == 3, f"Ожидалось 3 записи, получено {len(additional)}"
        assert source, "Запись refill_additional_data не найдена"
        assert source[0][0] == "MOSTBET", f"Ожидался MOSTBET, получен {source[0][0]}"
    elif bonus_packet_id in (50000, 50001):
        # MWL
        assert not user_options, "user_selected_option должна быть пуста"
        assert len(additional) == 3, f"Ожидалось 3 записи, получено {len(additional)}"
        assert source, "Запись refill_additional_data не найдена"
        assert source[0][0] == "MWL", f"Ожидался MWL, получен {source[0][0]}"
    else:
        assert not user_options, "При ошибке запись не должна создаваться"