import allure
import pytest
from src.db_client import DBClient


@allure.parent_suite("Team11")
@allure.suite("Bonus_packets")
@allure.sub_suite("/api/v1/bonus/packets/refill")
class TestAPIBonusPacketRefill:
    @allure.title("Запрос с пустым Authorization")
    @allure.tag("negative", "auth")
    @allure.description("Тест проверяет, что вызов метода без токена возвращает ошибку.")
    def test_bad_auth(
            self,
            bonus_packets_client
    ) -> None:
        token = {"Authorization": ""}
        with (allure.step("Делаем запрос без токена пользователя")):
            response = bonus_packets_client.put_bonus_packets_refill(
                body={"refillId": 1, "bonusPacketId": 50001},
                headers=token
            )
        with allure.step("Проверяем HTTP-статус 401"):
            assert response.status_code == 401
        with allure.step("Проверяем код и сообщение в ответе"):
            data = response.json()
            assert data["code"] == 401
            assert data["message"] == "JWT Token not found"


    @allure.title("Запрос с обязательными и дополнительными полями: {param_id}")
    @allure.tag("positive", "fields")
    @allure.description(
        "Проверяем успешный запрос с двумя обязательными полями,"
        "а также с одним и двумя дополнительными полями."
        "Ожидаем HTTP 200 и пустой список в ответе."
    )
    @pytest.mark.parametrize("fields", [
        pytest.param(("refillId", "bonusPacketId"), id="required_only"),
        pytest.param(("refillId", "bonusPacketId", "one_field"), id="plus_one_extra"),
        pytest.param(("refillId", "bonusPacketId", "one_field", "two_field"), id="plus_two_extra"),
    ])
    def test_positive_field_validations(
            self,
            fields: tuple[str, ...],
            create_user_and_refill,
            bonus_packets_client
    ) -> None:
        with allure.step("Создаём пользователя и пополнение в статусе 0, подготавливаем поля запроса"):
            user, refill_id = create_user_and_refill(0)
            all_values = {
                "refillId": refill_id,
                "bonusPacketId": 50001,
                "one_field": None,
                "two_field": None,
            }
        with allure.step(f"Отправляем запрос с полями: {', '.join(fields)}"):
            response = bonus_packets_client.put_bonus_packets_refill(
                body={key: all_values[key] for key in fields},
                headers= user.jwt_header
            )
        with allure.step("Проверяем HTTP-статус 200"):
            assert response.status_code == 200
        with allure.step("Проверяем тело ответа"):
            json_body = response.json()
            assert json_body == []


    @allure.title("Запрос без обязательных полей отклоняется: {param_id}")
    @allure.tag("negative", "fields")
    @allure.description(
        "Отправляем пустой JSON-объект или объект только с одним"
        "из двух обязательных полей: refillId и bonusPacketId."
        "Ожидаем HTTP 400, код VALIDATION и сообщение Validation failed."
    )
    @pytest.mark.parametrize("body_field", [
        pytest.param("", id="empty_body"),
        pytest.param("refillId", id="only_refillId"),
        pytest.param("bonusPacketId", id="only_bonusPacketId")
    ])
    def test_negative_field_validations(
            self,
            body_field: str,
            create_user_and_refill,
            bonus_packets_client
    ) -> None:
        with allure.step("Создаём пользователя и пополнение в статусе 0, подготавливаем поля запроса"):
            user, refill_id = create_user_and_refill(0)
            all_values = {
                "refillId": refill_id,
                "bonusPacketId": 50001,
            }
        with allure.step(f"Отправляем запрос: {body_field or 'пустое тело'}"):
            response = bonus_packets_client.put_bonus_packets_refill(
                body={body_field: all_values[body_field]} if body_field else {},
                headers=user.jwt_header,
            )
        with allure.step("Проверяем HTTP-статус 400"):
            assert response.status_code == 400
        with allure.step("Проверяем код и сообщение в ответе"):
            json_body = response.json()
            assert json_body["code"] == "VALIDATION"
            assert json_body["message"] == "Validation failed"


    @allure.title("Успешный выбор бонусного пакета при статусе пополнения {refill_status}")
    @allure.tag("positive", "field_refill")
    @allure.description(
        "Отправляем запрос с ID существующего пополнения в статусе 0 или 1."
        "Ожидаем HTTP 200 и пустой список в ответе."
    )
    @pytest.mark.parametrize("refill_status", [0, 1])
    def test_valid_refill_id(
            self,
            refill_status: int,
            create_user_and_refill,
            bonus_packets_client
    ) -> None:
        user, refill_id = create_user_and_refill(refill_status)
        with allure.step("Выполняем запрос"):
            response = bonus_packets_client.put_bonus_packets_refill(
                body={"refillId": refill_id, "bonusPacketId": 50001},
                headers=user.jwt_header)
        with allure.step("Проверяем HTTP-статус 200"):
            assert response.status_code == 200
        with allure.step("Проверяем тело ответа"):
            assert response.json() == []


    @allure.title("Выбор бонусного пакета отклоняется при статусе пополнения {refill_status}")
    @allure.tag("negative", "field_refill")
    @allure.description(
        "Отправляем запрос для пополнения в статусе 2 или 3."
        "Ожидаем HTTP 400 и сообщение refill_status_not_allowed."
    )
    @pytest.mark.parametrize("refill_status", [2, 3])
    def test_invalid_refill_status(
            self,
            refill_status: int,
            create_user_and_refill,
            bonus_packets_client,
    ) -> None:
        with allure.step(f"Создаём пользователя и пополнение в статусе {refill_status}"):
            user, refill_id = create_user_and_refill(refill_status)
            response = bonus_packets_client.put_bonus_packets_refill(
                body={"refillId": refill_id, "bonusPacketId": 50001},
                headers=user.jwt_header,
            )
        with allure.step("Проверяем HTTP-статус 400"):
            assert response.status_code == 400
        with allure.step("Проверяем тело ответа"):
            assert response.json()["message"] == "refill_status_not_allowed"


    @allure.title("Проверка валидация поля refill_id")
    @allure.tag("negative", "field_refill")
    @allure.description(
        "Отправляем запрос в поле refill_id указываем: None, -1000 и пустые скобки."
        "Ожидаем HTTP 400 и сообщение: Invalid request, refill_not_found, Validation failed."
    )
    @pytest.mark.parametrize("refill_id, expected_message", [
        (None, "Invalid request"),
        ("-1000", "refill_not_found"),
        ("", "Validation failed"),
    ])
    def test_invalid_refill_id(
            self,
            refill_id: int,
            expected_message: str,
            create_user,
            bonus_packets_client,
    ):
        response = bonus_packets_client.put_bonus_packets_refill(
            body = {"refillId": refill_id, "bonusPacketId": 50001},
            headers = create_user.jwt_header,
        )
        with allure.step("Проверяем HTTP-статус 400"):
            assert response.status_code == 400
        with allure.step("Проверяем тело ответа"):
            assert response.json()["message"] == expected_message


    @allure.title("Выбор бонусного пакета для чужого пополнения отклоняется")
    @allure.tag("negative", "field_refill")
    @allure.description(
        "Отправляем ID пополнения одного пользователя с токеном другого."
        "Ожидаем HTTP 400 и сообщение refill_not_found."
    )
    def test_incorrect_token_refill_id(
            self,
            create_user_and_refill,
            create_user,
            bonus_packets_client
    ) -> None:
        with allure.step("Получаем id пополнения и делаем запрос под токеном другого пользователя"):
            refill_id = create_user_and_refill(1)[1]
            response = bonus_packets_client.put_bonus_packets_refill(
                body={"refillId": refill_id, "bonusPacketId": 50001},
                headers=create_user.jwt_header,
            )
        with allure.step("Проверяем HTTP-статус 400"):
            assert response.status_code == 400
        with allure.step("Проверяем тело ответа"):
            assert response.json()["message"] == "refill_not_found"

    @staticmethod
    def _read_state(database_client: DBClient, refill_id: str) -> tuple[list[tuple], list[tuple]]:
        options = database_client.select(
            "SELECT id, value FROM user_selected_option WHERE entity_id = %s ORDER BY id",
            (refill_id,),
        )
        additional = database_client.select(
            "SELECT id, name, value FROM refill_additional_data WHERE refill_id = %s ORDER BY id",
            (refill_id,),
        )
        return options, additional


    @allure.title("Проверка валидация поля bonus_packet_id")
    @allure.tag("negative", "field_bonus_packet")
    @allure.description(
        "Отправляем запрос в поле bonus_packet_id указываем: act, пустые скобки, None, 111"
        "Ожидаем HTTP 400 и сообщение Invalid request и bonus_packet_not_found."
    )
    @pytest.mark.parametrize("bonus_packet_id, expected_message", [
        ("act", "Invalid request"),
        ("", "Invalid request"),
        (None, "Invalid request"),
        ("missing_bonus_packet_id", "bonus_packet_not_found"),
    ])
    def test_incorrect_bonus_packet_id(
            self,
            database_client,
            bonus_packet_id,
            create_user_and_refill,
            expected_message,
            request: pytest.FixtureRequest,
            bonus_packets_client,
    ) -> None:
        if bonus_packet_id == "missing_bonus_packet_id":
            bonus_packet_id = request.getfixturevalue(bonus_packet_id)
        user, refill_id = create_user_and_refill(0)
        before = self._read_state(database_client, refill_id)
        response = bonus_packets_client.put_bonus_packets_refill(
            body={"refillId": refill_id, "bonusPacketId": bonus_packet_id},
            headers=user.jwt_header,
        )
        with allure.step("Проверяем HTTP-статус 400"):
            assert response.status_code == 400
        after = self._read_state(database_client, refill_id)
        with allure.step("Сравнение записей в БД до и после выполнения запроса"):
            assert after == before
        with allure.step("Проверяем тело ответа"):
            assert response.json()["message"] == expected_message


    @allure.title("Проверка работы запроса с валидным БП MST.")
    @allure.tag("positive", "field_bonus_packet")
    @allure.description(
        "Отправляем запрос в поле bonus_packet_id указываем валидный БП MST."
        "Ожидаем HTTP 200 и пустой список в ответе."
        "Ожидаем пакет записан в БД user_selected_option."
        "Ожидаем три записи в таблице refill_additional_data"
        "и корректный 'value' в БД: bonus_package_id и bonus_package_source."
    )
    def test_mst_bonus_packets(
            self,
            create_user_and_refill,
            database_client: DBClient,
            valid_bonus_packet_id,
            bonus_packets_client
    ) -> None:
        user, refill_id = create_user_and_refill(0)
        response = bonus_packets_client.put_bonus_packets_refill(
            body = {"refillId": refill_id, "bonusPacketId": valid_bonus_packet_id},
            headers = user.jwt_header,
        )
        with allure.step("Проверяем HTTP-статус 200"):
            assert response.status_code == 200
        with allure.step("Проверяем тело ответа"):
            assert response.json() == []
        additional = self._read_state(database_client, refill_id)[1]
        matching = database_client.select(
            "SELECT id FROM user_selected_option "
            "WHERE entity_id = %s AND JSON_EXTRACT(value, '$.packetId') = %s",
            (refill_id, valid_bonus_packet_id),
        )
        with allure.step("Проверяем выбранный пакет записан в таблице user_selected_option"):
            assert matching, "Выбранный пакет не записан в user_selected_option"
        with allure.step("Проверяем в таблице refill_additional_data созданы 3 записи"):
            assert len(additional) == 3, f"Ожидалось 3 записи, получено {len(additional)}"
        data = {name: value for _, name, value in additional}
        with allure.step("Проверяем на дубли записи в БД"):
            assert len(data) == len(additional), "Имена дополнительных данных повторяются"
        with allure.step("Проверяем bonus_package_id корректно записан в БД"):
            assert data["bonus_package_id"] == str(valid_bonus_packet_id)
        with allure.step("Проверяем bonus_package_source корректно записан в БД"):
            assert data["bonus_package_source"] == "MOSTBET"

    @allure.title("Проверка работы поля bonus_packet_id с граничными значениями для БП MWL.")
    @allure.tag("positive", "field_bonus_packet")
    @allure.description(
        "Пакеты id >= 50000 относятся к проекту MWL."
        "Отправляем запрос с граничными значениями в поле bonus_packet_id указываем БП MWL (50000, 50001)."
        "Ожидаем HTTP 200 и пустой список в ответе."
        "Ожидаем три записи в таблице refill_additional_data"
        "и корректный 'value' в БД: bonus_package_id и bonus_package_source."
        "Не ожидаем записей в БД user_selected_option."
    )
    @pytest.mark.parametrize("bonus_packet_id", [50000, 50001])
    def test_mwl_bonus_packets(
            self,
            create_user_and_refill,
            database_client,
            bonus_packet_id,
            bonus_packets_client,
    ) -> None:
        user, refill_id = create_user_and_refill(0)
        options_before = self._read_state(database_client, refill_id)[0]
        response = bonus_packets_client.put_bonus_packets_refill(
            body={"refillId": refill_id, "bonusPacketId": bonus_packet_id},
            headers=user.jwt_header,
        )
        with allure.step("Проверяем HTTP-статус 200"):
            assert response.status_code == 200
        options_after, additional_after = self._read_state(database_client, refill_id)
        with allure.step("Проверяем тело ответа"):
            assert response.json() == []
        with allure.step("Сравнение записей в БД до и после выполнения запроса"):
            assert options_after == options_before, "MWL-запрос не должен был изменить user_selected_option"
        with allure.step("Проверяем в таблице refill_additional_data созданы 3 записи"):
            assert len(additional_after) == 3, f"Ожидалось 3 записи, получено {len(additional_after)}"
        data = {name: value for _, name, value in additional_after}
        with allure.step("Проверяем на дубли записи в БД"):
            assert len(data) == len(additional_after), "Имена дополнительных данных повторяются"
        with allure.step("Проверяем bonus_package_id верно записан в БД"):
            assert data["bonus_package_id"] == str(bonus_packet_id)
        with allure.step("Проверяем bonus_package_source верно записан в БД"):
            assert data["bonus_package_source"] == "MWL"
