"""
Core bill analysis engine.
Matches bill items to benchmarks, flags overcharges, and computes the Bill Health Score.
"""

import json
import re
from pathlib import Path
from typing import Optional

import config

# ─── Flag constants ───────────────────────────────────────────────────────────
FLAG_MAJOR_OVERCHARGE = "MAJOR OVERCHARGE"
FLAG_OVERCHARGED = "OVERCHARGED"
FLAG_SLIGHTLY_HIGH = "SLIGHTLY HIGH"
FLAG_FAIR = "FAIR"
FLAG_BELOW_BENCHMARK = "BELOW BENCHMARK"
FLAG_SUSPICIOUS = "SUSPICIOUS"
FLAG_UNKNOWN = "UNKNOWN"

# Variance thresholds
MAJOR_THRESHOLD = 50       # > 50% above benchmark → MAJOR OVERCHARGE
OVERCHARGE_THRESHOLD = 20  # > 20% above benchmark → OVERCHARGED
SLIGHTLY_HIGH_THRESHOLD = 5  # > 5% above benchmark → SLIGHTLY HIGH
BELOW_THRESHOLD = -20      # > 20% below benchmark → BELOW BENCHMARK (note it)


def _load_benchmarks() -> tuple[list[dict], list[dict]]:
    """Load benchmark data from rates.json. Returns (benchmarks, suspicious_patterns)."""
    path = config.BENCHMARKS_FILE
    if not path.exists():
        return [], []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("benchmarks", []), data.get("suspicious_patterns", [])


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation/extra spaces for matching."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _token_similarity(a: str, b: str) -> float:
    """Jaccard similarity on word tokens."""
    a_tokens = set(_normalize(a).split())
    b_tokens = set(_normalize(b).split())
    if not a_tokens or not b_tokens:
        return 0.0
    intersection = a_tokens & b_tokens
    union = a_tokens | b_tokens
    return len(intersection) / len(union)


def _find_benchmark(item_name: str, benchmarks: list[dict]) -> Optional[dict]:
    """
    Find the best-matching benchmark for an item name.
    Returns the benchmark dict or None.
    """
    name_norm = _normalize(item_name)

    best_match = None
    best_score = 0.0

    for bench in benchmarks:
        # Check primary name
        score = _token_similarity(item_name, bench["name"])

        # Check all aliases
        for alias in bench.get("aliases", []):
            s = _token_similarity(item_name, alias)
            if s > score:
                score = s

        # Exact substring match bonus
        bench_norm = _normalize(bench["name"])
        if bench_norm in name_norm or name_norm in bench_norm:
            score = max(score, 0.75)

        if score > best_score:
            best_score = score
            best_match = bench

    # Require at least 0.40 similarity to accept a match
    return best_match if best_score >= 0.40 else None


def _check_suspicious_patterns(item_name: str, suspicious_patterns: list[dict]) -> Optional[str]:
    """Return the reason string if the item matches a suspicious pattern, else None."""
    name_norm = _normalize(item_name)
    for pattern in suspicious_patterns:
        for alias in pattern.get("aliases", []):
            if _normalize(alias) in name_norm or name_norm in _normalize(alias):
                return pattern.get("reason", "Potentially incorrect charge")
    return None


def _determine_flag(variance_pct: float) -> str:
    if variance_pct > MAJOR_THRESHOLD:
        return FLAG_MAJOR_OVERCHARGE
    elif variance_pct > OVERCHARGE_THRESHOLD:
        return FLAG_OVERCHARGED
    elif variance_pct > SLIGHTLY_HIGH_THRESHOLD:
        return FLAG_SLIGHTLY_HIGH
    elif variance_pct >= BELOW_THRESHOLD:
        return FLAG_FAIR
    else:
        return FLAG_BELOW_BENCHMARK


