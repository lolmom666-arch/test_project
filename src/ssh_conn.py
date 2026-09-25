from fabric import Connection

from src.config import SSH_USER, DEV_STAND, SSH_HOST


def ssh_connect() -> Connection:
    """Подключение по SSH."""
    host = f"{DEV_STAND}.{SSH_HOST}"
    return Connection(host=f"{SSH_USER}@{host}")


def conn_refill(conn, user_id: str, amount=1000):
    """Пополнение юзера через консольную команду."""
    conn.run(
        f"sudo -iu mostbet bash -c '/var/www/mostbet/current/bin/console simulate:refill:greenback -u{user_id} -a{amount} -p270 -t27001'",
        in_stream=False, hide=True)