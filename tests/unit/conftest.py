import sqlite3
from types import SimpleNamespace

import fabric
import pymysql
import pytest
import requests

from src.db_client import DBClient


@pytest.fixture(autouse=True)
def block_external_services(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Unit-тест не должен обращаться к внешним HTTP/SSH/MySQL")

    monkeypatch.setattr(requests.sessions.Session, "request", blocked)
    monkeypatch.setattr(pymysql, "connect", blocked)
    monkeypatch.setattr(fabric.Connection, "open", blocked)


class Cursor:
    def __init__(self, connection, autocommit):
        self.connection = connection
        self.autocommit = autocommit
        self.cursor = connection.cursor()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.cursor.close()

    def execute(self, sql, params):
        # SQLite сама не начинает транзакцию на SELECT. Явный BEGIN
        # моделирует время жизни снимка при MySQL autocommit=False.
        if not self.autocommit and not self.connection.in_transaction:
            self.connection.execute("BEGIN")
        return self.cursor.execute(sql.replace("%s", "?"), params)

    def fetchall(self):
        return self.cursor.fetchall()


class Connection:
    def __init__(self, connection, autocommit):
        self.connection = connection
        self.autocommit = autocommit

    def cursor(self):
        return Cursor(self.connection, self.autocommit)

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()


@pytest.fixture
def local_database(tmp_path, monkeypatch):
    path = tmp_path / "database.sqlite"
    writer = sqlite3.connect(path, isolation_level=None)
    writer.execute("PRAGMA journal_mode=WAL")
    writer.executescript("""
        CREATE TABLE refill (id INTEGER PRIMARY KEY, user_id TEXT, status INTEGER);
        CREATE TABLE bonus_packet (id INTEGER PRIMARY KEY);
        INSERT INTO bonus_packet VALUES (42);
        CREATE TABLE user_selected_option (id INTEGER PRIMARY KEY, entity_id INTEGER, value TEXT);
        CREATE TABLE refill_additional_data (id INTEGER PRIMARY KEY, refill_id INTEGER, name TEXT, value TEXT);
    """)
    reader = sqlite3.connect(path, isolation_level=None)
    monkeypatch.setattr(pymysql, "connect", lambda **kwargs: Connection(reader, kwargs.get("autocommit", False)))
    client = DBClient()
    try:
        yield SimpleNamespace(client=client, writer=writer)
    finally:
        client.close()
        writer.close()
