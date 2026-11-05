"""Release verification script for MCP-CONSIST."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = [
    "pipeline.py",
    "requirements.txt",
    "README.md",
    "REPORT.md",
    "SECURITY.md",
    "mcp_consist/__init__.py",
    "mcp_consist/engine.py",
    "mcp_consist/rules.py",
    "mcp_consist/config.py",
    "mcp_consist/models.py",
    "mcp_consist/normalization.py",
    "mcp_consist/validation.py",
    "mcp_consist/reporting.py",
    "demo/app.py",
    "demo/components.py",
    "demo/theme.css",
    "data/eval_cases.jsonl",
    "data/scenarios.json",
    "data/DATASHEET.md",
    "data/samples.json",
    "scripts/evaluate.py",
    "scripts/evaluate_ablation.py",
    "scripts/generate_adversarial_cases.py",
    "tests/test_engine.py",
    "docs/SECURITY_REVIEW.md",
    "docs/THREAT_MODEL.md",
]
REQUIRED_DOCS = [
    "docs/ENGINE_ARCHITECTURE.md",
    "docs/RULE_CATALOG.md",
    "docs/EVALUATION_METHODOLOGY.md",
    "docs/SUPERVISOR_DEMO_GUIDE.md",
    "docs/PROJECT_PRESENTATION.md",
]


def main():
    errors = []
    for rel in REQUIRED_FILES + REQUIRED_DOCS:
        if not (PROJECT_ROOT / rel).exists():
            errors.append(f"missing required file: {rel}")

    # Dataset validity
    dataset = PROJECT_ROOT / "data" / "eval_cases.jsonl"
    if dataset.exists():
        count = 0
        try:
            for line in dataset.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    obj = json.loads(line)
                    for k in ("case_id", "description", "schema", "policy", "task",
                              "call", "expected_verdict", "attack_family",
                              "explanation", "split"):
                        if k not in obj:
                            errors.append(f"dataset case missing {k}")
                    count += 1
            if count < 60:
                errors.append(f"dataset too small: {count} < 60")
        except Exception as e:
            errors.append(f"dataset invalid: {e}")

    # Scenarios
    scen = PROJECT_ROOT / "data" / "scenarios.json"
    if scen.exists():
        try:
            s = json.loads(scen.read_text(encoding="utf-8"))
            if not isinstance(s, list) or len(s) < 3:
                errors.append("scenarios invalid or too few")
            for item in s:
                if "expected_verdict" not in item:
                    errors.append("scenario missing expected_verdict")
        except Exception as e:
            errors.append(f"scenarios invalid: {e}")

    # Result artifacts validity
    for res in ("results/eval_results.json", "results/ablation_results.json",
                "results/robustness_results.json"):
        p = PROJECT_ROOT / res
        if p.exists():
            try:
                json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                errors.append(f"{res} invalid json: {e}")

    # Secret scan (basic)
    secret_patterns = ["AKIA", "ghp_", "BEGIN PRIVATE KEY", "PRIVATE KEY-----"]
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts or ".venv" in path.parts:
            continue
        if path.name == "verify_release.py":
            continue
        if "tests" in path.parts:
            continue
        if path.suffix in (".py", ".md", ".json", ".txt", ".css", ".html", ".yml", ".yaml"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for pat in secret_patterns:
                if pat in text:
                    errors.append(f"possible secret pattern '{pat}' in {path}")

    # Check no .venv / caches in release? just report
    if errors:
        print("VERIFY FAILED:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    print("VERIFY OK: all required files present, dataset valid, no secret patterns.")


if __name__ == "__main__":
    main()
