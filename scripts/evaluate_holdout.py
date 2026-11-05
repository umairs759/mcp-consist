"""Evaluate the independent synthetic holdout v2 set."""

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

from scripts.evaluate import _load_cases, _run_engine, _metrics, _sha256_file, _config_hash, _source_revision  # noqa: E402

DATASET_PATH = PROJECT_ROOT / "data" / "eval_holdout_v2.jsonl"
RESULTS_PATH = PROJECT_ROOT / "results" / "holdout_v2_results.json"


def main():
    cases = _load_cases(DATASET_PATH)
    y_true, y_pred, lat, _ = _run_engine(cases)
    m = _metrics(y_true, y_pred, lat)
    results = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engine": "policy-rules-v1",
        "engine_version": __import__("mcp_consist").ENGINE_VERSION,
        "source_revision": _source_revision(),
        "config_hash": _config_hash(),
        "dataset_path": str(DATASET_PATH),
        "dataset_sha256": _sha256_file(DATASET_PATH),
        "dataset_provenance": "synthetic, authored by project author (independent holdout v2)",
        "note": "Independent synthetic holdout created after engine fixes; not external validation.",
        **m,
    }
    (PROJECT_ROOT / "results").mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
    print(f"Evaluated {len(cases)} holdout v2 cases. Accuracy {m['accuracy']:.4f}")


if __name__ == "__main__":
    main()
