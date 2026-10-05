import shlex

from fabric import Connection
from src.config import SSH_USER, DEV_STAND, SSH_HOST


class SSHClient:
    def __init__(self) -> None:
        """Подключение по SSH."""
        self.client: Connection | None = Connection(
            host=f"{SSH_USER}@{DEV_STAND}.{SSH_HOST}", connect_timeout=10
        )

    def refill(self, user_id: str, amount: int = 1000) -> None:
        """Пополнение счета через консоль."""
        if type(amount) is not int or amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительным целым числом")
        self.command(shlex.join([
            "bin/console", "simulate:refill:greenback", f"-u{user_id}",
            f"-a{amount}", "-p270", "-t27001",
        ]))

    def command(self, command: str) -> None:
        """Запустить консольные команды."""
        if self.client is None:
            raise RuntimeError("Нет активного соединения")
        script = f"cd /var/www/mostbet/current && {command}"
        self.client.run(
            f"sudo -iu mostbet bash -c {shlex.quote(script)}",
            in_stream=False, hide=True, timeout=30,
        )

    def close(self) -> None:
        """Закрыть соединение."""
        if self.client is not None:
            self.client.close()
            self.client = None
