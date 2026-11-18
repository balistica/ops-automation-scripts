from ops import logscan
from ops.loggen import generate


def test_parse_line():
    line = '1.2.3.4 - - [17/Nov/2026:10:05:09 +0000] "GET /api/x?a=1 HTTP/1.1" 502 10 "-" "curl"'
    assert list(logscan.parse([line])) == [("17/Nov/2026:10:05", "/api/x", 502)]


def test_garbage_lines_are_skipped():
    assert list(logscan.parse(["garbage", ""])) == []


def test_incident_is_detected_in_the_right_minute():
    r = logscan.analyze(generate(60000, incident_minute=37))
    assert [s["minute"] for s in r["spikes"]] == ["17/Nov/2026:10:37"]
    assert r["spikes"][0]["top_paths"][0][0] == "/api/orders"


def test_quiet_traffic_has_no_spikes():
    assert logscan.analyze(generate(60000, incident_minute=None))["spikes"] == []


def test_short_logs_do_not_crash():
    assert logscan.analyze(generate(10, minutes=2))["spikes"] == []
