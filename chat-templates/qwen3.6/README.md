# Qwen3.6 chat templates

## Supported files

- `qwen3.6-caduceus-v1.7.jinja` — the initial supported JSON-aligned Caduceus baseline.

## Caduceus v1.7 — initial supported baseline

Caduceus v1.7 is the supported Qwen3.6 template for HermesAgent and LM Studio. Supplied tool schemas are serialized as JSON inside the tools section. Historical tool calls are replayed in JSON-shaped `&lt;tool_call&gt;` envelopes. The system contract requests the same shape for newly generated calls, but the template cannot guarantee model compliance. Tool serialization is independent from thinking controls.

Select the template through the LM Studio configuration used by HermesAgent. Copy or select the v1.7 file there, then use the deterministic checks from the repository root before changing the template.

### Controls and defaults

| Control | Default | Effect |
|---|---:|---|
| `enable_thinking` | `true` | Opens current-turn thinking; `false` emits the supported pre-closed form. |
| `preserve_thinking` | `true` | Replays supplied assistant reasoning after exact-boundary sanitization. |
| `max_tool_arg_chars` | `8000` | Limits mapped string argument values; over-limit serialized containers fail closed. |
| `max_tool_response_chars` | `16000` | Trims result text before exact-boundary sanitization. |

Tool presence does not change either thinking control.

### JSON-shaped calls

Each rendered historical call contains one JSON object with a non-empty string `name` and an object `arguments`. A representative payload is:

```json
{"name":"function_name","arguments":{"parameter":"value"}}
```

Historical mapping arguments are serialized as JSON. A non-empty serialized top-level argument string is preserved without template-side parsing; if it exceeds `max_tool_arg_chars`, rendering fails closed rather than slicing it. Tool results retain the existing plain result wrapper.

### Historical replay

Supplied user, system/developer, assistant-visible, assistant-reasoning, and tool-result content is treated as historical text. Exact call, result, thinking, ChatML, legacy native function/parameter, and legacy Caduceus boundaries are converted to inert entities or marker text. Ordinary prose, JSON, quoted braces, mathematical notation, and unrelated angle brackets remain unchanged. Caduceus's own system contract, example, and protocol wrappers remain functional.

### Deterministic limitations

The system contract guides current thinking-enabled tool turns not to simulate expected results or reproduce protocol boundaries inside reasoning. This guidance is best effort: Jinja cannot inspect or rewrite newly generated tokens. Replay sanitization is deterministic only for supplied history; the template adds no retry, response repair, parser salvage, or automatic thinking change.

Run the public checks from the repository root:

```bash
python3 -m unittest discover -v
```
