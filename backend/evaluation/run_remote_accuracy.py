"""
Remote accuracy evaluator — hits the deployed backend's /evaluation/* endpoints
and produces the same JSON shape as evaluate_accuracy.py. Use this for writeup
numbers so the report reflects deployed performance (CUDA/T4 on HF Space),
not local M-series.

Usage:
    uv run python run_remote_accuracy.py \
        --base-url https://ethanmoynihan-cs552-final.hf.space
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

import httpx

EVAL_DIR = Path(__file__).resolve().parent


def run(base_url: str, timeout: float) -> None:
    base_url = base_url.rstrip("/")
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        cases = client.get("/evaluation/test-cases").raise_for_status().json()["cases"]
        print(f"{len(cases)} cases from {base_url}")

        results: list[dict] = []
        for case in cases:
            resp = client.post("/evaluation/run-case", json={"id": case["id"]})
            if resp.status_code != 200:
                print(f"[!] {case['id']} → HTTP {resp.status_code}: {resp.text}", file=sys.stderr)
                sys.exit(1)
            r = resp.json()
            m = r["metrics"]
            status = "✓" if m["exact_match"] else "~" if m["math_equivalent"] else "✗"
            print(
                f"[{status}] {r['id']:<14} ned={m['normalized_edit_distance']:.2f} "
                f"bleu={m['bleu']:.1f} rouge={m['rouge_l']:.2f} "
                f"math_eq={m['math_equivalent']} ({r['inference_ms']}ms)"
            )
            # Reshape to match evaluate_accuracy.py's output schema.
            results.append(
                {
                    "id": r["id"],
                    "category": r["category"],
                    "text": r["text"],
                    "expected": r["expected"],
                    "actual": r["actual"],
                    "tokens_used": r["tokens_used"],
                    "inference_ms": r["inference_ms"],
                    "wall_ms": r["inference_ms"],  # remote timing is server-side only
                    "metrics": m,
                }
            )

    summary = _summarize(results)
    _write_outputs(results, summary, base_url)
    _print_summary(summary)


def _summarize(results: list[dict]) -> dict:
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r)

    def stats(items: list[dict]) -> dict:
        n = len(items)
        exact = sum(1 for r in items if r["metrics"]["exact_match"])
        parses = sum(1 for r in items if r["metrics"]["parses_ok"])
        math_eq_true = sum(1 for r in items if r["metrics"]["math_equivalent"] is True)
        math_eq_checked = sum(1 for r in items if r["metrics"]["math_equivalent"] is not None)
        neds = [r["metrics"]["normalized_edit_distance"] for r in items]
        bleus = [r["metrics"]["bleu"] for r in items]
        rouges = [r["metrics"]["rouge_l"] for r in items]
        inf_ms = [r["inference_ms"] for r in items]
        return {
            "n": n,
            "exact_match_rate": exact / n if n else 0.0,
            "parses_ok_rate": parses / n if n else 0.0,
            "math_equivalent_rate": (math_eq_true / math_eq_checked) if math_eq_checked else None,
            "math_equivalent_checked": math_eq_checked,
            "mean_normalized_edit_distance": statistics.mean(neds) if neds else 0.0,
            "mean_bleu": statistics.mean(bleus) if bleus else 0.0,
            "mean_rouge_l": statistics.mean(rouges) if rouges else 0.0,
            "median_inference_ms": statistics.median(inf_ms) if inf_ms else 0,
        }

    return {"overall": stats(results), "by_category": {k: stats(v) for k, v in by_cat.items()}}


def _write_outputs(results: list[dict], summary: dict, base_url: str) -> None:
    results_dir = EVAL_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    path = results_dir / f"accuracy-remote-{stamp}.json"
    path.write_text(
        json.dumps({"summary": summary, "results": results, "source": base_url}, indent=2)
    )
    print(f"\nwrote {path.relative_to(EVAL_DIR)}")


def _print_summary(summary: dict) -> None:
    o = summary["overall"]
    print("\n=== Overall (deployed) ===")
    print(f"  exact match:       {o['exact_match_rate']:.1%}")
    if o["math_equivalent_rate"] is not None:
        print(
            f"  math equivalent:   {o['math_equivalent_rate']:.1%} "
            f"({o['math_equivalent_checked']}/{o['n']} checkable)"
        )
    print(f"  parses ok:         {o['parses_ok_rate']:.1%}")
    print(f"  mean BLEU:         {o['mean_bleu']:.1f}")
    print(f"  mean ROUGE-L:      {o['mean_rouge_l']:.2f}")
    print(f"  mean edit dist:    {o['mean_normalized_edit_distance']:.2f}")
    print(f"  median inference:  {o['median_inference_ms']} ms")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-url",
        required=True,
        help="Deployed backend base URL, e.g. https://ethanmoynihan-cs552-final.hf.space",
    )
    parser.add_argument("--timeout", type=float, default=120.0, help="Per-request timeout seconds")
    args = parser.parse_args()
    run(args.base_url, args.timeout)


if __name__ == "__main__":
    main()
