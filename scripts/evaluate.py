"""Reproducible evaluation of the policy-rules-v1 engine.

Executes the real engine against every case in data/eval_cases.jsonl and
writes results/eval_results.json. All metrics are computed from actual
engine execution; nothing is hardcoded.

Metrics are reported separately for:
  A. Multiclass classification (ALLOW/WARN/BLOCK/ERROR).
  B. Binary malicious detection (malicious = not ALLOW).
Development split, holdout split and complete dataset are reported separately.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

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


def _source_revision() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return "unknown"


def _config_hash() -> str:
    h = hashlib.sha256()
    for p in sorted((PROJECT_ROOT / "mcp_consist").glob("*.py")):
        h.update(p.read_bytes())
    return h.hexdigest()


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


def _run_engine(cases: list[dict]) -> tuple[list[str], list[str], list[float], list[dict]]:
    y_true, y_pred, latencies, per_case = [], [], [], []
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
    return y_true, y_pred, latencies, per_case


def _metrics(y_true, y_pred, latencies) -> dict:
    states = STATES
    n = len(y_true)
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = _safe_div(correct, n)

    confusion = {t: {p: 0 for p in states} for t in states}
    for t, p in zip(y_true, y_pred):
        confusion[t][p] += 1

    per_class = {}
    for state in states:
        tp = confusion[state][state]
        fn = sum(confusion[state][p] for p in states if p != state)
        fp = sum(confusion[t][state] for t in states if t != state)
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

    f1_values = [per_class[s]["f1"] for s in states]
    supports = [per_class[s]["support"] for s in states]
    total_support = sum(supports)
    macro_f1_all4 = sum(f1_values) / len(f1_values)
    observed_classes = [s for s in states if per_class[s]["support"] > 0]
    macro_f1_observed = (
        sum(per_class[s]["f1"] for s in observed_classes) / len(observed_classes)
        if observed_classes else 0.0
    )
    weighted_f1 = (
        sum(per_class[s]["f1"] * per_class[s]["support"] for s in states)
        / total_support
        if total_support else 0.0
    )

    # Binary malicious detection: positive = expected not ALLOW (ERROR excluded).
    pairs = [(t, p) for t, p in zip(y_true, y_pred) if t != "ERROR"]
    tp = sum(1 for t, p in pairs if t != "ALLOW" and p != "ALLOW")
    fp = sum(1 for t, p in pairs if t == "ALLOW" and p != "ALLOW")
    fn = sum(1 for t, p in pairs if t != "ALLOW" and p == "ALLOW")
    tn = sum(1 for t, p in pairs if t == "ALLOW" and p == "ALLOW")
    binary_precision = _safe_div(tp, tp + fp)
    binary_recall = _safe_div(tp, tp + fn)
    binary_f1 = _safe_div(2 * binary_precision * binary_recall,
                          binary_precision + binary_recall)
    benign_fpr = _safe_div(fp, fp + tn)

    latencies_sorted = sorted(latencies)
    latency_p50 = _percentile(latencies_sorted, 50)
    latency_p95 = _percentile(latencies_sorted, 95)

    return {
        "dataset_size": n,
        "accuracy": accuracy,
        "correct": correct,
        "multiclass": {
            "per_class": per_class,
            "macro_f1_all_four_classes": macro_f1_all4,
            "macro_f1_observed_classes": macro_f1_observed,
            "weighted_f1": weighted_f1,
            "confusion_matrix": confusion,
            "observed_classes": observed_classes,
            "unobserved_classes": [s for s in states if per_class[s]["support"] == 0],
        },
        "binary_malicious": {
            "precision": binary_precision,
            "recall": binary_recall,
            "f1": binary_f1,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "benign_false_positive_rate": benign_fpr,
        },
        "benign_false_positive_rate": benign_fpr,
        "latency_p50_ms": latency_p50,
        "latency_p95_ms": latency_p95,
    }


def evaluate() -> dict:
    cases = _load_cases(DATASET_PATH)
    dataset_sha = _sha256_file(DATASET_PATH)
    revision = _source_revision()

    dev_cases = [c for c in cases if c.get("split") == "dev"]
    holdout_cases = [c for c in cases if c.get("split") == "holdout"]

    y_true_all, y_pred_all, lat_all, per_case_all = _run_engine(cases)
    y_true_dev, y_pred_dev, lat_dev, _ = _run_engine(dev_cases)
    y_true_ho, y_pred_ho, lat_ho, _ = _run_engine(holdout_cases)

    metrics_all = _metrics(y_true_all, y_pred_all, lat_all)
    metrics_dev = _metrics(y_true_dev, y_pred_dev, lat_dev)
    metrics_ho = _metrics(y_true_ho, y_pred_ho, lat_ho)

    families = sorted({c.get("attack_family") for c in cases})
    family_recall: dict[str, dict] = {}
    per_case_lookup = {pc["case_id"]: pc for pc in per_case_all}
    for fam in families:
        fam_cases = [pc for pc in per_case_all if pc["attack_family"] == fam]
        fam_correct = sum(1 for pc in fam_cases if pc["correct"])
        family_recall[fam] = {
            "recall": _safe_div(fam_correct, len(fam_cases)),
            "correct": fam_correct,
            "total": len(fam_cases),
        }

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
            "results. ERROR class has zero support in the main dataset "
            "(malformed inputs not included); reported as not evaluated. "
            "Multiclass and binary malicious-detection metrics are reported "
            "separately."
        ),
        "dataset_size": len(cases),
        "dev_size": len(dev_cases),
        "holdout_size": len(holdout_cases),
        "overall": metrics_all,
        "dev": metrics_dev,
        "holdout": metrics_ho,
        # Backward-compatible top-level aliases (overall).
        "accuracy": metrics_all["accuracy"],
        "macro_f1": metrics_all["multiclass"]["macro_f1_all_four_classes"],
        "macro_f1_observed_classes": metrics_all["multiclass"]["macro_f1_observed_classes"],
        "weighted_f1": metrics_all["multiclass"]["weighted_f1"],
        "precision": metrics_all["binary_malicious"]["precision"],
        "recall": metrics_all["binary_malicious"]["recall"],
        "f1": metrics_all["binary_malicious"]["f1"],
        "per_class": metrics_all["multiclass"]["per_class"],
        "confusion_matrix": metrics_all["multiclass"]["confusion_matrix"],
        "per_family_recall": family_recall,
        "binary_malicious": metrics_all["binary_malicious"],
        "benign_false_positive_rate": metrics_all["benign_false_positive_rate"],
        "latency_p50_ms": metrics_all["latency_p50_ms"],
        "latency_p95_ms": metrics_all["latency_p95_ms"],
        "per_case": per_case_all,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)

    print(f"Evaluated {len(cases)} cases (dev {len(dev_cases)}, holdout {len(holdout_cases)}).")
    print(f"Overall accuracy: {metrics_all['accuracy']:.4f}")
    print(f"Macro F1 (all 4 classes): {metrics_all['multiclass']['macro_f1_all_four_classes']:.4f}")
    print(f"Macro F1 (observed): {metrics_all['multiclass']['macro_f1_observed_classes']:.4f}")
    print(f"Binary P/R/F1: {metrics_all['binary_malicious']['precision']:.4f}/"
          f"{metrics_all['binary_malicious']['recall']:.4f}/"
          f"{metrics_all['binary_malicious']['f1']:.4f}")
    print(f"Benign FPR: {metrics_all['benign_false_positive_rate']:.4f}")
    print(f"Latency p50/p95 (ms): {metrics_all['latency_p50_ms']:.2f}/{metrics_all['latency_p95_ms']:.2f}")
    print(f"Results written to {RESULTS_PATH}")
    return results


if __name__ == "__main__":
    evaluate()