def analyze_bill(bill_items: list[dict]) -> tuple[list[dict], dict]:
    """
    Main analysis entry point.

    Parameters
    ----------
    bill_items : list of dicts, each with keys:
        name, category, quantity, unit, unit_rate, amount

    Returns
    -------
    (results, summary)
        results : list of enriched item dicts
        summary : dict with totals and health score
    """
    benchmarks, suspicious_patterns = _load_benchmarks()

    results = []
    total_billed = 0.0
    total_fair = 0.0
    items_overcharged = 0
    items_suspicious = 0
    items_fair = 0
    items_unknown = 0

    for item in bill_items:
        result = _analyze_item(item, benchmarks, suspicious_patterns)
        results.append(result)

        amount = result.get("amount", 0.0)
        fair = result.get("fair_amount", amount)
        total_billed += amount
        total_fair += fair

        flag = result.get("flag", FLAG_UNKNOWN)
        if flag in (FLAG_MAJOR_OVERCHARGE, FLAG_OVERCHARGED, FLAG_SLIGHTLY_HIGH):
            items_overcharged += 1
        elif flag == FLAG_SUSPICIOUS:
            items_suspicious += 1
        elif flag == FLAG_FAIR:
            items_fair += 1
        elif flag == FLAG_UNKNOWN:
            items_unknown += 1

    potential_savings = max(0.0, total_billed - total_fair)

    # Health score: ratio of fair total to billed total, scaled 0-100
    if total_billed > 0:
        base_score = (total_fair / total_billed) * 100
    else:
        base_score = 100.0

    # Penalty for suspicious items (5 points each, capped at 20)
    suspicious_penalty = min(20, items_suspicious * 5)
    health_score = max(0, min(100, round(base_score - suspicious_penalty)))

    summary = {
        "total_billed": total_billed,
        "total_fair": total_fair,
        "potential_savings": potential_savings,
        "health_score": health_score,
        "items_overcharged": items_overcharged,
        "items_suspicious": items_suspicious,
        "items_fair": items_fair,
        "items_unknown": items_unknown,
        "total_items": len(results),
        "overcharge_pct": round((potential_savings / total_billed * 100), 1) if total_billed > 0 else 0,
    }

    return results, summary


