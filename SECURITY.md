# MCP-Consist Security Guide

## Overview

MCP-Consist is a research prototype for lexical consistency analysis of paired
text inputs. It is **not** a security product and must not be used as a
security boundary, WAF, or sole decision mechanism for tool-call safety.

## Data handling

- Inputs are processed **in memory only**; nothing is persisted or transmitted
  during normal operation.
- No personally identifiable information (PII) is collected unless a user
  explicitly pastes it.
- No database is used (`test.db`, previously in the repo, was an unrelated
  artifact and has been archived under `_archive_unrelated/`).

## Threat model (honest)

- The detector is lexical overlap only. It does **not** understand semantics,
  negation, intent, schemas, or policies.
- It does **not** connect to, intercept, or monitor any MCP server or traffic.
- There is no sandbox, no canary credential, and no outbound network request
  (except Gradio's optional public tunnel, which is off by default).
- ALLOW is explicitly **not** proof that content is safe. BLOCK does **not**
  intercept a malicious call.

## Reporting security concerns

Security researchers are encouraged to submit findings via a **private GitHub
security advisory** on the repository `umairs759/mcp-consist`. Do **not** file
public issues for potential vulnerabilities.

No bounty is offered. Responses are best-effort from the project author.

## Known issues / no-vulnerability claim

No claim is made that the tool is free of vulnerabilities. No pentesting or
formal security audit has been performed. See `docs/SECURITY_REVIEW.md`.

## Dependencies

- `requirements.txt` pins `gradio==5.50.0` and `pytest==9.2.0`.
- No external API keys or secret tokens are required.
