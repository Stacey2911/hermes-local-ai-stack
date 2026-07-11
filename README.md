# Hermes Local AI Stack

Reusable prompt templates, deterministic tests, and concise design notes for local Qwen3.6 use with HermesAgent and LM Studio.

## Caduceus v1.7 — initial supported baseline

Caduceus v1.7 is the repository's initial supported Caduceus baseline and the JSON-aligned Qwen3.6 chat template in [chat-templates/qwen3.6/qwen3.6-caduceus-v1.7.jinja](chat-templates/qwen3.6/qwen3.6-caduceus-v1.7.jinja). Supplied tool schemas are serialized as JSON inside the tools section. Historical tool calls are replayed in JSON-shaped `&lt;tool_call&gt;` envelopes, while the system contract only requests the same shape for newly generated calls. The template retains the plain tool-result wrapper and exposes independent `enable_thinking` and `preserve_thinking` controls.

Select the template in the LM Studio configuration used by HermesAgent. The template-specific [README](chat-templates/qwen3.6/README.md) describes its controls and replay behavior. Public checks are deterministic Jinja render tests; the template cannot rewrite newly generated tokens or repair generated output.

See the [changelog](CHANGELOG.md), [Apache License 2.0](LICENSE), and [third-party notices](THIRD_PARTY_NOTICES.md).

## Repository contents

- `chat-templates/` — Qwen3.6 prompt templates.
- `tests/` — deterministic rendering tests and a boundary-replay fixture.
- `docs/` — concise design and validation notes.

## Limitations

Exact protocol boundaries in supplied message content are neutralized during replay. Current-generation boundary placement remains prompt guidance because a Jinja template cannot inspect or rewrite model output. No runtime retry, response repair, parser salvage, or automatic thinking change is included.
