"""
Accuracy metrics for Phase 4 evaluation.

Per PROPOSAL.md §"Model Evaluation Criteria — Accuracy":
- Exact match against reference
- Edit distance from ground truth
- Mathematical equivalence
- Rendering success rate

We implement all four here. `math_equivalent` returns None (not "unchecked as
failure") when sympy can't parse one side — the proposal explicitly allows
"tracked by the tester" as a fallback, so ambiguous cases surface for review
rather than counting as wrong.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

import Levenshtein


@dataclass
class MetricResult:
    exact_match: bool
    edit_distance: int
    normalized_edit_distance: float  # 0.0 perfect, 1.0 totally different
    parses_ok: bool
    math_equivalent: bool | None  # None = could not check


def _normalize(latex: str) -> str:
    """Collapse whitespace so trivial formatting differences don't inflate edit distance."""
    return re.sub(r"\s+", " ", latex).strip()


def exact_match(candidate: str, reference: str) -> bool:
    return _normalize(candidate) == _normalize(reference)


def edit_distance(candidate: str, reference: str) -> int:
    return Levenshtein.distance(_normalize(candidate), _normalize(reference))


def normalized_edit_distance(candidate: str, reference: str) -> float:
    a, b = _normalize(candidate), _normalize(reference)
    if not a and not b:
        return 0.0
    return edit_distance(a, b) / max(len(a), len(b))


def parses_ok(latex: str) -> bool:
    """
    Render-success proxy: if pylatexenc can walk the LaTeX AST without raising,
    MathJax will almost certainly render it. Cheap pure-Python check.
    """
    try:
        from pylatexenc.latexwalker import LatexWalker

        LatexWalker(latex).get_latex_nodes()
        return True
    except Exception:
        return False


def math_equivalent(candidate: str, reference: str) -> bool | None:
    """
    Check mathematical equivalence via sympy's LaTeX parser.

    Returns:
      True  — sympy parsed both sides and simplify(a - b) == 0 (or equations match)
      False — sympy parsed both sides and they differ
      None  — sympy could not parse one/both sides (matrices, integrals with
              bounds, \\begin{...} environments, etc.). Surface for manual review.
    """
    try:
        from sympy import simplify
        from sympy.parsing.latex import parse_latex
    except ImportError:
        return None

    def _parse(s: str):
        try:
            return parse_latex(_strip_equation_wrappers(s))
        except Exception:
            return None

    # Equations: compare both sides
    if "=" in candidate and "=" in reference:
        c_lhs, _, c_rhs = candidate.partition("=")
        r_lhs, _, r_rhs = reference.partition("=")
        cl, cr = _parse(c_lhs), _parse(c_rhs)
        rl, rr = _parse(r_lhs), _parse(r_rhs)
        if any(x is None for x in (cl, cr, rl, rr)):
            return None
        try:
            return bool(simplify(cl - rl) == 0 and simplify(cr - rr) == 0)
        except Exception:
            return None

    c, r = _parse(candidate), _parse(reference)
    if c is None or r is None:
        return None
    try:
        return bool(simplify(c - r) == 0)
    except Exception:
        return None


def _strip_equation_wrappers(s: str) -> str:
    """sympy's parser doesn't like \\, \\begin{...}, or bare \\left\\|."""
    s = s.strip()
    s = re.sub(r"\\,", "", s)
    s = re.sub(r"\\\\", " ", s)
    return s.strip()


def evaluate(candidate: str, reference: str) -> MetricResult:
    return MetricResult(
        exact_match=exact_match(candidate, reference),
        edit_distance=edit_distance(candidate, reference),
        normalized_edit_distance=normalized_edit_distance(candidate, reference),
        parses_ok=parses_ok(candidate),
        math_equivalent=math_equivalent(candidate, reference),
    )
