# Threat Model — MCP-CONSIST

## Assets

- Tool descriptions, schemas, capability policies, user tasks, proposed tool calls.
- Any sensitive references embedded in those inputs (paths, hosts, tokens).
- The integrity of the ALLOW/WARN/BLOCK decision.

## Trust boundaries

- Inputs are untrusted data. The engine never executes, follows, decodes, or
  fetches them.
- The Gradio UI renders all user-derived strings escaped.
- No network egress during analysis.
- No filesystem access during analysis (lexical checks only).

## Attacker assumptions

- Attacker can craft tool descriptions, schemas, policies, tasks and proposed
  calls.
- Attacker may attempt prompt injection via hidden instructions, unicode
  obfuscation, sensitive resource references, path traversal, host confusion,
  schema abuse, side-channel parameters, intent mismatch, cross-tool pivots.
- Attacker cannot modify server code or dependencies.

## Threat categories and detection

| Threat | Layer / Rule |
|---|---|
| Hidden instructions in description | Layer 1 / R-101 |
| Unicode obfuscation | Layer 1 / R-101 |
| Encoded payload indicators | Layer 1 / R-101 |
| Sensitive resource references | Layer 2 / R-102 |
| Schema violations (required/unknown/type/enum) | Layer 3 / R-201 |
| Side-channel parameters | Layer 3 / R-202 |
| Path traversal / outside roots | Layer 4 / R-301 |
| Disallowed hosts/URLs/emails | Layer 4 / R-302 |
| Disallowed actions | Layer 4 / R-303 |
| Missing policy coverage | Layer 4 / R-304 |
| Task vs call misalignment | Layer 5 / R-401 |
| Description vs call misalignment | Layer 5 / R-402 |
| Cross-tool pivot | Layer 5 / R-501 |

## Detection boundaries (not protected)

- No semantics or negation handling beyond lexical categories.
- No real MCP traffic interception.
- No filesystem-level or symlink protection.
- No ML-based detection.
- No claim of external benchmark validation.

## Known bypasses / false negatives

- Novel phrasing not matching documented patterns.
- Sensitive resources referenced indirectly or encoded.
- Path traversal via unsupported encodings.
- Host confusion via lookalike domains not in suffix list.
- Intent mismatch expressed in synonyms outside category keyword lists.
- Cross-tool pivots represented in structures not scanned.

## False-positive risks

- Technical documentation mentioning sensitive terms may trigger R-102.
- Legitimate unknown parameters may trigger R-201 when additionalProperties=false.
- Benign cross-field wording may trigger R-401/R-402.

## Deployment risks

- If exposed publicly without auth, anyone can submit inputs (still no
  execution, but resource use).
- Gradio share=True creates a public tunnel; disabled by default.
- No authentication/authorization layer.

## Responsible reporting

Report security issues privately to the project maintainer. Do not include
secrets in reports. No formal bug-bounty program exists.