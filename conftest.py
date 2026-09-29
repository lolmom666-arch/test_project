import pytest
from src.ssh_client import SSHClient
from src.bd_client import BDConnection
from src.one_click import one_click, get_password

@pytest.fixture(scope="module")
def ssh_client():
    """SSH-клиент на весь модуль тестов."""
    client = SSHClient()
    yield client
    client.close()

@pytest.fixture(scope="module")
def valid_token() -> str:
    """Получение token пользователя."""
    return "Bearer " + one_click()

@pytest.fixture()
def user_id(valid_token: str) -> int:
    """Получение user_id."""
    return int(get_password(valid_token).username)

@pytest.fixture()
def refill_id(ssh_client, user_id: int) -> int:
    """Пополняет юзера через SSH, сбрасывает status=0. Возвращает refill_id."""
    ssh_client.refill(user_id)
    """Подключение к базе данных"""
    bd = BDConnection()
    cursors = bd.cursor()
    cursors.execute(
        "SELECT * FROM refill WHERE (`user_id` = %s)", (user_id,))
    refill_id = cursors.fetchone()[0]
    cursors.execute(
        "UPDATE `refill` SET `status`=0 WHERE (`id`= %s)", (refill_id,))
    bd.commit()
    return refill_id

@pytest.fixture()
def valid_body(refill_id: int) -> dict:
    """Тело запроса."""
    return {"refillId": str(refill_id), "bonusPacketId": 212}