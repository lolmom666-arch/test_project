from dataclasses import dataclass, field
from src.httpx_client import UserClient


@dataclass
class User:
    username: str
    password: str = field(repr=False)
    jwt_header: dict[str, str] = field(repr=False)


def one_click(
        *,
        user_client: UserClient,
        currencyId: str = "3",
        countryId: str = "3159",
        bonusType: str = "casino"
) -> User:
    """Регистрация в one_click."""
    payload = {
        "fos_user_registration_form[currencyId]": currencyId,
        "fos_user_registration_form[oferta_agreement]": "1",
        "fos_user_registration_form[countryId]": countryId,
        "first_refill_bonus_type_choice": bonusType,
    }
    response = user_client.post_registration_one_click(payload=payload)
    if response.status_code != 200:
        raise RuntimeError(
            f"Ошибка API: {response.status_code}, тело: {response.text}")
    jwt = response.json()["jwt"]
    jwt_header = {"Authorization": f"Bearer {jwt}"}
    return get_password(client=user_client,  header=jwt_header)


def get_password(
        *,
        client: UserClient,
        header: dict[str, str]
) -> User:
    """Получение username и password."""
    response = client.get_registration_one_click_get_password(header)
    if response.status_code != 200:
        raise RuntimeError(f"Ошибка API: {response.status_code}, тело: {response.text}")
    data = response.json()
    return User(data["username"], data["password"], header)
