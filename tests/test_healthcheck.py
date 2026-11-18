import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from ops import healthcheck


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(500 if self.path == "/bad" else 200)
        self.end_headers()

    def log_message(self, *a):
        pass


@pytest.fixture(scope="module")
def srv():
    s = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    yield s
    s.shutdown()


def test_http_ok_and_fail(srv):
    base = f"http://127.0.0.1:{srv.server_port}"
    assert healthcheck.check_http({"url": base + "/"})[0] is True
    ok, detail = healthcheck.check_http({"url": base + "/bad"})
    assert ok is False and "500" in detail
    assert healthcheck.check_http({"url": base + "/bad", "expect": 500})[0] is True


def test_http_unreachable_is_failure_not_exception():
    assert healthcheck.check_http({"url": "http://127.0.0.1:1/", "timeout": 1})[0] is False


def test_tcp(srv):
    assert healthcheck.check_tcp({"host": "127.0.0.1", "port": srv.server_port})[0] is True
    s = socket.socket(); s.bind(("127.0.0.1", 0)); free = s.getsockname()[1]; s.close()
    assert healthcheck.check_tcp({"host": "127.0.0.1", "port": free, "timeout": 1})[0] is False


def test_disk_threshold():
    assert healthcheck.check_disk({"path": "/", "max_percent": 100})[0] is True
    assert healthcheck.check_disk({"path": "/", "max_percent": 0})[0] is False


def test_cli_exit_codes(srv, tmp_path, capsys):
    base = f"http://127.0.0.1:{srv.server_port}"
    good = tmp_path / "good.json"
    good.write_text(json.dumps([{"name": "web", "type": "http", "url": base + "/"}]))
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps([{"name": "web", "type": "http", "url": base + "/bad"}]))
    assert healthcheck.main([str(good)]) == 0
    assert healthcheck.main([str(bad)]) == 1
    assert "FAIL" in capsys.readouterr().out