def _analyze_item(
    item: dict,
    benchmarks: list[dict],
    suspicious_patterns: list[dict],
) -> dict:
    """Analyze a single bill item against benchmarks."""
    name = item.get("name", "Unknown Item")
    category = item.get("category", "Other")
    quantity = float(item.get("quantity", 1))
    unit_rate = float(item.get("unit_rate", 0))
    amount = float(item.get("amount", 0))

    # If unit_rate is not provided but amount is, derive unit rate
    if unit_rate == 0 and amount > 0 and quantity > 0:
        unit_rate = amount / quantity

    # Recalculate amount for consistency
    if amount == 0 and unit_rate > 0:
        amount = unit_rate * quantity

    result = {
        "name": name,
        "category": category,
        "quantity": quantity,
        "unit": item.get("unit", "each"),
        "unit_rate": unit_rate,
        "amount": amount,
        "benchmark_name": None,
        "benchmark_rate": None,
        "benchmark_min": None,
        "benchmark_max": None,
        "fair_amount": amount,  # default: assume billed is fair
        "overcharge_amount": 0.0,
        "variance_pct": None,
        "flag": FLAG_UNKNOWN,
        "flag_reason": "No matching benchmark found for this item.",
        "notes": "",
    }

    # 1. Check suspicious patterns first (e.g., oxygen charges already in ICU)
    suspicious_reason = _check_suspicious_patterns(name, suspicious_patterns)
    if suspicious_reason:
        result["flag"] = FLAG_SUSPICIOUS
        result["flag_reason"] = suspicious_reason
        result["fair_amount"] = 0.0  # treat as potentially duplicate
        result["overcharge_amount"] = amount
        return result

    # 2. Find best benchmark match
    benchmark = _find_benchmark(name, benchmarks)

    if benchmark is None:
        # Unknown item — flag it if the amount is above threshold
        if amount >= config.UNKNOWN_ITEM_FLAG_THRESHOLD:
            result["flag"] = FLAG_UNKNOWN
            result["flag_reason"] = (
                f"No benchmark rate found for '{name}'. "
                "Verify this charge with the hospital."
            )
        else:
            result["flag"] = FLAG_FAIR
            result["flag_reason"] = "Low-value item; no benchmark check performed."
        return result

    bench_rate = float(benchmark["benchmark_rate"])
    bench_min = float(benchmark.get("min_rate", bench_rate * 0.8))
    bench_max = float(benchmark.get("max_rate", bench_rate * 1.2))
    flag_threshold = float(benchmark.get("flag_threshold_pct", 20))

    # Calculate fair amount using benchmark rate × quantity
    fair_unit_rate = bench_rate
    fair_amount = bench_rate * quantity

    # Variance based on unit_rate vs benchmark_rate
    if bench_rate > 0:
        variance_pct = ((unit_rate - bench_rate) / bench_rate) * 100
    else:
        variance_pct = 0.0

    # Use the item's own flag threshold if higher than default
    effective_threshold = max(flag_threshold, OVERCHARGE_THRESHOLD)

    # Determine flag with item-specific threshold
    if variance_pct > max(MAJOR_THRESHOLD, flag_threshold * 2):
        flag = FLAG_MAJOR_OVERCHARGE
    elif variance_pct > effective_threshold:
        flag = FLAG_OVERCHARGED
    elif variance_pct > SLIGHTLY_HIGH_THRESHOLD:
        flag = FLAG_SLIGHTLY_HIGH
    elif variance_pct >= BELOW_THRESHOLD:
        flag = FLAG_FAIR
    else:
        flag = FLAG_BELOW_BENCHMARK

    # Build human-readable reason
    if flag in (FLAG_MAJOR_OVERCHARGE, FLAG_OVERCHARGED):
        flag_reason = (
            f"Billed at ₹{unit_rate:,.0f}/{item.get('unit','unit')}. "
            f"Benchmark rate: ₹{bench_min:,.0f}–₹{bench_max:,.0f}. "
            f"This is {abs(variance_pct):.0f}% above the standard rate."
        )
    elif flag == FLAG_SLIGHTLY_HIGH:
        flag_reason = (
            f"Slightly above benchmark (₹{bench_rate:,.0f}). "
            f"Difference: {variance_pct:.0f}%. May be acceptable."
        )
    elif flag == FLAG_FAIR:
        flag_reason = f"Rate is within the benchmark range (₹{bench_min:,.0f}–₹{bench_max:,.0f})."
    elif flag == FLAG_BELOW_BENCHMARK:
        flag_reason = (
            f"Rate is below benchmark. This is good for the patient but worth verifying."
        )
    else:
        flag_reason = ""

    overcharge_amount = max(0.0, amount - fair_amount)

    result.update(
        {
            "benchmark_name": benchmark["name"],
            "benchmark_rate": bench_rate,
            "benchmark_min": bench_min,
            "benchmark_max": bench_max,
            "fair_amount": round(fair_amount, 2),
            "overcharge_amount": round(overcharge_amount, 2),
            "variance_pct": round(variance_pct, 1),
            "flag": flag,
            "flag_reason": flag_reason,
            "notes": benchmark.get("notes", ""),
        }
    )

    return result


def get_category_summary(results: list[dict]) -> list[dict]:
    """Aggregate overcharges and amounts by category."""
    from collections import defaultdict

    cats: dict[str, dict] = defaultdict(
        lambda: {"billed": 0.0, "fair": 0.0, "overcharge": 0.0, "items": 0}
    )
    for r in results:
        cat = r.get("category", "Other")
        cats[cat]["billed"] += r.get("amount", 0)
        cats[cat]["fair"] += r.get("fair_amount", r.get("amount", 0))
        cats[cat]["overcharge"] += r.get("overcharge_amount", 0)
        cats[cat]["items"] += 1

    return [
        {
            "category": cat,
            "billed": round(v["billed"], 2),
            "fair": round(v["fair"], 2),
            "overcharge": round(v["overcharge"], 2),
            "items": v["items"],
        }
        for cat, v in sorted(cats.items(), key=lambda x: -x[1]["overcharge"])
    ]
