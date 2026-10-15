import pytest
import requests

from src.config import BASE_URL
from src.db_client import DBClient


class TestAPIBonusPacketRefill:
    @pytest.mark.parametrize("authorized, expected_code", [(True, 200), (False, 401)])
    def test_auth(self, authorized: bool, expected_code: int, create_user_and_refill) -> None:
        """Проверка заголовков; меняется только заголовок авторизации."""
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

    @pytest.mark.parametrize("fields, expected_code", [
        ((), 400),
        (("refillId",), 400),
        (("bonusPacketId",), 400),
        (("refillId", "bonusPacketId"), 200),
        (("refillId", "bonusPacketId", "one_field"), 200),
        (("refillId", "bonusPacketId", "one_field", "two_field"), 200),
    ])
    def test_fields(self, fields: tuple[str, ...], expected_code: int, create_user_and_refill, request) -> None:
        """Проверка обязательности полей + лишние поля"""
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
            self,
            refill_id: int | str | None,
            refill_status: int | None,
            expected_code: int,
            expected_message: str | None,
            create_user_and_refill,
            request,
    ) -> None:
        """Проверка работы поля refillId в зависимости от переданного значения."""
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

    @staticmethod
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
        self,
        project: str | None,
        bonus_packet_id: int | str | None,
        expected_code: int,
        expected_message: str | None,
        create_user_and_refill,
        database_client: DBClient,
        request,
    ) -> None:
        """Проверка работы поля bonus_packet_id в зависимости от переданного значения."""
        user, refill_id = create_user_and_refill(0)
        if bonus_packet_id in ("valid_bonus_packet_id", "missing_bonus_packet_id"):
            bonus_packet_id = request.getfixturevalue(bonus_packet_id)
        before = self._read_state(database_client, refill_id)
        response = requests.put(
            f"{BASE_URL}/api/v1/bonus/packets/refill",
            json={"refillId": refill_id, "bonusPacketId": bonus_packet_id},
            headers=user.jwt_header,
            timeout=10,
        )
        assert response.status_code == expected_code
        after = self._read_state(database_client, refill_id)
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