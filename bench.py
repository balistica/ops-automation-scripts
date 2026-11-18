"""Reproducible benchmarks for the README numbers: python bench.py"""
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from ops import healthcheck, logscan
from ops.loggen import generate


class Slow(BaseHTTPRequestHandler):
    def do_GET(self):
        time.sleep(0.1)  # a typical 100 ms service response
        self.send_response(200); self.end_headers()

    def log_message(self, *a):
        pass


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Slow)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    checks = [{"name": f"svc-{i}", "type": "http", "url": f"http://127.0.0.1:{srv.server_port}/{i}"} for i in range(50)]
    t = time.perf_counter(); [healthcheck.run_one(c) for c in checks]; seq = time.perf_counter() - t
    t = time.perf_counter(); healthcheck.run_all(checks, 20); par = time.perf_counter() - t
    print(f"healthcheck, 50 endpoints @100ms: sequential {seq:.2f}s | 20 threads {par:.2f}s | x{seq / par:.1f}")

    lines = list(generate(500_000, minutes=120, incident_minute=77))
    t = time.perf_counter(); r = logscan.analyze(lines); el = time.perf_counter() - t
    print(f"logscan, {r['lines']:,} lines: {el:.2f}s | {r['lines'] / el:,.0f} lines/s | spikes: "
          f"{[(s['minute'], s['errors']) for s in r['spikes']]}")


if __name__ == "__main__":
    main()
