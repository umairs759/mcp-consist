# MCP-Consist Security Guide

## Overview

MCP-Consist is a consistency-checking tool for multi-context text evaluation. This project is intended for research and educational purposes.

## Data Handling

- All input text is processed in-memory only; no data is persisted or transmitted externally during normal operation.
- The tool does not store any personally identifiable information (PII) unless explicitly provided by the user.

## Known Issues

- No security vulnerabilities identified to date.
- The Gradio UI runs locally; for public deployment, consider enabling authentication and HTTPS.

## Dependencies

- All dependencies are listed in `requirements.txt` (if present).
- No external API keys or secret tokens are required for core functionality.