# MoneyPrinterTurbo Foundation

This is an independent public fork of [harry0703/MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo), not an official upstream release.
The upstream MIT LICENSE, source files, main history (1,178 commits at import) and 21 tags were retained.
Import base: `90f77011d7e3b46d382e6d0180dabfb6725ffee4`.
Existing tags describe upstream releases, not releases validated by this fork.

## First foundation increment (2026-10-20)

- Fork banners and package metadata identify this repository. The package name and entry point remain `mpt` for compatibility.
- CI explicitly requests only `contents: read`.
- The inherited container workflow no longer runs on pushes or tags. A manual run builds only by default; publishing requires explicitly setting `publish=true` and targets this fork's GHCR namespace. No upstream registry target is used.
- GitHub Actions remain disabled at repository level while initial inherited-suite failures are investigated. This change does not start video creation, media uploads, releases or package publishing.
- `mpt doctor` provides a read-only offline preflight without importing `app.config`, initializing configuration, contacting providers, or executing FFmpeg. It checks tool discovery, TOML readability and obviously exposed API bindings. It never reports configuration values or parser exception text.

The original API/CLI/WebUI, provider integrations and task/state handling remain available. This increment does not claim a new video production pipeline, credential availability or production readiness.

## Setup and offline preflight

Python 3.11 or newer and [uv](https://docs.astral.sh/uv/) are required:

```sh
uv sync --frozen --python 3.11
uv run --no-sync mpt doctor --json
# Equivalent without the installed entry point:
uv run --no-sync python -m app.doctor --json
```

Keep runtime data outside the checkout using a private `MPT_HOME` directory. Copy `config.example.toml` to that directory as `config.toml` and edit it privately when generation is actually needed. Alternatively, `doctor --config /private/config.toml` reads one explicit file without printing its path or contents. Protect configuration with filesystem permissions; do not commit it or put credentials in command arguments.

Doctor exit codes: 0 for checks that are OK or warnings; 1 for missing FFmpeg/FFprobe or unreadable/invalid configuration; 2 for invalid command arguments. Missing configuration is a warning and is not automatically created. Warnings require attention before exposing an API.
A successful doctor result does not verify provider credentials, network connectivity, codecs, fonts, filesystem writability or a rendered video. This is not a complete security check.

## Requested external research: actual result

The user requested **Vertex AI Claude Opus 5.5, Medium**, for proposals only. Codex performs implementation.
A single proposal-only request used the official `claude-opus-5-5` model, global `rawPredict`, adaptive thinking and `output_config.effort=medium`. No tools, model fallback or automatic retry were provided.

**Result: blocked, HTTP 429 RESOURCE_EXHAUSTED**, for
`aiplatform.googleapis.com/global_online_prediction_requests_per_base_model`,
base model `anthropic-claude-opus`. No proposal text was received. A read-only quota lookup confirmed an effective and default limit of **0 requests per minute** for this model quota.
Model metadata availability does not establish usable inference capacity. No claim is made about remaining credit or token charges; billing has not been verified.

Consequently, the changes above are Codex's own bounded implementation, not Opus recommendations. The source evidence and request are retained privately on the VM, without credentials. Once the project's Opus quota is enabled/increased, request the actual source-grounded proposal and implement accepted findings separately.

References:
- [Official Opus 5.5 model documentation](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/partner-models/claude/opus-5-5)
- [Vertex inference quotas](https://cloud.google.com/vertex-ai/docs/generative-ai/quotas-genai)
- [Google Cloud quotas console](https://console.cloud.google.com/iam-admin/quotas?project=voice-box-512208)

## Validation and limits

- Changed Python files: Ruff passed.
- Doctor boundary tests and existing packaging tests: **23 passed**, one existing Starlette deprecation warning.
- The expanded foundation tests (including manual-publication and read-only CI permission checks): **8 passed**; this adds two workflow policy tests to the six doctor tests already included above.
- Eight original loopback HTTP fixture tests, rerun directly on the VM: **8 passed**.
- An earlier broad upstream baseline inside the Antigravity terminal sandbox reported 2,345 passed, 49 failed and 54 skipped. The eight passing direct-VM reruns show that sandbox results alone do not establish source defects. The remaining failures have not been classified or fixed.
- No complete post-change suite, GitHub-hosted CI run, production video/audio generation, provider credential test or public media upload was performed.

Do not replace remaining unknowns with a blanket “all tests passed” or “production ready” claim.
