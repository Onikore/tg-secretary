from types import SimpleNamespace

from src.handlers.connection import can_reply


def test_can_reply_from_rights_true():
    update = SimpleNamespace(rights=SimpleNamespace(can_reply=True), can_reply=None)
    assert can_reply(update) is True


def test_can_reply_from_rights_false():
    update = SimpleNamespace(rights=SimpleNamespace(can_reply=False), can_reply=None)
    assert can_reply(update) is False


def test_can_reply_legacy_fallback():
    # Older payloads without rights still expose the deprecated top-level field.
    update = SimpleNamespace(rights=None, can_reply=True)
    assert can_reply(update) is True


def test_can_reply_none_means_false():
    update = SimpleNamespace(rights=None, can_reply=None)
    assert can_reply(update) is False
