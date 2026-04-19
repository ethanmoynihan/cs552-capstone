"""
Phase 4 concurrent-request evaluator.

Per PROPOSAL.md §"Scalability and Robustness":
  "The model will be tested for concurrent requests."

Fires N parallel /generate-latex requests at a running backend and reports
p50/p95/p99 latency + error rate. Unlike the accuracy/latency scripts this
hits the FastAPI server (because concurrency is an I/O-path concern, not a
model-call concern).

Usage:
    # with backend running on :8000
    uv run python evaluate_concurrent.py --concurrency 8 --total 32
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path

import httpx

EVAL_DIR = Path(__file__).resolve().parent
DEFAULT_BASE = "http://localhost:8000"


async def _one_request(client: httpx.AsyncClient, text: str) -> tuple[int, int, bool]:
    start = time.perf_counter()
    try:
        resp = await client.post("/generate-latex", json={"text": text}, timeout=300.0)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return elapsed_ms, resp.status_code, resp.status_code == 200
    except Exception:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return elapsed_ms, 0, False


async def _worker(
    client: httpx.AsyncClient, queue: asyncio.Queue, results: list[tuple[int, int, bool]]
) -> None:
    while True:
        try:
            text = queue.get_nowait()
        except asyncio.QueueEmpty:
            return
        results.append(await _one_request(client, text))
        queue.task_done()


async def run(base_url: str, concurrency: int, total: int) -> None:
    cases = json.loads((EVAL_DIR / "test_cases.json").read_text())["cases"]
    prompts = [c["text"] for c in cases if c["category"] != "edit"]
    # Cycle through prompts to reach `total`.
    queue: asyncio.Queue = asyncio.Queue()
    for i in range(total):
        queue.put_nowait(prompts[i % len(prompts)])

    results: list[tuple[int, int, bool]] = []
    wall_start = time.perf_counter()
    async with httpx.AsyncClient(base_url=base_url) as client:
        workers = [asyncio.create_task(_worker(client, queue, results)) for _ in range(concurrency)]
        await asyncio.gather(*workers)
    wall_ms = int((time.perf_counter() - wall_start) * 1000)

    summary = _summarize(results, wall_ms, concurrency, total)
    _write_outputs(results, summary)
    _print_summary(summary)


def _summarize(
    results: list[tuple[int, int, bool]], wall_ms: int, concurrency: int, total: int
) -> dict:
    latencies = [r[0] for r in results]
    successes = sum(1 for _, _, ok in results if ok)
    return {
        "concurrency": concurrency,
        "total_requests": total,
        "wall_ms": wall_ms,
        "success_rate": successes / len(results) if results else 0.0,
        "throughput_rps": round(len(results) / (wall_ms / 1000), 2) if wall_ms else 0.0,
        "latency_ms": {
            "min": min(latencies) if latencies else 0,
            "median": int(statistics.median(latencies)) if latencies else 0,
            "p95": int(_percentile(latencies, 95)) if latencies else 0,
            "p99": int(_percentile(latencies, 99)) if latencies else 0,
            "max": max(latencies) if latencies else 0,
        },
        "status_codes": _tally_statuses(results),
    }


def _tally_statuses(results: list[tuple[int, int, bool]]) -> dict[str, int]:
    tally: dict[str, int] = {}
    for _, code, _ in results:
        key = str(code) if code else "connect_error"
        tally[key] = tally.get(key, 0) + 1
    return tally


def _percentile(values: list[float], pct: int) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * pct / 100
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def _write_outputs(results: list[tuple[int, int, bool]], summary: dict) -> None:
    results_dir = EVAL_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    json_path = results_dir / f"concurrent-{stamp}.json"
    md_path = results_dir / f"concurrent-{stamp}.md"
    raw = [{"latency_ms": ms, "status": code, "ok": ok} for ms, code, ok in results]
    json_path.write_text(json.dumps({"summary": summary, "results": raw}, indent=2))
    md_path.write_text(_render_markdown(summary))
    print(f"\nwrote {json_path.relative_to(EVAL_DIR)}")
    print(f"wrote {md_path.relative_to(EVAL_DIR)}")


def _render_markdown(s: dict) -> str:
    lat = s["latency_ms"]
    lines = [
        "# Concurrent-request evaluation",
        "",
        "| metric | value |",
        "|---|---|",
        f"| concurrency | {s['concurrency']} |",
        f"| total requests | {s['total_requests']} |",
        f"| wall time | {s['wall_ms']} ms |",
        f"| throughput | {s['throughput_rps']} rps |",
        f"| success rate | {s['success_rate']:.1%} |",
        f"| latency min/med/p95/p99/max | {lat['min']} / {lat['median']} / {lat['p95']} / {lat['p99']} / {lat['max']} ms |",
        f"| status codes | {s['status_codes']} |",
    ]
    return "\n".join(lines) + "\n"


def _print_summary(s: dict) -> None:
    lat = s["latency_ms"]
    print("\n=== Overall ===")
    print(f"  concurrency:   {s['concurrency']}")
    print(f"  requests:      {s['total_requests']} in {s['wall_ms']}ms")
    print(f"  throughput:    {s['throughput_rps']} rps")
    print(f"  success rate:  {s['success_rate']:.1%}")
    print(f"  latency (ms):  min={lat['min']} med={lat['median']} p95={lat['p95']} p99={lat['p99']} max={lat['max']}")
    print(f"  statuses:      {s['status_codes']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--total", type=int, default=16)
    args = parser.parse_args()
    asyncio.run(run(args.base_url, args.concurrency, args.total))


if __name__ == "__main__":
    main()
