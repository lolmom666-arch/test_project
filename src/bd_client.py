import pymysql
import pymysql.cursors
from src.config import HOST, SSH_USER, PASSWORD, DATABASE, PORT


class BDConnection:
    def __init__(self) -> None:
        """Подключиться к базе данных."""
        self.data = {
            "host": HOST,
            "user": SSH_USER,
            "port": PORT,
            "password": PASSWORD,
            "database": DATABASE,
        }
        self.client: pymysql.connections.Connection | None = pymysql.connect(**self.data)

    def cursor(self) -> pymysql.cursors.Cursor:
        """Вернуть курсор для запросов."""
        if self.client is None:
            raise RuntimeError("Соединение закрыто.")
        return self.client.cursor()

    def commit(self) -> None:
        """Зафиксировать транзакцию."""
        if self.client is None:
            raise RuntimeError("Соединение закрыто.")
        self.client.commit()

    def close(self) -> None:
        """Закрыть соединение."""
        if self.client is not None:
            self.client.close()
            self.client = None