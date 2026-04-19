"""
Phase 4 latency evaluator.

Per PROPOSAL.md §"Model Evaluation Criteria — Latency":
  "The end to end latency from speech spoken to the rendered equation.
   Setting a target of less than 3 seconds of total latency."

Reads any audio file in audio_fixtures/ (webm, wav, mp3, m4a), runs it through
Whisper + LLaMA end-to-end, and logs per-stage timings. Renders a markdown table
flagging cases that exceed the 3s target.

Usage:
    uv run python evaluate_latency.py

Requires:
  - ffmpeg on PATH (Whisper shells out to it for audio decode)
  - At least one audio fixture in audio_fixtures/
"""

from __future__ import annotations

import json
import resource
import statistics
import sys
import time
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL_DIR.parent))

from services.llama_service import get_generator  # noqa: E402
from services.whisper_service import get_transcriber  # noqa: E402

AUDIO_DIR = EVAL_DIR / "audio_fixtures"
TARGET_MS = 3000


def run() -> None:
    fixtures = sorted(
        p for p in AUDIO_DIR.iterdir() if p.suffix.lower() in {".webm", ".wav", ".mp3", ".m4a", ".ogg"}
    )
    if not fixtures:
        print(f"No audio fixtures in {AUDIO_DIR}. Record some and re-run.")
        return

    transcriber = get_transcriber()
    generator = get_generator()

    rss_start_kb = _rss_kb()
    results = []
    for path in fixtures:
        audio_bytes = path.read_bytes()
        asr_start = time.perf_counter()
        transcript, asr_ms = transcriber.transcribe(audio_bytes, path.name)
        asr_wall_ms = int((time.perf_counter() - asr_start) * 1000)

        llm_start = time.perf_counter()
        latex, tokens, llm_ms = generator.generate(transcript)
        llm_wall_ms = int((time.perf_counter() - llm_start) * 1000)

        total_ms = asr_wall_ms + llm_wall_ms
        tok_per_s = (tokens / (llm_ms / 1000)) if llm_ms > 0 else 0.0
        exceeded = total_ms > TARGET_MS

        results.append(
            {
                "fixture": path.name,
                "transcript": transcript,
                "latex": latex,
                "asr_ms": asr_wall_ms,
                "llm_ms": llm_wall_ms,
                "total_ms": total_ms,
                "tokens_used": tokens,
                "tokens_per_second": round(tok_per_s, 2),
                "exceeded_target": exceeded,
            }
        )
        flag = " ⚠ OVER 3s TARGET" if exceeded else ""
        print(
            f"{path.name}: asr={asr_wall_ms}ms llm={llm_wall_ms}ms "
            f"total={total_ms}ms ({tok_per_s:.1f} tok/s){flag}"
        )

    rss_peak_kb = _rss_kb()
    summary = _summarize(results, rss_start_kb, rss_peak_kb)
    _write_outputs(results, summary)
    _print_summary(summary)


def _rss_kb() -> int:
    """Resident set size in KB. Darwin reports bytes; Linux reports KB."""
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return rss // 1024 if sys.platform == "darwin" else rss


def _summarize(results: list[dict], rss_start_kb: int, rss_peak_kb: int) -> dict:
    totals = [r["total_ms"] for r in results]
    asrs = [r["asr_ms"] for r in results]
    llms = [r["llm_ms"] for r in results]
    tok_ps = [r["tokens_per_second"] for r in results]
    return {
        "n": len(results),
        "target_ms": TARGET_MS,
        "exceeded_count": sum(1 for r in results if r["exceeded_target"]),
        "median_asr_ms": int(statistics.median(asrs)),
        "median_llm_ms": int(statistics.median(llms)),
        "median_total_ms": int(statistics.median(totals)),
        "p95_total_ms": int(_percentile(totals, 95)),
        "median_tokens_per_second": round(statistics.median(tok_ps), 2),
        "rss_start_mb": round(rss_start_kb / 1024, 1),
        "rss_peak_mb": round(rss_peak_kb / 1024, 1),
    }


def _percentile(values: list[float], pct: int) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * pct / 100
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def _write_outputs(results: list[dict], summary: dict) -> None:
    results_dir = EVAL_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    json_path = results_dir / f"latency-{stamp}.json"
    md_path = results_dir / f"latency-{stamp}.md"
    json_path.write_text(json.dumps({"summary": summary, "results": results}, indent=2))
    md_path.write_text(_render_markdown(summary, results))
    print(f"\nwrote {json_path.relative_to(EVAL_DIR)}")
    print(f"wrote {md_path.relative_to(EVAL_DIR)}")


def _render_markdown(summary: dict, results: list[dict]) -> str:
    lines = [
        "# Latency evaluation",
        "",
        f"Target: end-to-end under **{summary['target_ms']}ms** (PROPOSAL.md).",
        "",
        "## Summary",
        "",
        "| metric | value |",
        "|---|---|",
        f"| fixtures | {summary['n']} |",
        f"| exceeded target | {summary['exceeded_count']} |",
        f"| median ASR ms | {summary['median_asr_ms']} |",
        f"| median LLM ms | {summary['median_llm_ms']} |",
        f"| median total ms | {summary['median_total_ms']} |",
        f"| p95 total ms | {summary['p95_total_ms']} |",
        f"| median tokens/sec | {summary['median_tokens_per_second']} |",
        f"| RSS start / peak (MB) | {summary['rss_start_mb']} / {summary['rss_peak_mb']} |",
        "",
        "## Per-fixture",
        "",
        "| fixture | asr ms | llm ms | total ms | tok/s | transcript | latex |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        lines.append(
            f"| {r['fixture']} | {r['asr_ms']} | {r['llm_ms']} | {r['total_ms']} | "
            f"{r['tokens_per_second']} | {r['transcript']} | `{r['latex']}` |"
        )
    return "\n".join(lines) + "\n"


def _print_summary(summary: dict) -> None:
    print("\n=== Overall ===")
    print(f"  median total:    {summary['median_total_ms']}ms (target {summary['target_ms']}ms)")
    print(f"  p95 total:       {summary['p95_total_ms']}ms")
    print(f"  exceeded target: {summary['exceeded_count']}/{summary['n']}")
    print(f"  tokens/sec:      {summary['median_tokens_per_second']}")
    print(f"  RSS peak:        {summary['rss_peak_mb']} MB")


if __name__ == "__main__":
    run()
