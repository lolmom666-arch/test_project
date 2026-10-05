from collections.abc import Callable, Iterator
from time import monotonic, sleep

import pytest

from src.one_click import User, one_click
from src.ssh_client import SSHClient
from src.db_client import DBClient

ALLOWED_STATUSES = (0, 1, 2, 3)
RefillFactory = Callable[[int], tuple[User, str]]


@pytest.fixture(scope="module")
def ssh_client() -> Iterator[SSHClient]:
    """SSH-клиент для одного тестового модуля."""
    client = SSHClient()
    try:
        yield client
    finally:
        client.close()


@pytest.fixture(scope="module")
def database_client() -> Iterator[DBClient]:
    """Клиент с независимыми запросами для одного тестового модуля."""
    client = DBClient()
    try:
        yield client
    finally:
        client.close()


@pytest.fixture()
def create_user() -> User:
    """Регистрация пользователя вместе с его заголовком авторизации."""
    return one_click()


@pytest.fixture()
def valid_bonus_packet_id(database_client: DBClient) -> int:
    """Обычный пакет из БД, исключая специальные значения MWL."""
    rows = database_client.select(
        "SELECT id FROM bonus_packet WHERE id NOT IN (%s, %s) ORDER BY id LIMIT 1",
        (50000, 50001),
    )
    if not rows:
        pytest.fail("Для MOSTBET-сценария нужен бонусный пакет в таблице bonus_packet")
    return int(rows[0][0])


@pytest.fixture()
def missing_bonus_packet_id(database_client: DBClient) -> int:
    """Свободный положительный ID ниже специальных значений MWL."""
    rows = database_client.select(
        "SELECT id FROM bonus_packet WHERE id BETWEEN %s AND %s", (49000, 49999)
    )
    available = set(range(49000, 50000)) - {int(row[0]) for row in rows}
    if not available:
        pytest.fail("Для отрицательного сценария нужен свободный ID в диапазоне 49000–49999")
    return max(available)


def _wait_for_refill(database_client: DBClient, username: str, timeout: float = 5) -> str:
    """Ограниченно ждать запись после завершения SSH-команды."""
    deadline = monotonic() + timeout
    while True:
        rows = database_client.select(
            "SELECT id FROM refill WHERE user_id = %s ORDER BY id DESC LIMIT 1",
            (username,),
        )
        if rows:
            return str(rows[0][0])
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise RuntimeError(f"Пополнение пользователя {username} не появилось за {timeout} с")
        sleep(min(0.2, remaining))


@pytest.fixture()
def create_user_and_refill(request: pytest.FixtureRequest) -> RefillFactory:
    """Фабрика: user, refill_id = create_user_and_refill(status).

    Каждый вызов регистрирует владельца пополнения. Подключения нужны только
    при вызове фабрики; отрицательные сценарии могут использовать create_user.
    """
    def _create(status: int = 2) -> tuple[User, str]:
        if type(status) is not int or status not in ALLOWED_STATUSES:
            raise ValueError(f"Недопустимый статус {status}. Разрешены: {ALLOWED_STATUSES}")

        database_client: DBClient = request.getfixturevalue("database_client")
        ssh_client: SSHClient = request.getfixturevalue("ssh_client")
        user = one_click()
        ssh_client.refill(user.username)
        refill_id = _wait_for_refill(database_client, user.username)
        database_client.update(
            "UPDATE refill SET status = %s WHERE id = %s", (status, refill_id)
        )
        return user, refill_id

    return _create
