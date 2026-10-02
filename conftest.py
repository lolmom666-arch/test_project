import pytest
from src.one_click import User, one_click, get_password
from src.ssh_client import SSHClient
from src.db_client import DBClient

ALLOWED_STATUSES = (None, 0, 1, 2, 3)

@pytest.fixture(scope="module")
def ssh_client():
    """SSH-клиент для одного теста."""
    client = SSHClient()
    yield client
    client.close()


@pytest.fixture(scope="module")
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
def create_refill(request, ssh_client, database_client, create_user) -> str|None:
    status = getattr(request, "param", 2)
    assert status in ALLOWED_STATUSES, (
        f"Недопустимый статус {status}. Разрешены: {ALLOWED_STATUSES}"
    )
    if status is None:
        return None
    ssh_client.refill(create_user.username)
    refill_id = database_client.select(
    "SELECT id FROM refill WHERE user_id = %s ORDER BY id DESC LIMIT 1",
    (create_user.username,),
        )[0][0]
    if status in (0,1,3):
        database_client.update(
        "UPDATE refill SET status = %s WHERE id = %s",
        (status, refill_id,)
    )
    return str(refill_id)

@pytest.fixture()
def valid_bonus_packet_id(database_client: DBClient) -> int:
    """Возвращает ID любого Бонус пакета."""
    bonus_packet_id = database_client.select(
        "SELECT id FROM bonus_packet LIMIT 1",
    )[0][0]
    return bonus_packet_id
