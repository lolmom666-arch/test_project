import pytest
from src.one_click import one_click, get_password
from src.ssh_conn import *
from src.bd_conn import client_db

@pytest.fixture(scope="module")
def get_one_click_token():
    return "Bearer " + one_click()

@pytest.fixture()
def get_user_id(get_one_click_token: str):
    return get_password(get_one_click_token).username

@pytest.fixture()
def connection_bd(get_user_id: int):
    cursors = client_db.cursor()
    conn_refill(ssh_connect(), get_user_id)
    cursors.execute(
        "SELECT * FROM refill WHERE (`user_id` = %s)", (get_user_id))
    refill_id = cursors.fetchone()[0]
    cursors.execute(
        "UPDATE `refill` SET `status`=0 WHERE (`id`= %s)", (refill_id))
    client_db.commit()
    return

@pytest.fixture()
def get_refill_id(cursors, get_user_id):
    refill_id = cursors.fetchone()[0]
    valid_body = {
        "refillId": f"{refill_id}",
        "bonusPacketId": 212
    }

