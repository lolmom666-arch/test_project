import pymysql
import pymysql.cursors
from src.config import HOST, SSH_USER, PASSWORD, DATABASE, PORT


class DBClient:
    def __init__(self) -> None:
        """Подключиться к базе данных."""
        self.client: pymysql.connections.Connection | None = pymysql.connect(
            host=HOST,
            user=SSH_USER,
            port=PORT,
            password=PASSWORD,
            database=DATABASE,
            # API/SSH пишут через другие подключения: каждый SELECT должен
            # видеть уже зафиксированные изменения, без снимка прошлого теста.
            autocommit=True,
            connect_timeout=10,
            read_timeout=15,
            write_timeout=15,
        )

    def select(self, command: str, params: tuple = ()) -> list[tuple]:
        """Выполнить SELECT, вернуть все строки."""
        if self.client is None:
            raise RuntimeError("Нет активного соединения")
        with self.client.cursor() as cursors:
            cursors.execute(command, params)
            return list(cursors.fetchall())

    def update(self, command: str, params: tuple = ()) -> None:
        """Обновить запись."""
        if self.client is None:
            raise RuntimeError("Нет активного соединения")
        with self.client.cursor() as cursors:
            cursors.execute(command, params)
        self.client.commit()

    def delete(self, command: str, params: tuple = ()) -> None:
        """Удалить запись."""
        if self.client is None:
            raise RuntimeError("Нет активного соединения")
        with self.client.cursor() as cursors:
            cursors.execute(command, params)
        self.client.commit()

    def close(self) -> None:
        """Закрыть соединение."""
        if self.client is not None:
            self.client.close()
            self.client = None
