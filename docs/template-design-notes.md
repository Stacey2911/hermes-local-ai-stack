# Caduceus v1.7 template design notes

## JSON-shaped calls

Supplied tool schemas are serialized as JSON inside the tools section. Historical tool calls are replayed in JSON-shaped `&lt;tool_call&gt;` envelopes. This keeps rendered history consistent with the intended HermesAgent and LM Studio use while retaining the existing plain tool-result wrapper. The system contract requests the same shape for newly generated calls, but the template cannot guarantee model compliance. Mapping arguments are encoded as JSON; serialized top-level argument strings are preserved without template-side parsing.

## Independent controls

`enable_thinking` selects the current-generation thinking boundary. `preserve_thinking` selects whether supplied assistant reasoning is replayed. Their defaults are both `true`, and tool presence does not change either value.

## Supplied-history sanitization

Supplied user, system/developer, assistant-visible, assistant-reasoning, and tool-result content is sanitized with exact split/join replacements. The narrow replacements cover call, result, thinking, ChatML, legacy native function/parameter, and legacy Caduceus boundaries. Ordinary JSON and prose are not parsed or generically escaped. The synthesized system contract, example, and real wrappers are not passed through this sanitizer.

## Serialized arguments and truncation

Mapped string arguments and tool results can be limited by their respective character controls. A serialized top-level argument string cannot be safely sliced without JSON parsing, so an over-limit value fails closed. Structured mapping values remain JSON-shaped.

## Generation boundary

The system contract asks thinking-enabled tool turns to avoid simulating expected results and reproducing protocol boundaries inside reasoning, then to close reasoning before the JSON call. The active assistant prefill remains a protocol boundary, and the template cannot inspect, rewrite, retry, or repair newly generated output.
