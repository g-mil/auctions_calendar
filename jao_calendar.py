"""JAO monthly auction calendar.

python jao_calendar.py            fetch this month's and all published future auctions of the corridors in
                                  corridors.txt, merge them into data/auctions.json, write index.html
python jao_calendar.py --render   only rewrite index.html from data/auctions.json

JAO API key: environment variable JAO_API_KEY, or a line JAO_API_KEY=... in .env next to this file.
Standard library only.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "auctions.json"
BASE = "https://api.jao.eu/OWSMP/getauctions"
AHEAD = 12          # months after the current one to try; stops at the first month JAO has nothing for
GATES = ["ltResaleGateOpening", "ltResaleGateClosure", "bidGateOpening", "bidGateClosure",
         "provisionalAuctionresult", "disputeSubmissionGateOpening", "disputeSubmissionGateClosure"]


def api_key() -> str:
    key = os.environ.get("JAO_API_KEY")
    env = HERE / ".env"
    if not key and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("JAO_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"\'')
    if not key:
        sys.exit("JAO_API_KEY not set (environment or .env)")
    return key


def monthly_auctions(corridor: str, month: date, key: str) -> list[dict]:
    """JAO's monthly auctions of `corridor` delivering in `month`; [] when JAO has none yet."""
    last = month.replace(day=monthrange(month.year, month.month)[1])
    q = urllib.parse.urlencode({"corridor": corridor, "horizon": "Monthly", "shadow": 0,
                                "fromdate": (month - timedelta(days=1)).isoformat(), "todate": last.isoformat()})
    for attempt in range(4):
        try:
            req = urllib.request.Request(f"{BASE}?{q}", headers={"AUTH_API_KEY": key})
            with urllib.request.urlopen(req, timeout=60) as r:
                time.sleep(0.5)
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(5 * (attempt + 1))
                continue
            if e.code == 404 or (e.code == 400 and b"no data found" in e.read().lower()):
                return []
            raise
    raise RuntimeError(f"JAO rate limit: {corridor} {month:%Y-%m}")


def record(a: dict, corridor: str) -> dict:
    # marketPeriodStart is local midnight in UTC (e.g. 2026-10-31T23:00Z for November)
    start = datetime.fromisoformat(a["marketPeriodStart"].replace("Z", "+00:00")) + timedelta(hours=12)
    return {"identification": a["identification"], "corridor": corridor,
            "delivery_month": f"{start:%Y-%m}", "cancelled": bool(a.get("cancelled")),
            **{g: a.get(g) for g in GATES}}


def add_months(d: date, n: int) -> date:
    y, m = divmod(d.month - 1 + n, 12)
    return date(d.year + y, m + 1, 1)


def update(store: dict[str, dict]) -> None:
    key = api_key()
    corridors = [c.strip() for c in (HERE / "corridors.txt").read_text().splitlines() if c.strip()]
    this = date.today().replace(day=1)
    for corridor in corridors:
        for i in range(AHEAD + 1):
            m = add_months(this, i)
            got = [record(a, corridor) for a in monthly_auctions(corridor, m, key)]
            got = [r for r in got if r["delivery_month"] == f"{m:%Y-%m}"]
            for r in got:
                store[r["identification"]] = r
            print(f"{corridor} {m:%Y-%m}: {len(got)} auction(s)")
            if not got and i > 0:
                break


def main() -> None:
    store = {r["identification"]: r for r in json.loads(DATA.read_text())} if DATA.exists() else {}
    if "--render" not in sys.argv:
        update(store)
    rows = sorted(store.values(), key=lambda r: (r["delivery_month"], r["corridor"], r["identification"]))
    DATA.parent.mkdir(exist_ok=True)
    DATA.write_text("[\n" + ",\n".join(json.dumps(r) for r in rows) + "\n]\n")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    page = (HERE / "template.html").read_text(encoding="utf-8")
    page = page.replace("__DATA__", json.dumps(rows).replace("</", "<\\/")).replace("__UPDATED__", stamp)
    (HERE / "index.html").write_text(page, encoding="utf-8")
    print(f"{len(rows)} auctions -> index.html")


if __name__ == "__main__":
    main()
