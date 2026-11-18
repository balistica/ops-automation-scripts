"""Scan an access log (nginx 'combined'-like), find 5xx spikes and the endpoints behind them."""
import argparse
import re
import statistics
import sys
from collections import Counter, defaultdict

LINE = re.compile(r'\[(?P<ts>\d{2}/\w{3}/\d{4}:\d{2}:\d{2}):\d{2} [^\]]+\] "(?P<m>\w+) (?P<path>\S+) [^"]*" (?P<status>\d{3}) ')


def parse(lines):
    for ln in lines:
        m = LINE.search(ln)
        if m:
            yield m["ts"], m["path"].split("?")[0], int(m["status"])


def analyze(lines, sigma: float = 3.0, min_errors: int = 20):
    total = defaultdict(int)
    errors = defaultdict(int)
    by_path = defaultdict(Counter)
    n = 0
    for ts, path, status in parse(lines):
        n += 1
        total[ts] += 1
        if status >= 500:
            errors[ts] += 1
            by_path[ts][path] += 1
    minutes = sorted(total)
    counts = [errors[m] for m in minutes]
    spikes = []
    if len(counts) >= 5:
        mean, sd = statistics.fmean(counts), statistics.pstdev(counts)
        thr = max(mean + sigma * sd, min_errors)
        for m in minutes:
            if errors[m] > thr:
                spikes.append({"minute": m, "errors": errors[m], "requests": total[m],
                               "rate": errors[m] / total[m], "top_paths": by_path[m].most_common(3)})
    return {"lines": n, "minutes": len(minutes), "total_errors": sum(counts), "spikes": spikes}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("logfile")
    ap.add_argument("--sigma", type=float, default=3.0)
    a = ap.parse_args(argv)
    with open(a.logfile, encoding="utf-8", errors="replace") as f:
        r = analyze(f, a.sigma)
    print(f"lines={r['lines']} minutes={r['minutes']} 5xx={r['total_errors']}")
    for s in r["spikes"]:
        print(f"SPIKE {s['minute']}  5xx={s['errors']}/{s['requests']} ({s['rate']:.0%})  top: {s['top_paths']}")
    return 2 if r["spikes"] else 0


if __name__ == "__main__":
    sys.exit(main())
