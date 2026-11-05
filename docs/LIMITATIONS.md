# Limitations — MCP-CONSIST Stage 1 (lexical prototype)

This document lists the honest limitations of the Stage 1 lexical prototype.
It is intended to counter any impression that the tool does more than it does.

## What the detector is

A lexical consistency baseline between two text inputs:

1. Normalise each input to lowercase.
2. Tokenise on whitespace into a set of tokens.
3. `overlap = len(set1 & set2) / max(len(set1), len(set2))`
4. Compare overlap to the user-selected threshold (default 0.80).
5. Emit one of ALLOW / WARN / BLOCK / ERROR.

## What it is NOT

- **No semantics.** Negation, paraphrase, synonyms, and intent are not
  understood. "allow this" and "deny this" share many tokens.
- **No schema validation.** There is no JSON schema, parameter typing, or
  constraint checking.
- **No policy enforcement.** No allow-lists, deny-lists, rate limits, or
  credential scopes are evaluated.
- **No MCP traffic monitoring.** The tool does not connect to, intercept, or
  observe any Model Context Protocol server or traffic. There is no sandbox,
  no canary credential, and no outbound network request.
- **No ML.** There is no MiniLM, no XGBoost, no embedding classifier, and no
  trained model. Any numbers reported elsewhere are from this lexical rule,
  not a learned model.
- **Not a security boundary.** ALLOW is explicitly NOT proof the content is
  safe, and BLOCK does not intercept a malicious call.

## Known questionable prototype rule (retained in Stage 1)

Identical token sets (e.g. "Hello" vs "hello", or any two inputs with the same
word set regardless of order) are flagged **BLOCK** regardless of the
threshold. This rule is part of the existing tested behaviour the supervisor
saw. It is conservative in some cases and arbitrary in others — it is a known
limitation, documented here, and revisited in Stage 2, where a rule-based
`policy-rules-v1` engine replaces overlap-only decisions.

## Result fidelity

Everything shown in the UI (badge, overlap, matched / unmatched terms,
explanation) is computed by `pipeline.analyze_pair` from the two raw inputs.
There are no JS-only mock results, no invented confidence scores, and no
decorative telemetry.

## Stage 2 direction

Stage 2 adds `mcp_consist/engine.py` (`policy-rules-v1`), a deterministic,
explainable, rule-based five-layer detector over a joint context
(description, schema, policy, task, call). It is rule-based, not ML-based, and
evaluated on a small synthetic benchmark authored by the project author
(`data/eval_cases.jsonl`), not MCPTox.
