"""
Phase 4 accuracy evaluator.

Runs every case in test_cases.json through the real LaTeX generator (imported
directly from the backend — no FastAPI hop), computes metrics.py results,
writes a JSON dump plus a markdown summary to results/.

Usage:
    uv run python evaluate_accuracy.py
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
# Make the backend importable as a top-level package (matches how it runs under uvicorn).
sys.path.insert(0, str(EVAL_DIR.parent / "backend"))

from services.llama_service import get_generator  # noqa: E402

from metrics import evaluate  # noqa: E402


def run() -> None:
    cases = json.loads((EVAL_DIR / "test_cases.json").read_text())["cases"]
    generator = get_generator()

    results = []
    for case in cases:
        start = time.perf_counter()
        if case["category"] == "edit":
            latex, tokens, inference_ms = generator.edit(case["current_latex"], case["text"])
        else:
            latex, tokens, inference_ms = generator.generate(case["text"])
        wall_ms = int((time.perf_counter() - start) * 1000)

        metrics = evaluate(latex, case["expected_latex"])
        results.append(
            {
                "id": case["id"],
                "category": case["category"],
                "text": case["text"],
                "expected": case["expected_latex"],
                "actual": latex,
                "tokens_used": tokens,
                "inference_ms": inference_ms,
                "wall_ms": wall_ms,
                "metrics": asdict(metrics),
            }
        )
        status = "✓" if metrics.exact_match else "~" if metrics.math_equivalent else "✗"
        print(
            f"[{status}] {case['id']:<14} ned={metrics.normalized_edit_distance:.2f} "
            f"parses={metrics.parses_ok} math_eq={metrics.math_equivalent} "
            f"({inference_ms}ms, {tokens} tok)"
        )

    summary = _summarize(results)
    _write_outputs(results, summary)
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


def _write_outputs(results: list[dict], summary: dict) -> None:
    results_dir = EVAL_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    json_path = results_dir / f"accuracy-{stamp}.json"
    md_path = results_dir / f"accuracy-{stamp}.md"
    json_path.write_text(json.dumps({"summary": summary, "results": results}, indent=2))
    md_path.write_text(_render_markdown(summary, results))
    print(f"\nwrote {json_path.relative_to(EVAL_DIR)}")
    print(f"wrote {md_path.relative_to(EVAL_DIR)}")


def _render_markdown(summary: dict, results: list[dict]) -> str:
    lines = ["# Accuracy evaluation", "", "## Overall", ""]
    lines.append(_stats_table(summary["overall"]))
    lines.append("")
    lines.append("## By category")
    lines.append("")
    for cat, s in summary["by_category"].items():
        lines.append(f"### {cat} (n={s['n']})")
        lines.append("")
        lines.append(_stats_table(s))
        lines.append("")
    lines.append("## Per-case")
    lines.append("")
    lines.append("| id | cat | exact | math_eq | parses | ned | ms | expected | actual |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in results:
        m = r["metrics"]
        lines.append(
            f"| {r['id']} | {r['category']} | {'✓' if m['exact_match'] else ''} | "
            f"{'' if m['math_equivalent'] is None else ('✓' if m['math_equivalent'] else '✗')} | "
            f"{'✓' if m['parses_ok'] else '✗'} | {m['normalized_edit_distance']:.2f} | "
            f"{r['inference_ms']} | `{r['expected']}` | `{r['actual']}` |"
        )
    return "\n".join(lines) + "\n"


def _stats_table(s: dict) -> str:
    math_rate = s["math_equivalent_rate"]
    math_str = (
        f"{math_rate:.1%} ({s['math_equivalent_checked']} checkable)"
        if math_rate is not None
        else "n/a"
    )
    return (
        "| metric | value |\n"
        "|---|---|\n"
        f"| n | {s['n']} |\n"
        f"| exact match | {s['exact_match_rate']:.1%} |\n"
        f"| math equivalent | {math_str} |\n"
        f"| parses ok | {s['parses_ok_rate']:.1%} |\n"
        f"| mean BLEU | {s['mean_bleu']:.1f} |\n"
        f"| mean ROUGE-L | {s['mean_rouge_l']:.2f} |\n"
        f"| mean normalized edit distance | {s['mean_normalized_edit_distance']:.2f} |\n"
        f"| median inference ms | {s['median_inference_ms']} |"
    )


def _print_summary(summary: dict) -> None:
    o = summary["overall"]
    print("\n=== Overall ===")
    print(f"  exact match:       {o['exact_match_rate']:.1%}")
    if o["math_equivalent_rate"] is not None:
        print(
            f"  math equivalent:   {o['math_equivalent_rate']:.1%} "
            f"({o['math_equivalent_checked']}/{o['n']} checkable)"
        )
    print(f"  parses ok:         {o['parses_ok_rate']:.1%}")
    print(f"  mean edit dist:    {o['mean_normalized_edit_distance']:.2f}")
    print(f"  median inference:  {o['median_inference_ms']} ms")


if __name__ == "__main__":
    run()
