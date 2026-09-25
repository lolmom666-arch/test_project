import json
import requests
from src.config import BASE_URL
from dataclasses import dataclass


@dataclass
class User:
    username: str
    password: str


"""Регистрация в one_click."""


def one_click(currencyId: str = "3", countryId: str = "3159",
              bonusType: str = "casino") -> str:  # -> это функция вернет тип Х
    payload = {
        "fos_user_registration_form[currencyId]": currencyId,
        "fos_user_registration_form[oferta_agreement]": "1",
        "fos_user_registration_form[countryId]": countryId,
        "first_refill_bonus_type_choice": bonusType,
    }
    reg = requests.post(f"{BASE_URL}/api/v1/registration/one_click", data=payload)
    if reg.status_code != 200:
        raise RuntimeError(
            f"Ошибка API: {reg.status_code}, тело: {reg.text}")  # это выбросить ошибку и остановить функцию
    return json.loads(reg.text)["jwt"]  # разбери текст ответа и верни значение по ключу jwt


"""Получение username и password."""


def get_password(jwt: str) -> User:
    headers_data = {"Authorization": jwt}
    get = requests.get(f"{BASE_URL}/api/v1/registration/one_click/get_password.json", headers=headers_data)
    if get.status_code != 200:
        raise RuntimeError(f"Ошибка API: {get.status_code}, тело: {get.text}")

    get_text = get.text  # взять у объекта его текстовую часть
    pass_log = json.loads(get_text)  # превращает строку в формате json в словарь питона
    return User(pass_log["username"], pass_log["password"])