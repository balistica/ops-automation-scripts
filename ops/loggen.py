"""Deterministic synthetic access-log generator with an optional incident (for demos, tests, benchmarks)."""
import random

PATHS = ["/", "/api/products", "/api/orders", "/api/login", "/static/app.js", "/api/cart", "/health"]


def generate(n_lines: int, minutes: int = 60, incident_minute: int | None = 37, seed: int = 7):
    rnd = random.Random(seed)
    per_min = max(1, n_lines // minutes)
    for mi in range(minutes):
        hh, mm = divmod(mi, 60)
        ts = f"17/Nov/2026:{10 + hh:02d}:{mm:02d}"
        for i in range(per_min):
            if mi == incident_minute and rnd.random() < 0.45:
                status, path = 502, "/api/orders"
            else:
                status = 500 if rnd.random() < 0.002 else rnd.choice([200] * 18 + [301, 404])
                path = rnd.choice(PATHS)
            yield f'10.0.{rnd.randint(0, 9)}.{rnd.randint(1, 250)} - - [{ts}:{i % 60:02d} +0000] "GET {path}?x={i} HTTP/1.1" {status} {rnd.randint(200, 5000)} "-" "curl/8"\n'


if __name__ == "__main__":
    import sys

    sys.stdout.writelines(generate(int(sys.argv[1]) if len(sys.argv) > 1 else 100000))
