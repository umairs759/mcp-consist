"""Reproducible evaluation of the policy-rules-v1 engine.

Executes the real engine against every case in data/eval_cases.jsonl and
writes results/eval_results.json. All metrics are computed from actual
engine execution; nothing is hardcoded.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure the project root (parent of scripts/) is importable.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_consist import analyze, ENGINE_NAME, ENGINE_VERSION  # noqa: E402

DATASET_PATH = PROJECT_ROOT / "data" / "eval_cases.jsonl"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_PATH = RESULTS_DIR / "eval_results.json"

STATES = ["ALLOW", "WARN", "BLOCK", "ERROR"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _config_hash() -> str:
    h = hashlib.sha256()
    for p in sorted((PROJECT_ROOT / "mcp_consist").glob("*.py")):
        h.update(p.read_bytes())
    return h.hexdigest()


def _source_revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _percentile(sorted_values: list[float], p: float) -> float:
    if not sorted_values:
        return 0.0
    s = sorted(sorted_values)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def _safe_div(num: float, den: float) -> float:
    if den == 0:
        return 0.0
    return num / den


def _load_cases(path: Path) -> list[dict]:
    cases = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def evaluate() -> dict:
    cases = _load_cases(DATASET_PATH)
    dataset_sha = _sha256_file(DATASET_PATH)
    revision = _source_revision()

    per_case: list[dict] = []
    latencies: list[float] = []
    y_true: list[str] = []
    y_pred: list[str] = []

    # Confusion matrix: rows=true, cols=pred
    confusion = {t: {p: 0 for p in STATES} for t in STATES}

    for case in cases:
        ctx = {
            "description": case.get("description", ""),
            "schema": case.get("schema", ""),
            "policy": case.get("policy", ""),
            "task": case.get("task", ""),
            "call": case.get("call", ""),
        }
        result = analyze(ctx)
        verdict = result.get("verdict", "ERROR")
        latency = result.get("latency_ms", 0.0)

        expected = case.get("expected_verdict", "ERROR")
        y_true.append(expected)
        y_pred.append(verdict)
        confusion[expected][verdict] += 1
        latencies.append(latency)

        per_case.append({
            "case_id": case.get("case_id"),
            "split": case.get("split"),
            "attack_family": case.get("attack_family"),
            "expected_verdict": expected,
            "predicted_verdict": verdict,
            "score": result.get("score"),
            "latency_ms": latency,
            "correct": verdict == expected,
        })

    n = len(cases)
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = _safe_div(correct, n)

    # ---- Per-class metrics (multiclass) ----
    per_class = {}
    for state in STATES:
        tp = confusion[state][state]
        fn = sum(confusion[state][p] for p in STATES if p != state)
        fp = sum(confusion[t][state] for t in STATES if t != state)
        support = sum(confusion[state].values())
        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, tp + fn)
        f1 = _safe_div(2 * precision * recall, precision + recall)
        per_class[state] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "support": support,
        }

    f1_values = [per_class[s]["f1"] for s in STATES]
    supports = [per_class[s]["support"] for s in STATES]
    macro_f1 = sum(f1_values) / len(f1_values)
    total_support = sum(supports)
    weighted_f1 = (
        sum(f * s for f, s in zip(f1_values, supports)) / total_support
        if total_support else 0.0
    )

    # ---- Per-family recall ----
    family_recall: dict[str, dict] = {}
    families = sorted({c.get("attack_family") for c in cases})
    for fam in families:
        fam_cases = [pc for pc in per_case if pc["attack_family"] == fam]
        fam_correct = sum(1 for pc in fam_cases if pc["correct"])
        family_recall[fam] = {
            "recall": _safe_div(fam_correct, len(fam_cases)),
            "correct": fam_correct,
            "total": len(fam_cases),
        }

    # ---- Binary malicious detection ----
    # Positive (malicious/suspicious) = expected not ALLOW.
    # Negative (benign) = expected ALLOW.
    # ERROR cases excluded from binary metrics.
    binary_pairs = [(t, p) for t, p in zip(y_true, y_pred) if t != "ERROR"]
    tp = sum(1 for t, p in binary_pairs if t != "ALLOW" and p != "ALLOW")
    fp = sum(1 for t, p in binary_pairs if t == "ALLOW" and p != "ALLOW")
    fn = sum(1 for t, p in binary_pairs if t != "ALLOW" and p == "ALLOW")
    tn = sum(1 for t, p in binary_pairs if t == "ALLOW" and p == "ALLOW")
    binary_precision = _safe_div(tp, tp + fp)
    binary_recall = _safe_div(tp, tp + fn)
    binary_f1 = _safe_div(2 * binary_precision * binary_recall,
                          binary_precision + binary_recall)
    benign_fpr = _safe_div(fp, fp + tn)  # benign false-positive rate

    # ---- Latency ----
    latencies_sorted = sorted(latencies)
    latency_p50 = _percentile(latencies_sorted, 50)
    latency_p95 = _percentile(latencies_sorted, 95)

    results = {
        "generated_at_utc": _utc_now_iso(),
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "source_revision": revision,
        "config_hash": _config_hash(),
        "dataset_path": str(DATASET_PATH),
        "dataset_sha256": dataset_sha,
        "dataset_provenance": "synthetic, authored by project author",
        "evaluation_method": (
            "Each JSONL case executed through mcp_consist.analyze(); "
            "predicted verdict compared to expected_verdict. No hardcoded "
            "results."
        ),
        "dataset_size": n,
        "dev_size": sum(1 for c in cases if c.get("split") == "dev"),
        "holdout_size": sum(1 for c in cases if c.get("split") == "holdout"),
        "accuracy": accuracy,
        "correct": correct,
        "precision": binary_precision,
        "recall": binary_recall,
        "f1": binary_f1,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "per_class": per_class,
        "per_family_recall": family_recall,
        "binary_malicious": {
            "precision": binary_precision,
            "recall": binary_recall,
            "f1": binary_f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        },
        "benign_false_positive_rate": benign_fpr,
        "confusion_matrix": confusion,
        "latency_p50_ms": latency_p50,
        "latency_p95_ms": latency_p95,
        "per_case": per_case,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)

    print(f"Evaluated {n} cases.")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Binary precision/recall/F1: "
          f"{binary_precision:.4f}/{binary_recall:.4f}/{binary_f1:.4f}")
    print(f"Macro F1: {macro_f1:.4f}  Weighted F1: {weighted_f1:.4f}")
    print(f"Benign FPR: {benign_fpr:.4f}")
    print(f"Latency p50/p95 (ms): {latency_p50:.2f}/{latency_p95:.2f}")
    print(f"Results written to {RESULTS_PATH}")
    return results


if __name__ == "__main__":
    evaluate()
