"""Прогон эталонных карт через живой API и сверка. Запуск: python3 tests/run_reference.py"""

from __future__ import annotations

import json
import sys
import urllib.request

from reference_charts import CHARTS

BASE = "http://127.0.0.1:8130"


def post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main():
    print(f"{'ID':<3}{'Сценарий':<52}{'TZ наш':>7}{'TZ эт.':>7}{'Δ':>5}  Луна/лагна")
    print("-" * 120)
    fails = 0
    details = []
    for c in CHARTS:
        try:
            res = post("/v1/natal", c["input"])
        except Exception as e:
            print(f"{c['id']:<3}{c['label'][:50]:<52} ОШИБКА: {e}")
            fails += 1
            continue

        exp = c["expected_tz_offset"]
        if res.get("time_unknown"):
            vars_ = res.get("variants", [])
            off = vars_[0]["utc_offset_hours"] if vars_ else None
            moon = f"{len(vars_)} вар.: " + "; ".join(
                f"{v['interval_local']} {v['moon_nakshatra']}/{v['moon_rashi']}" for v in vars_)
            lagna_s = "—(время неизв.)"
        else:
            off = res.get("utc_offset_hours")
            moon = next(g for g in res["grahas_d1"] if g["graha"] == "Moon")
            moon = f"Луна {moon['rashi']} {moon['nakshatra']} п.{moon['pada']}"
            lg = res.get("lagna") or {}
            lagna_s = f"Лагна {lg.get('rashi')} {lg.get('longitude_dms','')}"

        if exp is None:
            delta = "n/a"
            ok = True
        else:
            delta = f"{(off - exp):+.1f}" if off is not None else "?"
            ok = off is not None and abs(off - exp) < 0.01
        if not ok:
            fails += 1
        mark = "" if ok else "  ❌"
        print(f"{c['id']:<3}{c['label'][:50]:<52}{str(off):>7}{str(exp):>7}{delta:>5}  {moon} | {lagna_s}{mark}")
        details.append({"id": c["id"], "our_offset": off, "expected": exp,
                        "utc": res.get("utc"), "lagna": (res.get("lagna") or {}).get("rashi") if not res.get("time_unknown") else None})

    print("-" * 120)
    print(f"ИТОГО: {len(CHARTS)-fails}/{len(CHARTS)} совпало по часовому поясу; провалов: {fails}")
    with open("/tmp/ref_details.json", "w") as f:
        json.dump(details, f, ensure_ascii=False, indent=2)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
