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
def create_user() -> User:
    """Получение username и password."""
    return one_click()


@pytest.fixture()
def valid_bonus_packet_id(database_client: DBClient) -> int:
    """Возвращает ID любого Бонус пакета."""
    bonus_packet_id = database_client.select(
        "SELECT id FROM bonus_packet LIMIT 1",
    )[0][0]
    return bonus_packet_id


@pytest.fixture()
def create_user_and_refill(request, ssh_client, database_client):
    refill_status: int | None = getattr(request, "param", 2)
    assert refill_status in ALLOWED_STATUSES, (
        f"Недопустимый статус {refill_status}. Разрешены: {ALLOWED_STATUSES}"
    )

    def _create(status=refill_status):
        if status is None:
            return None

        user = one_click()
        ssh_client.refill(user.username)
        refill_id = database_client.select(
            "SELECT id FROM refill WHERE user_id = %s ORDER BY id DESC LIMIT 1",
            (user.username,),
        )[0][0]
        if status in (0, 1, 3):
            database_client.update(
                "UPDATE refill SET status = %s WHERE id = %s",
                (status, refill_id,)
            )
        return user, str(refill_id)

    return _create
