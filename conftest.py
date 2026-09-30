import pytest
from src.one_click import User, one_click, get_password
from src.ssh_client import SSHClient
from src.db_client import DBClient


@pytest.fixture()
def ssh_client():
    """SSH-клиент для одного теста."""
    client = SSHClient()
    yield client
    client.close()


@pytest.fixture()
def database_client():
    """БД-клиент для одного теста."""
    client = DBClient()
    yield client
    client.close()

@pytest.fixture()
def token_header() -> dict[str, str]:
    """Получение token пользователя."""
    token = one_click()
    header = {"Authorization": token}
    return header

@pytest.fixture()
def create_user(token_header) -> User:
    """Получение username и password."""
    return get_password(token_header)

@pytest.fixture()
def create_refill(ssh_client: SSHClient, database_client: DBClient, create_user: User) -> str:
    """Пополнение счета через SSH-клиент, возвращает refill_id."""
    ssh_client.refill(create_user.username)
    refill_id = database_client.select(
        "SELECT id FROM refill WHERE user_id = %s",
        (create_user.username,),
    )[0][0]
    return str(refill_id)

@pytest.fixture()
def valid_bonus_packet_id(database_client:  DBClient) -> int:
    """Возвращает ID любого Бонус пакета."""
    bonus_packet_id = database_client.select(
        "SELECT id FROM bonus_packet LIMIT 1",
    )[0][0]
    return bonus_packet_id