"""Deterministic scoring step of the triage flow.

The AI only extracts facts (see PROMPTS.md). Everything here is plain rules:
gate -> score -> rank. Same input + same criteria version = same output.

Usage:  python3 prototype/score.py
"""
import json
import pathlib

HERE = pathlib.Path(__file__).parent


def load(name):
    return json.loads((HERE / name).read_text())


def gate(p):
    """Mandatory pass/fail. Returns 'pass', 'fail' or 'unclear'."""
    if p["licence"] in ("not_held", "deferred") or p["wsib"] == "not_held" or p["insurance_5m"] == "not_held":
        return "fail"
    ok = p["licence"] == "held" and p["wsib"] == "confirmed" and p["insurance_5m"] == "confirmed"
    return "pass" if ok else "unclear"


def experience(p, c):
    n = p["qualifying_installs"] or 0
    for t in c["params"]["experience_tiers"]:
        if n >= t["min"]:
            return c["weights"]["experience"] * t["pct"]
    return 0.0


def price(p, c, lowest):
    v = p["price_cad"]
    if v is None or v > c["budget_ceiling_cad"]:
        return 0.0
    return c["weights"]["price"] * lowest / v


def timeline(p, c):
    w, best, cap = p["weeks"], c["params"]["timeline_full_marks_weeks"], c["max_weeks"]
    if w is None or w > cap:
        return 0.0  # not stated or too slow: no credit
    if w <= best:
        return float(c["weights"]["timeline"])
    return c["weights"]["timeline"] * (cap - w) / (cap - best)


def warranty(p, c):
    half = c["weights"]["warranty"] / 2
    a = min((p["panel_years"] or 0) / c["params"]["warranty_full_panel_years"], 1)
    b = min((p["workmanship_years"] or 0) / c["params"]["warranty_full_workmanship_years"], 1)
    return half * a + half * b


def team(p, c):
    items = c["params"]["team_items"]
    hit = sum(1 for i in items if p["team"].get(i))
    return c["weights"]["team"] * hit / len(items)


def main():
    c, data = load("criteria.json"), load("extracted_sample.json")
    data = {k: v for k, v in data.items() if not k.startswith("_")}

    gates = {k: gate(v) for k, v in data.items()}
    flagged = {k for k, v in data.items() if v["suspicious_instructions"]}
    # Price baseline: only clean, eligible bidders, so a flagged one cannot shift others' scores.
    base = [v["price_cad"] for k, v in data.items() if gates[k] == "pass" and k not in flagged and v["price_cad"]]
    lowest = min(base)

    rows = {}
    for k, p in data.items():
        if gates[k] == "fail":
            rows[k] = {"status": "ineligible", "score": None}
            continue
        parts = {
            "experience": experience(p, c), "price": price(p, c, lowest),
            "timeline": timeline(p, c), "warranty": warranty(p, c), "team": team(p, c),
        }
        total = round(sum(parts.values()), 1)
        status = "flagged" if (k in flagged or gates[k] == "unclear") else "ranked"
        rows[k] = {"status": status, "score": total, "shadow": status == "flagged",
                   "parts": {n: round(v, 2) for n, v in parts.items()}}

    ranked = sorted((k for k, r in rows.items() if r["status"] == "ranked"), key=lambda k: -rows[k]["score"])
    for i, k in enumerate(ranked, 1):
        rows[k]["rank"] = i

    print(f"criteria v{c['version']} | lowest eligible price = {lowest}")
    for k in sorted(rows):
        r = rows[k]
        print(k, r["status"], "rank", r.get("rank"), "score", r["score"], r.get("parts", ""))
        if r.get("shadow"):
            print("   ^ shadow score only, not ranked: needs human review")


if __name__ == "__main__":
    main()
