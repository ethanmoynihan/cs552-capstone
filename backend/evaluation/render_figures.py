"""
Render PNG figures from an accuracy results JSON for the final writeup.

Emits:
  - fig_category_bars.png — exact / math-eq / parses_ok grouped by category
  - fig_latency_hist.png — inference_ms histogram with 3s target line
  - fig_ned_box.png — normalized edit distance distribution by category
  - fig_bleu_vs_matheq.png — BLEU scatter colored by math-equivalent
  - representative_cases.md — markdown table of 5 hand-picked cases

Usage:
    uv run python render_figures.py [path/to/results.json]

If no path is given, picks the newest file matching results/accuracy-*.json.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use("Agg")  # headless — no display needed

EVAL_DIR = Path(__file__).resolve().parent
RESULTS_DIR = EVAL_DIR / "results"
FIGURES_DIR = RESULTS_DIR / "figures"

CATEGORY_ORDER = ["simple", "complex", "ambiguous", "edit"]


def main() -> None:
    source = _pick_source(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"reading {source.relative_to(EVAL_DIR)}")
    data = json.loads(source.read_text())
    results = data["results"]

    FIGURES_DIR.mkdir(exist_ok=True)

    _fig_category_bars(results)
    _fig_latency_hist(results)
    _fig_ned_box(results)
    _fig_bleu_vs_matheq(results)
    _write_representative_cases(results)

    print(f"\nwrote {len(list(FIGURES_DIR.glob('*.png')))} figures to {FIGURES_DIR.relative_to(EVAL_DIR)}")


def _pick_source(arg: str | None) -> Path:
    if arg:
        return Path(arg)
    candidates = sorted(RESULTS_DIR.glob("accuracy-*.json"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        sys.exit(f"No results/accuracy-*.json in {RESULTS_DIR}. Run evaluate_accuracy.py first.")
    return candidates[-1]


def _group_by_category(results: list[dict]) -> dict[str, list[dict]]:
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by_cat[r["category"]].append(r)
    return by_cat


def _fig_category_bars(results: list[dict]) -> None:
    by_cat = _group_by_category(results)
    cats = [c for c in CATEGORY_ORDER if c in by_cat]

    exact = [_rate(by_cat[c], lambda r: r["metrics"]["exact_match"]) for c in cats]
    math_eq = [_rate_nullable(by_cat[c], lambda r: r["metrics"]["math_equivalent"]) for c in cats]
    parses = [_rate(by_cat[c], lambda r: r["metrics"]["parses_ok"]) for c in cats]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    width = 0.26
    x = list(range(len(cats)))
    ax.bar([i - width for i in x], exact, width, label="Exact match")
    ax.bar(x, math_eq, width, label="Math equivalent")
    ax.bar([i + width for i in x], parses, width, label="Parses ok")

    ax.set_xticks(x)
    ax.set_xticklabels(cats)
    ax.set_ylabel("Rate")
    ax.set_ylim(0, 1.05)
    ax.set_title("Accuracy metrics by test category")
    ax.legend(loc="lower right")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_category_bars.png", dpi=160)
    plt.close(fig)


def _fig_latency_hist(results: list[dict]) -> None:
    ms = [r["inference_ms"] for r in results]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(ms, bins=20, color="#4a7", edgecolor="white")
    ax.axvline(3000, color="#b00", linestyle="--", linewidth=2, label="3s proposal target")
    ax.set_xlabel("Inference time (ms)")
    ax.set_ylabel("Cases")
    ax.set_title(f"LLM inference latency (n={len(ms)}, median {sorted(ms)[len(ms)//2]}ms)")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_latency_hist.png", dpi=160)
    plt.close(fig)


def _fig_ned_box(results: list[dict]) -> None:
    by_cat = _group_by_category(results)
    cats = [c for c in CATEGORY_ORDER if c in by_cat]
    data = [[r["metrics"]["normalized_edit_distance"] for r in by_cat[c]] for c in cats]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.boxplot(data, tick_labels=cats, showmeans=True)
    ax.set_ylabel("Normalized edit distance (lower is better)")
    ax.set_ylim(0, 1.0)
    ax.set_title("Edit-distance distribution by category")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_ned_box.png", dpi=160)
    plt.close(fig)


def _fig_bleu_vs_matheq(results: list[dict]) -> None:
    checkable = [r for r in results if r["metrics"]["math_equivalent"] is not None]
    if not checkable:
        return
    bleu = [r["metrics"]["bleu"] for r in checkable]
    eq = [1 if r["metrics"]["math_equivalent"] else 0 for r in checkable]
    colors = ["#2a8" if e else "#b00" for e in eq]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.scatter(bleu, eq, c=colors, s=60, alpha=0.7, edgecolor="white")
    ax.set_xlabel("BLEU score (0-100)")
    ax.set_ylabel("Math equivalent")
    ax.set_yticks([0, 1])
    ax.set_yticklabels(["No", "Yes"])
    ax.set_title("BLEU vs. mathematical equivalence")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_bleu_vs_matheq.png", dpi=160)
    plt.close(fig)


def _write_representative_cases(results: list[dict]) -> None:
    """Pick one case per interesting bucket, produce a markdown table."""

    def find(pred):
        for r in results:
            if pred(r):
                return r
        return None

    picks: list[tuple[str, dict | None]] = [
        ("Exact match", find(lambda r: r["metrics"]["exact_match"])),
        (
            "Math-equivalent but not exact",
            find(
                lambda r: not r["metrics"]["exact_match"]
                and r["metrics"]["math_equivalent"] is True
            ),
        ),
        (
            "Partial (parses, not equivalent)",
            find(
                lambda r: r["metrics"]["parses_ok"]
                and r["metrics"]["math_equivalent"] is False
            ),
        ),
        (
            "Unparseable reference (manual review)",
            find(lambda r: r["metrics"]["math_equivalent"] is None),
        ),
        ("Edit case", find(lambda r: r["category"] == "edit")),
    ]

    lines = [
        "# Representative cases",
        "",
        "| Bucket | Input | Expected | Actual | Exact | Math-eq | BLEU | ROUGE-L | ms |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for label, r in picks:
        if not r:
            continue
        m = r["metrics"]
        math_eq = {True: "✓", False: "✗", None: "—"}[m["math_equivalent"]]
        lines.append(
            f"| {label} | {r['text']} | `{r['expected']}` | `{r['actual']}` | "
            f"{'✓' if m['exact_match'] else '✗'} | {math_eq} | "
            f"{m['bleu']:.1f} | {m['rouge_l']:.2f} | {r['inference_ms']} |"
        )
    (FIGURES_DIR / "representative_cases.md").write_text("\n".join(lines) + "\n")


def _rate(items: list[dict], pred) -> float:
    if not items:
        return 0.0
    return sum(1 for r in items if pred(r)) / len(items)


def _rate_nullable(items: list[dict], pred) -> float:
    """Fraction of True among items where the metric is not None."""
    checked = [r for r in items if pred(r) is not None]
    if not checked:
        return 0.0
    return sum(1 for r in checked if pred(r)) / len(checked)


if __name__ == "__main__":
    main()
