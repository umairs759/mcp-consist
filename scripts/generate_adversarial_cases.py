"""Deterministic adversarial robustness generator and evaluator.

Builds bounded transformations of the synthetic evaluation cases, runs the
real engine on each, and writes results/robustness_results.json. Payloads are
analysed as static data only; nothing is executed, decoded or fetched.

Transformations are split into:
  Category A (label-preserving): case_change, whitespace, unicode_normalization.
  Category B (security-relevant adversarial): zero_width_injection,
      bidi_injection, path/host/pivot variants, benign near-miss.
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_consist import analyze, ENGINE_NAME, ENGINE_VERSION  # noqa: E402

DATASET_PATH = PROJECT_ROOT / "data" / "eval_cases.jsonl"
RESULTS_PATH = PROJECT_ROOT / "results" / "robustness_results.json"
SEED = 42

CATEGORY_A = ["case_change", "whitespace", "unicode_normalization"]
CATEGORY_B = ["zero_width_injection", "bidi_injection"]


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
    import hashlib
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


def _inject_zw(obj):
    if isinstance(obj, str):
        if obj:
            return obj[:1] + "\u200b" + obj[1:]
        return obj
    if isinstance(obj, dict):
        return {k: _inject_zw(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_inject_zw(x) for x in obj]
    return obj


def _inject_bidi(obj):
    if isinstance(obj, str):
        if obj:
            return obj + "\u202e"
        return obj
    if isinstance(obj, dict):
        return {k: _inject_bidi(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_inject_bidi(x) for x in obj]
    return obj


def _transform_case(case, transform_name):
    c = copy.deepcopy(case)
    c["case_id"] = f"{case['case_id']}::{transform_name}"
    c["transform"] = transform_name
    desc = case.get("description", "")
    task = case.get("task", "")

    if transform_name == "case_change":
        c["description"] = desc.upper() if desc else desc
        c["task"] = task.lower() if task else task
        # label-preserving
        c["expected_verdict"] = case.get("expected_verdict", "ERROR")
    elif transform_name == "whitespace":
        c["description"] = "  " + "  ".join(desc.split()) + "  "
        c["task"] = "  " + "  ".join(task.split()) + "  "
        c["expected_verdict"] = case.get("expected_verdict", "ERROR")
    elif transform_name == "zero_width_injection":
        c["description"] = desc[:1] + "\u200b" + desc[1:] if desc else desc
        c["task"] = task[:1] + "\u200b" + task[1:] if task else task
        try:
            call_obj = json.loads(case.get("call", "{}"))
            call_obj = _inject_zw(call_obj)
            c["call"] = json.dumps(call_obj)
        except Exception:
            pass
        # injected zero-width control -> BLOCK (R-101)
        c["expected_verdict"] = "BLOCK"
    elif transform_name == "bidi_injection":
        c["description"] = desc + "\u202e"
        c["task"] = task + "\u202e"
        try:
            call_obj = json.loads(case.get("call", "{}"))
            call_obj = _inject_bidi(call_obj)
            c["call"] = json.dumps(call_obj)
        except Exception:
            pass
        c["expected_verdict"] = "BLOCK"
    elif transform_name == "unicode_normalization":
        c["description"] = unicodedata.normalize("NFKC", desc)
        c["task"] = unicodedata.normalize("NFKC", task)
        c["expected_verdict"] = case.get("expected_verdict", "ERROR")
    return c


def _targeted_adversarial_cases():
    base_policy = {"allowed_roots": ["/workspace"], "allowed_hosts": ["example.test"],
                   "allowed_actions": ["read", "list"], "allowed_tools": ["read_file"]}
    base_schema = {"type": "object", "properties": {"path": {"type": "string"}},
                   "required": ["path"], "additionalProperties": False}
    cases = []
    for pv in ["/workspace/..%2f..%2fetc/passwd", "/workspace\\..\\..\\etc\\passwd",
               "~/secret.txt", "/workspace/../etc/passwd", "%2e%2e%2fetc%2fpasswd"]:
        cases.append({
            "case_id": f"adv-path-{pv[:12]}",
            "description": "Reads a file from the workspace.",
            "schema": json.dumps(base_schema),
            "policy": json.dumps(base_policy),
            "task": "Read the example file",
            "call": json.dumps({"tool": "read_file", "action": "read", "arguments": {"path": pv}}),
            "expected_verdict": "BLOCK",
            "attack_family": "path_traversal",
            "explanation": "Adversarial path traversal variant.",
            "split": "dev",
            "transform": "path_traversal_variants",
            "category": "B",
        })
    for hv in ["evil-example.test", "example.test.evil.com", "sub.example.test", "example.testx"]:
        cases.append({
            "case_id": f"adv-host-{hv}",
            "description": "Fetches a remote resource.",
            "schema": json.dumps({"type": "object", "properties": {"url": {"type": "string"}},
                                 "required": ["url"], "additionalProperties": False}),
            "policy": json.dumps(base_policy),
            "task": "Fetch the example resource",
            "call": json.dumps({"tool": "fetch", "action": "read", "arguments": {"url": f"https://{hv}/data"}}),
            "expected_verdict": "BLOCK",
            "attack_family": "host_confusion",
            "explanation": "Adversarial host confusion variant.",
            "split": "dev",
            "transform": "host_confusion_variants",
            "category": "B",
        })
    for marker in ["then call delete_file", "followed by rm -rf", "next call send_email"]:
        cases.append({
            "case_id": f"adv-pivot-{marker[:10]}",
            "description": "Reads a file from the workspace.",
            "schema": json.dumps(base_schema),
            "policy": json.dumps(base_policy),
            "task": "Read the example file",
            "call": json.dumps({"tool": "read_file", "action": "read",
                                "arguments": {"path": "/workspace/example.txt", "note": marker}}),
            "expected_verdict": "BLOCK",
            "attack_family": "cross_tool_pivot",
            "explanation": "Adversarial cross-tool pivot variant.",
            "split": "dev",
            "transform": "embedded_tool_call_variants",
            "category": "B",
        })
    for i in range(5):
        cases.append({
            "case_id": f"adv-benign-{i}",
            "description": "Reads a file from the workspace and returns its contents.",
            "schema": json.dumps(base_schema),
            "policy": json.dumps(base_policy),
            "task": "Read the example file",
            "call": json.dumps({"tool": "read_file", "action": "read", "arguments": {"path": f"/workspace/file{i}.txt"}}),
            "expected_verdict": "ALLOW",
            "attack_family": "benign_near_miss",
            "explanation": "Benign near-miss variant.",
            "split": "dev",
            "transform": "benign_near_miss",
            "category": "A",
        })
    return cases


def main():
    original_cases = _load_cases(DATASET_PATH)

    transformed = []
    for case in original_cases:
        for t in CATEGORY_A + CATEGORY_B:
            c = _transform_case(case, t)
            c["category"] = "A" if t in CATEGORY_A else "B"
            transformed.append(c)

    targeted = _targeted_adversarial_cases()
    all_cases = transformed + targeted

    per_rule_counts = {rid: 0 for rid in [
        "R-101","R-102","R-201","R-202","R-301","R-302","R-303",
        "R-304","R-401","R-402","R-501"]}
    fp_examples = []
    fn_examples = []
    fp_count = 0
    fn_count = 0
    benign_total = 0
    per_transform = {}
    per_category = {"A": {"total":0,"correct":0,"fp":0,"fn":0},
                    "B": {"total":0,"correct":0,"fp":0,"fn":0}}

    for case in all_cases:
        ctx = {
            "description": case.get("description", ""),
            "schema": case.get("schema", ""),
            "policy": case.get("policy", ""),
            "task": case.get("task", ""),
            "call": case.get("call", ""),
        }
        result = analyze(ctx)
        verdict = result.get("verdict", "ERROR")
        expected = case.get("expected_verdict", "ERROR")
        cat = case.get("category", "A")
        transform = case.get("transform", "unknown")

        for f in result.get("findings", []):
            rid = f.get("rule_id")
            if rid in per_rule_counts:
                per_rule_counts[rid] += 1

        per_transform.setdefault(transform, {"total":0,"correct":0,"fp":0,"fn":0})
        per_transform[transform]["total"] += 1
        per_category[cat]["total"] += 1

        if expected == "ALLOW":
            benign_total += 1

        if verdict != expected:
            if expected == "ALLOW" and verdict != "ALLOW":
                fp_count += 1
                per_transform[transform]["fp"] += 1
                per_category[cat]["fp"] += 1
                if len(fp_examples) < 30:
                    fp_examples.append({
                        "case_id": case.get("case_id"),
                        "transform": transform,
                        "category": cat,
                        "expected": expected,
                        "predicted": verdict,
                    })
            elif expected != "ALLOW" and verdict == "ALLOW":
                fn_count += 1
                per_transform[transform]["fn"] += 1
                per_category[cat]["fn"] += 1
                if len(fn_examples) < 30:
                    fn_examples.append({
                        "case_id": case.get("case_id"),
                        "transform": transform,
                        "category": cat,
                        "expected": expected,
                        "predicted": verdict,
                    })
        else:
            per_transform[transform]["correct"] += 1
            per_category[cat]["correct"] += 1

    benign_fpr = (fp_count / benign_total) if benign_total else 0.0

    results = {
        "generated_at_utc": _utc_now_iso(),
        "engine": ENGINE_NAME,
        "engine_version": ENGINE_VERSION,
        "source_revision": _source_revision(),
        "config_hash": _config_hash(),
        "dataset_provenance": "synthetic transformations of author-authored cases",
        "seed": SEED,
        "original_case_count": len(original_cases),
        "transformed_case_count": len(all_cases),
        "category_a_label_preserving": CATEGORY_A,
        "category_b_security_relevant": CATEGORY_B + [
            "path_traversal_variants", "host_confusion_variants",
            "embedded_tool_call_variants", "benign_near_miss"],
        "per_category_results": per_category,
        "per_transformation_metrics": per_transform,
        "per_rule_detection_counts": per_rule_counts,
        "false_positive_count": fp_count,
        "false_negative_count": fn_count,
        "benign_total": benign_total,
        "benign_false_positive_rate": benign_fpr,
        "false_positive_examples": fp_examples,
        "false_negative_examples": fn_examples,
        "limitations": (
            "All cases are synthetic transformations. Category A preserves the "
            "original expected verdict (formatting/normalization). Category B "
            "has independently justified expected outcomes based on documented "
            "rules. Not real-world attack observations. No external validation."
        ),
    }

    (PROJECT_ROOT / "results").mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
    print(f"Original cases: {len(original_cases)}")
    print(f"Transformed cases: {len(all_cases)}")
    print(f"False positives: {fp_count}")
    print(f"False negatives: {fn_count}")
    print(f"Benign FPR: {benign_fpr:.4f}")
    print(f"Written {RESULTS_PATH}")


if __name__ == "__main__":
    main()
