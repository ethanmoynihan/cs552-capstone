"""
Evaluation router — exposes the Phase 4 test suite over HTTP so the frontend
can run it interactively.

The metrics implementation lives in ../evaluation/metrics.py. We import it
lazily on first request so the backend still boots when the eval harness
dependencies (sacrebleu, rouge-score, sympy) aren't installed — e.g., on
a slimmed-down production build.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.llama_service import get_generator

router = APIRouter(prefix="/evaluation")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEST_CASES_PATH = REPO_ROOT / "evaluation" / "test_cases.json"
METRICS_DIR = REPO_ROOT / "evaluation"


_evaluate_fn = None


def _get_evaluate():
    """Lazily import metrics.evaluate so a missing eval dep doesn't break /health."""
    global _evaluate_fn
    if _evaluate_fn is None:
        if str(METRICS_DIR) not in sys.path:
            sys.path.insert(0, str(METRICS_DIR))
        from metrics import evaluate  # noqa: WPS433

        _evaluate_fn = evaluate
    return _evaluate_fn


def _load_cases() -> list[dict[str, Any]]:
    if not TEST_CASES_PATH.exists():
        raise HTTPException(status_code=503, detail="test_cases.json not found on server")
    return json.loads(TEST_CASES_PATH.read_text())["cases"]


class RunCaseRequest(BaseModel):
    id: str


class RunCaseResponse(BaseModel):
    id: str
    category: str
    text: str
    expected: str
    actual: str
    inference_ms: int
    tokens_used: int
    metrics: dict[str, Any]


@router.get("/test-cases")
def list_test_cases() -> dict[str, Any]:
    """Return the full suite so the frontend knows what to iterate."""
    return {"cases": _load_cases()}


@router.post("/run-case", response_model=RunCaseResponse)
def run_case(req: RunCaseRequest) -> RunCaseResponse:
    cases = _load_cases()
    case = next((c for c in cases if c["id"] == req.id), None)
    if case is None:
        raise HTTPException(status_code=404, detail=f"unknown case id: {req.id}")

    generator = get_generator()
    start = time.perf_counter()
    if case["category"] == "edit":
        latex, tokens, inference_ms = generator.edit(case["current_latex"], case["text"])
    else:
        latex, tokens, inference_ms = generator.generate(case["text"])
    # wall time isn't reported separately — inference_ms covers the interesting work

    evaluate = _get_evaluate()
    metrics = asdict(evaluate(latex, case["expected_latex"]))

    return RunCaseResponse(
        id=case["id"],
        category=case["category"],
        text=case["text"],
        expected=case["expected_latex"],
        actual=latex,
        inference_ms=inference_ms,
        tokens_used=tokens,
        metrics=metrics,
    )
