import allure
import pytest
from src.db_client import DBClient


@pytest.mark.integration
@allure.parent_suite("Team11")
@allure.suite("Bonus_packets")
@allure.sub_suite("/api/v1/bonus/packets/refill")
class TestAPIBonusPacketRefill:
    @allure.title("Запрос с пустым заголовком Authorization отклоняется")
    @allure.testcase(
        "https://media.test8bit.com/testrail/index.php?/cases/view/12566511",
        name="Авторизация",
    )
    @allure.tag("negative", "auth")
    @allure.description(
        "Отправляем запрос с пустым заголовком Authorization. "
        "Ожидаем HTTP 401 и сообщение JWT Token not found."
    )
    def test_bad_auth(
            self,
            bonus_packets_client
    ) -> None:
        token = {"Authorization": ""}
        with (allure.step("Отправляем запрос с пустым заголовком Authorization")):
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
    @allure.testcase(
        "https://media.test8bit.com/testrail/index.php?/cases/view/12574129",
        name="Проверка обязательности полей",
    )
    @allure.tag("positive", "fields")
    @allure.description(
        "Отправляем запрос с обязательными полями refillId и bonusPacketId. "
        "Состав дополнительных полей определяется сценарием. "
        "Ожидаем HTTP 200 и пустой JSON-массив в ответе."
    )
    @pytest.mark.parametrize("fields", [
        pytest.param(("refillId", "bonusPacketId"), id="Только обязательные поля"),
        pytest.param(("refillId", "bonusPacketId", "one_field"), id="Одно дополнительное поле"),
        pytest.param(("refillId", "bonusPacketId", "one_field", "two_field"), id="Два дополнительных поля"),
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
    @allure.testcase(
        "https://media.test8bit.com/testrail/index.php?/cases/view/12574129",
        name="Проверка обязательности полей",
    )
    @allure.tag("negative", "fields")
    @allure.description(
        "Отправляем запрос с неполным набором обязательных полей, указанным в сценарии. "
        "Ожидаем HTTP 400, код VALIDATION и сообщение Validation failed."
    )
    @pytest.mark.parametrize("body_field", [
        pytest.param("", id="Пустой JSON-объект"),
        pytest.param("refillId", id="Отсутствует bonusPacketId"),
        pytest.param("bonusPacketId", id="Отсутствует refillId")
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
        with allure.step(f"Отправляем JSON-объект: {body_field or 'пустой объект {}'}"):
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


    @allure.title("Успешный выбор бонусного пакета: {param_id}")
    @allure.testcase(
        "https://media.test8bit.com/testrail/index.php?/cases/view/12566512",
        name="Валидация refillId",
    )
    @allure.tag("positive", "field_refill")
    @allure.description(
        "Выбираем пакет MWL с ID 50001 для пополнения в статусе, указанном в сценарии. "
        "Используем токен владельца. "
        "Ожидаем HTTP 200 и пустой JSON-массив в ответе."
    )
    @pytest.mark.parametrize("refill_status", [
        pytest.param(0, id="Статус пополнения 0"),
        pytest.param(1, id="Статус пополнения 1"),
    ])
    def test_valid_refill_id(
            self,
            refill_status: int,
            create_user_and_refill,
            bonus_packets_client
    ) -> None:
        user, refill_id = create_user_and_refill(refill_status)
        with allure.step("Отправляем запрос на выбор бонусного пакета для пополнения"):
            response = bonus_packets_client.put_bonus_packets_refill(
                body={"refillId": refill_id, "bonusPacketId": 50001},
                headers=user.jwt_header)
        with allure.step("Проверяем HTTP-статус 200"):
            assert response.status_code == 200
        with allure.step("Проверяем тело ответа"):
            assert response.json() == []


    @allure.title("Выбор бонусного пакета отклоняется: {param_id}")
    @allure.testcase(
        "https://media.test8bit.com/testrail/index.php?/cases/view/12566512",
        name="Валидация refillId",
    )
    @allure.tag("negative", "field_refill")
    @allure.description(
        "Запрашиваем выбор бонусного пакета для пополнения в запрещённом статусе, "
        "указанном в сценарии. "
        "Ожидаем HTTP 400 и сообщение refill_status_not_allowed."
    )
    @pytest.mark.parametrize("refill_status", [
        pytest.param(2, id="Запрещённый статус пополнения 2"),
        pytest.param(3, id="Запрещённый статус пополнения 3"),
    ])
    def test_invalid_refill_status(
            self,
            refill_status: int,
            create_user_and_refill,
            bonus_packets_client,
    ) -> None:
        with allure.step(f"Создаём пополнение в статусе {refill_status} и отправляем запрос на выбор пакета"):
            user, refill_id = create_user_and_refill(refill_status)
            response = bonus_packets_client.put_bonus_packets_refill(
                body={"refillId": refill_id, "bonusPacketId": 50001},
                headers=user.jwt_header,
            )
        with allure.step("Проверяем HTTP-статус 400"):
            assert response.status_code == 400
        with allure.step("Проверяем тело ответа"):
            assert response.json()["message"] == "refill_status_not_allowed"


    @allure.title("Запрос с некорректным refillId отклоняется: {param_id}")
    @allure.testcase(
        "https://media.test8bit.com/testrail/index.php?/cases/view/12566512",
        name="Валидация refillId",
    )
    @allure.tag("negative", "field_refill")
    @allure.description(
        "Отправляем запрос со значением refillId, указанным в сценарии. "
        "Ожидаем HTTP 400 и сообщение об ошибке, соответствующее этому значению."
    )
    @pytest.mark.parametrize("refill_id, expected_message", [
        pytest.param(None, "Invalid request", id="Значение null"),
        pytest.param("-1000", "refill_not_found", id="Отрицательный ID в виде строки"),
        pytest.param("", "Validation failed", id="Пустая строка"),
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
    @allure.testcase(
        "",
        name="",
    )
    @allure.tag("negative", "field_refill")
    @allure.description(
        "Запрашиваем выбор бонусного пакета для пополнения другого пользователя в статусе 1. "
        "Ожидаем HTTP 400 и сообщение refill_not_found."
    )
    def test_incorrect_token_refill_id(
            self,
            create_user_and_refill,
            create_user,
            bonus_packets_client
    ) -> None:
        with allure.step("Создаём пополнение и отправляем запрос с токеном другого пользователя"):
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


    @allure.title("Запрос с некорректным bonusPacketId отклоняется: {param_id}")
    @allure.testcase(
        "https://media.test8bit.com/testrail/index.php?/cases/view/12573068",
        name="Валидация bonusPacketId",
    )
    @allure.tag("negative", "field_bonus_packet")
    @allure.description(
        "Отправляем запрос со значением bonusPacketId, указанным в сценарии. "
        "Ожидаем HTTP 400 и соответствующее сообщение об ошибке. "
        "Проверяем, что записи пополнения в user_selected_option "
        "и refill_additional_data не изменились."
    )
    @pytest.mark.parametrize("bonus_packet_id, expected_message", [
        pytest.param("act", "Invalid request", id="Текст вместо ID"),
        pytest.param("", "Invalid request", id="Пустая строка"),
        pytest.param(None, "Invalid request", id="Значение null"),
        pytest.param("missing_bonus_packet_id", "bonus_packet_not_found", id="Несуществующий ID пакета"),
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


    @allure.title("Выбор бонусного пакета MOSTBET сохраняется в БД")
    @allure.testcase(
        "https://media.test8bit.com/testrail/index.php?/cases/view/12573068",
        name="Валидация bonusPacketId",
    )
    @allure.tag("positive", "field_bonus_packet")
    @allure.description(
        "Выбираем существующий пакет MOSTBET для пополнения в статусе 0. "
        "Ожидаем HTTP 200 и пустой JSON-массив. "
        "Проверяем наличие выбранного packetId в user_selected_option, "
        "ровно три записи с уникальными именами в refill_additional_data, "
        "корректный bonus_package_id и источник MOSTBET."
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
        with allure.step("Проверяем наличие выбранного пакета в user_selected_option"):
            assert matching, "Выбранный пакет не записан в user_selected_option"
        with allure.step("Проверяем, что в refill_additional_data ровно три записи для пополнения"):
            assert len(additional) == 3, f"Ожидалось 3 записи, получено {len(additional)}"
        data = {name: value for _, name, value in additional}
        with allure.step("Проверяем уникальность имён записей в refill_additional_data"):
            assert len(data) == len(additional), "Имена дополнительных данных повторяются"
        with allure.step("Проверяем, что bonus_package_id совпадает с ID выбранного пакета"):
            assert data["bonus_package_id"] == str(valid_bonus_packet_id)
        with allure.step("Проверяем, что bonus_package_source равен MOSTBET"):
            assert data["bonus_package_source"] == "MOSTBET"

    @allure.title("Выбор бонусного пакета MWL: {param_id}")
    @allure.testcase(
        "https://media.test8bit.com/testrail/index.php?/cases/view/12573068",
        name="Валидация bonusPacketId",
    )
    @allure.tag("positive", "field_bonus_packet")
    @allure.description(
        "Выбираем пакет MWL с ID, указанным в сценарии, для пополнения в статусе 0. "
        "Ожидаем HTTP 200 и пустой JSON-массив. "
        "Проверяем отсутствие изменений в user_selected_option, "
        "наличие ровно трёх записей с уникальными именами в refill_additional_data, "
        "корректный bonus_package_id и источник MWL."
    )
    @pytest.mark.parametrize("bonus_packet_id", [
        pytest.param(50000, id="Пакет 50000"),
        pytest.param(50001, id="Пакет 50001"),
    ])
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
        with allure.step("Проверяем, что записи user_selected_option не изменились"):
            assert options_after == options_before, "MWL-запрос не должен был изменить user_selected_option"
        with allure.step("Проверяем, что в refill_additional_data ровно три записи для пополнения"):
            assert len(additional_after) == 3, f"Ожидалось 3 записи, получено {len(additional_after)}"
        data = {name: value for _, name, value in additional_after}
        with allure.step("Проверяем уникальность имён записей в refill_additional_data"):
            assert len(data) == len(additional_after), "Имена дополнительных данных повторяются"
        with allure.step("Проверяем, что bonus_package_id совпадает с ID выбранного пакета"):
            assert data["bonus_package_id"] == str(bonus_packet_id)
        with allure.step("Проверяем, что bonus_package_source равен MWL"):
            assert data["bonus_package_source"] == "MWL"
