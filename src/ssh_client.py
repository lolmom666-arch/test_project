from fabric import Connection
from src.config import SSH_USER, DEV_STAND, SSH_HOST


class SSHClient:
    def __init__(self) -> None:
        """Подключение по SSH."""
        self.client: Connection | None = Connection(host=f"{SSH_USER}@{DEV_STAND}.{SSH_HOST}")

    def refill(self, user_id: str, amount: int = 1000) -> None:
        """Пополнение пользователя через консольную команду."""
        self.client.run(
            f"sudo -iu mostbet bash -c '/var/www/mostbet/current/"
            f"bin/console simulate:refill:greenback -u{user_id} -a{amount} -p270 -t27001'",
            in_stream=False, hide=True)

    def command(self, command: str) -> None:
        """Выполнение конкретной консольной команды."""
        self.client.run(f"sudo -iu mostbet bash -c '/var/www/mostbet/current/ "
                        f"{command}", in_stream=False, hide=True)

    def close(self) -> None:
        """Закрыть соединение."""
        if self.client is not None:
            self.client.close()
            self.client = None