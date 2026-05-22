import pytest

from src.db.repository import Repository


@pytest.fixture
async def repo(tmp_path):
    r = Repository(str(tmp_path / "test.db"))
    await r.init_db()
    return r


async def test_upsert_and_get_connection(repo):
    await repo.upsert_connection("conn1", 1, True, True)
    conn = await repo.get_connection("conn1")
    assert conn.user_id == 1
    assert conn.can_reply is True
    assert conn.is_active is True


async def test_upsert_connection_updates_existing(repo):
    await repo.upsert_connection("conn1", 1, True, True)
    await repo.upsert_connection("conn1", 1, False, False)
    conn = await repo.get_connection("conn1")
    assert conn.can_reply is False
    assert conn.is_active is False


async def test_get_connection_returns_none_for_missing(repo):
    result = await repo.get_connection("nonexistent")
    assert result is None


async def test_get_settings_creates_default(repo):
    s = await repo.get_settings(42)
    assert s.user_id == 42
    assert s.dnd_enabled is False
    assert s.ai_context == ""


async def test_update_dnd(repo):
    await repo.update_dnd(42, True)
    s = await repo.get_settings(42)
    assert s.dnd_enabled is True


async def test_update_ai_context(repo):
    await repo.update_ai_context(42, "I am a developer")
    s = await repo.get_settings(42)
    assert s.ai_context == "I am a developer"


async def test_log_and_retrieve_messages(repo):
    await repo.upsert_connection("conn1", 1, True, True)
    await repo.log_message("conn1", 100, "incoming", "Hello")
    await repo.log_message("conn1", 100, "outgoing", "Hi back")
    msgs = await repo.get_recent_messages("conn1", 100, limit=10)
    assert len(msgs) == 2
    assert msgs[0].text == "Hello"
    assert msgs[1].text == "Hi back"


async def test_get_recent_messages_respects_limit(repo):
    await repo.upsert_connection("conn1", 1, True, True)
    for i in range(15):
        await repo.log_message("conn1", 100, "incoming", f"msg {i}")
    msgs = await repo.get_recent_messages("conn1", 100, limit=5)
    assert len(msgs) == 5


async def test_get_last_outgoing(repo):
    await repo.upsert_connection("conn1", 1, True, True)
    await repo.log_message("conn1", 100, "incoming", "hi")
    await repo.log_message("conn1", 100, "outgoing", "first")
    await repo.log_message("conn1", 100, "outgoing", "second")
    last = await repo.get_last_outgoing("conn1", 100)
    assert last.text == "second"


async def test_get_last_outgoing_none_when_no_outgoing(repo):
    await repo.upsert_connection("conn1", 1, True, True)
    await repo.log_message("conn1", 100, "incoming", "hi")
    assert await repo.get_last_outgoing("conn1", 100) is None


async def test_get_recent_messages_returns_last_n_in_order(repo):
    await repo.upsert_connection("conn1", 1, True, True)
    for i in range(15):
        await repo.log_message("conn1", 100, "incoming", f"msg {i}")
    msgs = await repo.get_recent_messages("conn1", 100, limit=5)
    assert [m.text for m in msgs] == ["msg 10", "msg 11", "msg 12", "msg 13", "msg 14"]
