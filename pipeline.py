"""Lexical consistency prototype backend.

Provides :func:`run_consistency_check` (backwards-compatible string API) and
:func:`analyze_pair` (structured dict API). All logic lives in :func:`analyze_pair`;
:func:`run_consistency_check` is a thin wrapper so there is no duplicated logic.

The detector is a *prototype*: it measures pure lexical overlap between two
normalised texts. It has no semantics, no negation handling, no policy engine
and no ML. See docs/LIMITATIONS.md for the full list.
"""

from __future__ import annotations

MAX_INPUT_LENGTH = 20_000  # characters per field


def _is_number(value) -> bool:
    """Return True for int/float (excluding bool) so thresholds like True/False
    are rejected as invalid."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _tokenise(text: str) -> set[str]:
    """Lowercase then whitespace-split into a set of tokens.

    Matches the historic prototype behaviour exactly: ``text.lower().split()``.
    """
    return set(text.lower().split())


def analyze_pair(text1, text2, threshold: float = 0.8) -> dict:
    """Analyse the lexical consistency of two texts.

    Returns a dict with keys::

        status        "ALLOW" | "WARN" | "BLOCK" | "ERROR"
        overlap       float in [0, 1] (None on ERROR)
        threshold     float (the validated threshold, None if invalid)
        matched_terms sorted list of shared tokens
        unmatched_a   sorted list of tokens only in text1
        unmatched_b   sorted list of tokens only in text2
        explanation   human-readable short explanation
        error         human-readable error message (empty on success)

    Rules:
      * None / non-string / empty / whitespace-only input -> ERROR
      * either field longer than MAX_INPUT_LENGTH -> ERROR
      * threshold not a number in [0, 1] -> ERROR (no exception raised)
      * identical token sets -> BLOCK  (prototype rule - see LIMITATIONS)
      * overlap >= threshold -> ALLOW
      * otherwise -> WARN
    """
    result = {
        "status": "ERROR",
        "overlap": None,
        "threshold": None,
        "matched_terms": [],
        "unmatched_a": [],
        "unmatched_b": [],
        "explanation": "",
        "error": "",
    }

    # --- input validation -------------------------------------------------
    if text1 is None or text2 is None:
        result["error"] = "Both inputs are required."
        result["explanation"] = "ERROR: one or both inputs were None."
        return result
    if not isinstance(text1, str) or not isinstance(text2, str):
        result["error"] = "Both inputs must be text strings."
        result["explanation"] = "ERROR: non-string input provided."
        return result
    if not text1.strip() or not text2.strip():
        result["error"] = "Inputs must not be empty or whitespace only."
        result["explanation"] = "ERROR: empty/whitespace-only input."
        return result
    if len(text1) > MAX_INPUT_LENGTH or len(text2) > MAX_INPUT_LENGTH:
        result["error"] = (
            f"Each input must be {MAX_INPUT_LENGTH:,} characters or fewer."
        )
        result["explanation"] = "ERROR: input exceeds maximum length."
        return result

    # --- threshold validation --------------------------------------------
    if not _is_number(threshold) or not (0.0 <= threshold <= 1.0):
        result["error"] = f"Threshold must be a number between 0 and 1 (got {threshold!r})."
        result["explanation"] = "ERROR: invalid threshold."
        return result
    result["threshold"] = float(threshold)

    # --- tokenisation + overlap ------------------------------------------
    set1 = _tokenise(text1)
    set2 = _tokenise(text2)

    if not set1 or not set2:
        result["error"] = "Inputs produced no tokens."
        result["explanation"] = "ERROR: no tokens after normalisation."
        return result

    matched = set1 & set2
    overlap = len(matched) / max(len(set1), len(set2))
    result["overlap"] = overlap
    result["matched_terms"] = sorted(matched)
    result["unmatched_a"] = sorted(set1 - set2)
    result["unmatched_b"] = sorted(set2 - set1)

    # --- decision ---------------------------------------------------------
    # NOTE (Stage 1): identical token sets are flagged BLOCK regardless of
    # threshold. This is a known questionable prototype rule - see
    # docs/LIMITATIONS.md ("prototype rule: identical token sets are flagged").
    # Do not silently change this behaviour.
    if overlap == 1.0:
        result["status"] = "BLOCK"
        result["explanation"] = (
            "The two inputs share the same set of tokens (identical after "
            "lowercase + whitespace normalisation), so they are flagged as "
            "BLOCK under the prototype identical-set rule."
        )
    elif overlap >= result["threshold"]:
        result["status"] = "ALLOW"
        result["explanation"] = (
            f"Lexical overlap {overlap:.3f} meets the threshold "
            f"{result['threshold']:.2f} — NOT proof the content is safe."
        )
    else:
        result["status"] = "WARN"
        result["explanation"] = (
            f"Lexical overlap {overlap:.3f} is below the threshold "
            f"{result['threshold']:.2f}."
        )

    return result


def run_consistency_check(input_text1, input_text2, threshold: float = 0.8) -> str:
    """Backwards-compatible string API.

    Returns one of ``"ALLOW"``, ``"WARN"``, ``"BLOCK"``, ``"ERROR"``.

    Delegates entirely to :func:`analyze_pair`.
    """
    return analyze_pair(input_text1, input_text2, threshold)["status"]
