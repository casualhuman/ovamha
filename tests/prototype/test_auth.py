"""Offline login: hashed PINs, wrong PIN, lockout."""
import json

import pytest

from ovamha_proto import auth


@pytest.fixture
def users(tmp_path, monkeypatch):
    salt, h = auth.hash_pin("123456")
    f = tmp_path / "users.json"
    f.write_text(json.dumps({"users": [{"username": "test", "worker_id": "nurse-test", "display_name": "Nurse Test", "role": "Nurse",
                                        "facility": "Test CHP", "pin_salt": salt, "pin_hash": h}]}))
    monkeypatch.setattr(auth, "USERS_FILE", f)
    monkeypatch.setattr(auth, "_failures", {})
    return f


def test_pin_not_stored_in_clear(users):
    assert "123456" not in users.read_text()


def test_login_ok(users):
    w, err = auth.login("test", "123456")
    assert w and w.display_name == "Nurse Test" and err == ""


def test_wrong_pin(users):
    w, err = auth.login("test", "000000")
    assert w is None and "wrong" in err


def test_lockout_after_five_wrong(users):
    for _ in range(5):
        auth.login("test", "000000")
    w, err = auth.login("test", "123456")  # correct PIN is refused while locked
    assert w is None and "Too many" in err


def test_demo_users_file_has_no_plain_pins():
    data = json.loads(auth.USERS_FILE.read_text())
    assert all(set(u) >= {"pin_salt", "pin_hash"} and "pin" not in u for u in data["users"])


def test_username_case_insensitive(users):
    assert auth.login("TEST", "123456")[0] is not None


def test_unknown_user_same_message_as_wrong_pin(users):
    _, a = auth.login("nobody", "123456")
    _, b = auth.login("test", "999999")
    assert a.split(".")[0] == b.split(".")[0] == "Username or PIN is wrong"
