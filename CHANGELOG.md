# Changelog

User-visible changes are grouped by product so skills, chat templates, bundles, and utilities can share one repository history.

## Caduceus v1.8

- Carries the current task across follow-up messages while keeping earlier completed work distinct.
- Grounds completion language in tool results returned for the active objective.
- Groups independent actions with known arguments into adjacent multi-action batches.
- Keeps dependent, conflicting, shared-state, and overlapping-resource actions sequential.
- Reuses equivalent calls and keeps repeated actions tied to changed inputs or outcomes.
- Reports mixed action outcomes individually and accurately.
- Allows brief visible narration before the first thinking-enabled call while keeping adjacent calls contiguous.
- Defaults `preserve_thinking` to `false` for caller-supplied historical reasoning.

## Caduceus v1.7

- Renders one JSON-shaped payload for each structured tool call.
- Replays historical calls and results in their original order with positional association.
- Neutralizes protocol-shaped supplied history at exact boundaries while preserving ordinary prose and JSON.
- Provides independent controls for current-turn thinking and supplied historical reasoning.
- Defaults `preserve_thinking` to `true`.
- Bounds mapped string arguments and tool-result text with configurable size controls.
