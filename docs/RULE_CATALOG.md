# Rule Catalog — MCP-CONSIST

## Layer 1 — Description Integrity
- **R-101** (HIGH/MEDIUM): hidden instruction phrases; zero-width Unicode; bidi control chars; long base64-like payload indicators.

## Layer 2 — Sensitive Resource Protection
- **R-102** (MEDIUM/HIGH): references to ~/.ssh, id_rsa, .env, .aws, /etc/passwd, tokens, cookies, credentials, passwords (evidence redacted).

## Layer 3 — Schema and Parameter Integrity
- **R-201** (HIGH/MEDIUM): required args missing; unknown args when additionalProperties=false; type mismatches; enum violations.
- **R-202** (MEDIUM): undeclared side-channel params (notes, context, metadata, sidenote, ...) not declared in schema.

## Layer 4 — Capability Policy Compliance
- **R-301** (HIGH): path outside allowed roots; traversal indicators.
- **R-302** (HIGH/MEDIUM): host/URL/email not allow-listed; misleading suffixes.
- **R-303** (HIGH): action not in allowed_actions.
- **R-304** (MEDIUM): missing policy coverage fields -> WARN.

## Layer 5 — Joint Intent and Tool-Call Integrity
- **R-401** (MEDIUM): task vs proposed-call action misalignment.
- **R-402** (MEDIUM): description vs proposed-call operation/resource mismatch.
- **R-501** (HIGH): explicit cross-tool pivot markers.

## Severity penalties
LOW 0.15, MEDIUM 0.40, HIGH 0.75, CRITICAL 1.00. Centralized in config.py.