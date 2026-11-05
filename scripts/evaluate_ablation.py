"""Ablation evaluation of the policy-rules-v1 engine.

Genuinely disables layers via the engine's enabled_layers parameter and
records actual metrics for every configuration. Nothing is hardcoded.
"""

from __future__ import annotations

import hashlib
import json
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
RESULTS_PATH = PROJECT_ROOT / "results" / "ablation_results.json"

STATES = ["ALLOW", "WARN", "BLOCK", "ERROR"]
LAYER_IDS = ["layer1", "layer2", "layer3", "layer4", "layer5"]

# Configurations: (label, enabled layers)
CONFIGS = []
# All disabled baseline
CONFIGS.append(("none (all layers disabled)", []))
# Individual layers
for lid in LAYER_IDS:
    CONFIGS.append((f"{lid} only", [lid]))
# Progressive combinations
progressive = []
for lid in LAYER_IDS:
    progressive.append(lid)
    CONFIGS.append((f"progressive: {'+'.join(progressive)}", list(progressive)))
# Full engine
CONFIGS.append(("full (all five layers)", list(LAYER_IDS)))


def _utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _source_revision():
    try:
        return subprocess.check_output(
            ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return "unknown"


def _config_hash():
    h = hashlib.sha256()
    for p in sorted((PROJECT_ROOT / "mcp_consist").glob("*.py")):
        h.update(p.read_bytes())
    return h.hexdigest()


def _load_cases(path):
    cases = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


def _metrics_for_config(cases, enabled):
    y_true, y_pred = [], []
    confusion = {t: {p: 0 for p in STATES} for t in STATES}
    latencies = []
    for case in cases:
        ctx = {
            "description": case.get("description", ""),
            "schema": case.get("schema", ""),
            "policy": case.get("policy", ""),
            "task": case.get("task", ""),
            "call": case.get("call", ""),
        }
        result = analyze(ctx, enabled_layers=enabled)
        verdict = result.get("verdict", "ERROR")
        expected = case.get("expected_verdict", "ERROR")
        y_true.append(expected)
        y_pred.append(verdict)
        confusion[expected][verdict] += 1
        latencies.append(result.get("latency_ms", 0.0))

    n = len(cases)
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    accuracy = (correct / n) if n else 0.0

    per_class = {}
    for state in STATES:
        tp = confusion[state][state]
        fn = sum(confusion[state][p] for p in STATES if p != state)
        fp = sum(confusion[t][state] for t in STATES if t != state)
        support = sum(confusion[state].values())
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        per_class[state] = {"precision": precision, "recall": recall, "f1": f1, "support": support}

    f1s = [per_class[s]["f1"] for s in STATES]
    supports = [per_class[s]["support"] for s in STATES]
    total = sum(supports)
    macro_f1 = sum(f1s) / len(f1s)
    weighted_f1 = (sum(f * s for f, s in zip(f1s, supports)) / total) if total else 0.0

    # binary malicious
    pairs = [(t, p) for t, p in zip(y_true, y_pred) if t != "ERROR"]
    tp = sum(1 for t, p in pairs if t != "ALLOW" and p != "ALLOW")
    fp = sum(1 for t, p in pairs if t == "ALLOW" and p != "ALLOW")
    fn = sum(1 for t, p in pairs if t != "ALLOW" and p == "ALLOW")
    tn = sum(1 for t, p in pairs if t == "ALLOW" and p == "ALLOW")
    bp = tp / (tp + fp) if (tp + fp) else 0.0
    br = tp / (tp + fn) if (tp + fn) else 0.0
    bf1 = (2 * bp * br / (bp + br)) if (bp + br) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0

    return {
        "enabled_layers": enabled,
        "dataset_size": n,
        "accuracy": accuracy,
        "correct": correct,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "binary_precision": bp,
        "binary_recall": br,
        "binary_f1": bf1,
        "benign_false_positive_rate": fpr,
        "per_class": per_class,
        "confusion_matrix": confusion,
    }


def main():
    cases = _load_cases(DATASET_PATH)
    results = {
        "generated_at_utc": _utc_now_iso(),
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "source_revision": _source_revision(),
        "dataset_path": str(DATASET_PATH),
        "dataset_sha256": _sha256_file(DATASET_PATH),
        "dataset_provenance": "synthetic, authored by project author",
        "config_hash": _config_hash(),
        "evaluation_method": (
            "Each configuration executed through mcp_consist.analyze(enabled_layers=...). "
            "Layers not in enabled_layers are genuinely disabled (N/A, no rules run)."
        ),
        "configurations": [],
    }
    for label, enabled in CONFIGS:
        m = _metrics_for_config(cases, enabled)
        m["label"] = label
        results["configurations"].append(m)
        print(f"{label}: acc={m['accuracy']:.4f} macro_f1={m['macro_f1']:.4f} "
              f"binary_recall={m['binary_recall']:.4f} fpr={m['benign_false_positive_rate']:.4f}")

    (PROJECT_ROOT / "results").mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
    print(f"Written {RESULTS_PATH}")


if __name__ == "__main__":
    main()
