"""Concurrent health checks (HTTP / TCP / disk) driven by a JSON file. Exit code 1 if anything is down."""
import argparse
import json
import shutil
import socket
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass


@dataclass
class Result:
    name: str
    ok: bool
    detail: str
    ms: float


def check_http(c: dict) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(c["url"], timeout=c.get("timeout", 5)) as r:
            code = r.status
    except urllib.error.HTTPError as e:
        code = e.code
    except Exception as e:  # DNS, refused, timeout...
        return False, f"{type(e).__name__}: {e}"
    want = c.get("expect", 200)
    return code == want, f"HTTP {code}" + ("" if code == want else f" (expected {want})")


def check_tcp(c: dict) -> tuple[bool, str]:
    try:
        with socket.create_connection((c["host"], c["port"]), timeout=c.get("timeout", 3)):
            return True, "port open"
    except OSError as e:
        return False, f"{type(e).__name__}: {e}"


def check_disk(c: dict) -> tuple[bool, str]:
    u = shutil.disk_usage(c["path"])
    pct = u.used / u.total * 100
    return pct <= c.get("max_percent", 90), f"{pct:.0f}% used"


CHECKS = {"http": check_http, "tcp": check_tcp, "disk": check_disk}


def run_one(c: dict) -> Result:
    t = time.perf_counter()
    ok, detail = CHECKS[c["type"]](c)
    return Result(c["name"], ok, detail, (time.perf_counter() - t) * 1000)


def run_all(checks: list[dict], workers: int = 20) -> list[Result]:
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(run_one, checks))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("config", help="JSON file: a list of checks")
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    with open(a.config, encoding="utf-8") as f:
        results = run_all(json.load(f), a.workers)
    if a.json:
        print(json.dumps([asdict(r) for r in results], ensure_ascii=False, indent=2))
    else:
        for r in results:
            print(f"{'OK  ' if r.ok else 'FAIL'} {r.name:<28} {r.detail:<40} {r.ms:6.0f} ms")
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
