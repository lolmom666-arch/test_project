import json
import requests
from src.config import BASE_URL
from dataclasses import dataclass


@dataclass
class User:
    username: str
    password: str


def one_click(
        currencyId: str = "3",
        countryId: str = "3159",
        bonusType: str = "casino"
) -> str:
    """Регистрация в one_click."""
    payload = {
        "fos_user_registration_form[currencyId]": currencyId,
        "fos_user_registration_form[oferta_agreement]": "1",
        "fos_user_registration_form[countryId]": countryId,
        "first_refill_bonus_type_choice": bonusType,
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/registration/one_click",
        data=payload,
        timeout=10
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"Ошибка API: {response.status_code}, тело: {response.text}")
    jwt = response.json()["jwt"]
    return f"Bearer {jwt}"


def get_password(headers) -> User:
    """Получение username и password."""
    response = requests.get(
        f"{BASE_URL}/api/v1/registration/one_click/get_password.json",
        headers=headers,
        timeout=10
    )
    if response.status_code != 200:
        raise RuntimeError(f"Ошибка API: {response.status_code}, тело: {response.text}")

    data = response.json()
    return User(data["username"], data["password"])