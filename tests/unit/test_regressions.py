import importlib.util
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src import one_click as registration
from src import ssh_client as ssh_module

ROOT = Path(__file__).resolve().parents[2]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Отдельные имена не зависят от того, какой conftest pytest импортировал последним.
fixtures = load_module("project_fixtures", ROOT / "conftest.py")
bonus_checks = load_module(
    "bonus_checks", ROOT / "tests/bonus_packets/api_v1_bonus_packets_refill/test_field_bonus_packet_id.py"
)


def test_all_integration_fixture_dependencies_resolve():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--setup-plan", "-q", "tests/bonus_packets"],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
        env={**os.environ, "PYTEST_ADDOPTS": "", "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_reads_see_external_commits_and_delete_persists(local_database):
    db, writer = local_database.client, local_database.writer
    assert db.select("SELECT id FROM refill") == []
    writer.execute("INSERT INTO refill (user_id, status) VALUES ('owner', 2)")
    assert db.select("SELECT id FROM refill") == [(1,)]
    db.delete("DELETE FROM refill WHERE id = %s", (1,))
    db.close()
    assert writer.execute("SELECT id FROM refill").fetchall() == []


def test_factory_keeps_ownership_and_sets_every_status(local_database, monkeypatch):
    db, writer = local_database.client, local_database.writer
    users = [registration.User(f"user_{i}", "password", {"Authorization": f"Bearer {i}"}) for i in range(4)]
    register = Mock(side_effect=users)
    monkeypatch.setattr(fixtures, "one_click", register)
    ssh = SimpleNamespace(refill=lambda username: writer.execute(
        "INSERT INTO refill (user_id, status) VALUES (?, 1)", (username,)
    ))
    request = Mock()
    request.getfixturevalue.side_effect = {"database_client": db, "ssh_client": ssh}.__getitem__
    factory = fixtures.create_user_and_refill.__wrapped__(request)
    request.getfixturevalue.assert_not_called()
    register.assert_not_called()
    for status, expected_user in enumerate(users):
        user, refill_id = factory(status)
        assert user is expected_user
        assert writer.execute("SELECT user_id, status FROM refill WHERE id = ?", (refill_id,)).fetchone() == (user.username, status)
        # Чтение между сценариями раньше оставляло снимок, скрывавший новую запись.
        assert db.select("SELECT id FROM refill WHERE id = %s", (refill_id,))


@pytest.mark.parametrize("status", [None, -1, 4, True, "0"])
def test_factory_rejects_invalid_status_without_creating_data(status):
    request = Mock()
    factory = fixtures.create_user_and_refill.__wrapped__(request)
    with pytest.raises(ValueError, match="Недопустимый статус"):
        factory(status)
    request.getfixturevalue.assert_not_called()


def test_refill_wait_is_bounded_and_reports_missing_data(monkeypatch):
    db = Mock()
    db.select.return_value = []
    monkeypatch.setattr(fixtures, "monotonic", Mock(side_effect=[0, 5]))
    with pytest.raises(RuntimeError, match="не появилось"):
        fixtures._wait_for_refill(db, "owner", timeout=5)


def test_refill_wait_handles_delayed_visibility(monkeypatch):
    db = Mock()
    db.select.side_effect = [[], [(42,)]]
    monkeypatch.setattr(fixtures, "sleep", lambda _: None)
    assert fixtures._wait_for_refill(db, "owner") == "42"


def test_ssh_command_runs_from_project_and_quotes_arguments(tmp_path, monkeypatch):
    connection = Mock()
    monkeypatch.setattr(ssh_module, "Connection", Mock(return_value=connection))
    client = ssh_module.SSHClient()
    client.command("printf '%s' 'value with quotes' > result.txt")
    outer = shlex.split(connection.run.call_args.args[0])
    assert outer[:5] == ["sudo", "-iu", "mostbet", "bash", "-c"]
    script = outer[5].replace("/var/www/mostbet/current", shlex.quote(str(tmp_path)))
    result = subprocess.run(["bash", "-c", script], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "result.txt").read_text() == "value with quotes"
    user_id = "user'; echo unintended-command"
    client.refill(user_id)
    script = shlex.split(connection.run.call_args.args[0])[5]
    args = shlex.split(script.partition(" && ")[2])
    assert args[2] == f"-u{user_id}"
    assert len(args) == 6


def test_registration_keeps_owner_token_and_timeouts(monkeypatch):
    post = Mock(return_value=SimpleNamespace(status_code=200, json=lambda: {"jwt": "owner-token"}))
    get = Mock(return_value=SimpleNamespace(status_code=200, json=lambda: {"username": "owner", "password": "secret"}))
    monkeypatch.setattr(registration.requests, "post", post)
    monkeypatch.setattr(registration.requests, "get", get)
    user = registration.one_click()
    assert user.jwt_header == get.call_args.kwargs["headers"] == {"Authorization": "Bearer owner-token"}
    assert post.call_args.kwargs["timeout"] == get.call_args.kwargs["timeout"] == 10
    assert "secret" not in repr(user) and "owner-token" not in repr(user)


@pytest.mark.parametrize("fault", ["wrong_mwl_option", "error_option", "error_metadata", "extra_metadata", "duplicate_key"])
def test_bonus_assertions_reject_incorrect_database_changes(fault, local_database, monkeypatch):
    project, packet_id, code, message = ("MWL", 50000, 200, None)
    if fault.startswith("error_"):
        project, packet_id, code, message = (None, None, 400, "Invalid request")
    user = registration.User("owner", "secret", {"Authorization": "Bearer owner"})
    writer = local_database.writer

    def put(*args, **kwargs):
        if fault in ("wrong_mwl_option", "error_option"):
            writer.execute("INSERT INTO user_selected_option (entity_id, value) VALUES (101, ?)", (json.dumps({"packetId": 42}),))
        rows = []
        if project:
            rows = [(101, "bonus_package_id", str(packet_id)), (101, "bonus_package_source", project), (101, "third_field", "value")]
        if fault in ("error_metadata", "extra_metadata"):
            rows.append((101, "unexpected", "value"))
        if fault == "duplicate_key":
            rows[-1] = rows[0]
        writer.executemany("INSERT INTO refill_additional_data (refill_id, name, value) VALUES (?, ?, ?)", rows)
        return SimpleNamespace(status_code=code, json=lambda: [] if project else {"message": message})

    monkeypatch.setattr(bonus_checks.requests, "put", put)
    with pytest.raises(AssertionError):
        bonus_checks.test_field_bonus_packet_id(
            project, packet_id, code, message, lambda status: (user, "101"), local_database.client, Mock()
        )


@pytest.mark.parametrize("project, packet_id, code, message", [
    ("MOSTBET", 42, 200, None), ("MWL", 50000, 200, None), (None, None, 400, "Invalid request"),
])
def test_bonus_assertions_accept_expected_changes(project, packet_id, code, message, local_database, monkeypatch):
    user = registration.User("owner", "secret", {"Authorization": "Bearer owner"})
    writer = local_database.writer

    def put(*args, **kwargs):
        if project == "MOSTBET":
            writer.execute("INSERT INTO user_selected_option (entity_id, value) VALUES (101, ?)", (json.dumps({"packetId": packet_id}),))
        if project:
            writer.executemany("INSERT INTO refill_additional_data (refill_id, name, value) VALUES (?, ?, ?)", [
                (101, "bonus_package_id", str(packet_id)), (101, "bonus_package_source", project), (101, "third_field", "value"),
            ])
        return SimpleNamespace(status_code=code, json=lambda: [] if project else {"message": message})

    monkeypatch.setattr(bonus_checks.requests, "put", put)
    bonus_checks.test_field_bonus_packet_id(
        project, packet_id, code, message, lambda status: (user, "101"), local_database.client, Mock()
    )


def test_missing_bonus_id_avoids_existing_rows(local_database):
    local_database.writer.execute("INSERT INTO bonus_packet VALUES (49999)")
    assert fixtures.missing_bonus_packet_id.__wrapped__(local_database.client) == 49998


def test_empty_bonus_table_has_actionable_error(local_database):
    local_database.writer.execute("DELETE FROM bonus_packet")
    with pytest.raises(pytest.fail.Exception, match="нужен бонусный пакет"):
        fixtures.valid_bonus_packet_id.__wrapped__(local_database.client)
