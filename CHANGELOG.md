# Changelog

## v1.7 — initial supported baseline

### Added

- Supplied tool schemas serialized as JSON inside the tools section, and historical tool calls replayed in JSON-shaped `&lt;tool_call&gt;` envelopes, with the existing plain tool-result wrapper.
- Independent `enable_thinking` and `preserve_thinking` controls, both enabled by default.
- Exact-boundary sanitization for supplied user, system/developer, assistant, reasoning, and tool-result content.
- Mapping and serialized-string historical argument handling, including fail-closed over-limit serialized containers.
- Deterministic rendering tests and boundary-replay coverage.

### Limitations

- Current-generation boundary placement is system guidance; the Jinja template cannot rewrite generated output.
- The template adds no runtime retry, response repair, parser salvage, or automatic thinking change.
