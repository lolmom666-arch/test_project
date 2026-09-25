import pytest
import requests
from src.config import BASE_URL
from src.one_click import one_click, get_password
from src.ssh_conn import *
from src.bd_conn import client_db


GET_VALID_TOKEN = "Bearer " + one_click() # функция и фикстура
user_id = get_password(GET_VALID_TOKEN).username # функция и фикстура / токен параметр

cursors = client_db.cursor() # фнукция и фикстура/ что такое курсор?
conn_refill(ssh_connect(), user_id) # рефилл айди фнкуия
cursors.execute(
    "SELECT * FROM refill WHERE (`user_id` = %s)", (user_id))
refill_id = cursors.fetchone()[0] # функция и фистура / параметр курсор и юзер айди
cursors.execute(
    "UPDATE `refill` SET `status`=0 WHERE (`id`= %s)", (refill_id))
client_db.commit()
VALID_BODY = {
    "refillId": f"{refill_id}",
    "bonusPacketId": 212
}


"""Проверка авторизации."""


@pytest.mark.parametrize("jwt_token, status_code", [
    (GET_VALID_TOKEN, 200),
    ("", 401)
])
def test_auth(jwt_token: str, status_code: int): # токен и ерфилл
    headers = {"Authorization": jwt_token}
    auth = requests.put(f"{BASE_URL}/api/v1/bonus/packets/refill", json=VALID_BODY, headers=headers, timeout=10)
    status_auth = auth.status_code
    auth_text = auth.json()
    assert status_auth == status_code
    match status_code:
        case 200:
            assert auth_text == []
        case 401:
            assert auth_text['code'] == 401
            assert auth_text['message'] == "JWT Token not found"


