from src.handlers.commands import HELP_TEXT, _fmt_min, _parse_hhmm


def test_parse_hhmm_valid():
    assert _parse_hhmm("00:00") == 0
    assert _parse_hhmm("09:30") == 570
    assert _parse_hhmm("23:59") == 1439


def test_parse_hhmm_invalid_format():
    assert _parse_hhmm("9") is None
    assert _parse_hhmm("09-30") is None
    assert _parse_hhmm("09:30:00") is None
    assert _parse_hhmm("ab:cd") is None


def test_parse_hhmm_out_of_range():
    assert _parse_hhmm("24:00") is None
    assert _parse_hhmm("12:60") is None
    assert _parse_hhmm("-1:00") is None


def test_fmt_min():
    assert _fmt_min(0) == "00:00"
    assert _fmt_min(570) == "09:30"
    assert _fmt_min(1439) == "23:59"


def test_parse_fmt_roundtrip():
    for value in ("00:00", "07:05", "13:45", "23:59"):
        assert _fmt_min(_parse_hhmm(value)) == value


def test_help_lists_commands():
    for cmd in ("/dnd", "/quiet", "/rules", "/here", "/status"):
        assert cmd in HELP_TEXT
