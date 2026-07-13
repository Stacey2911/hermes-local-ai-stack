# How Caduceus works

Caduceus is the first shipped product in the Hermes Local AI Stack catalog. It is a chat-template family that shapes Qwen3.6 conversations for structured local tool workflows.

## Architecture

```text
User
  → HermesAgent
  → LM Studio
  → Qwen3.6 rendered with Caduceus
  → structured actions
  → HermesAgent tools and results
```

The user gives HermesAgent an objective. HermesAgent supplies the conversation, tool definitions, and policy context to LM Studio. LM Studio renders that input through Caduceus and serves it to Qwen3.6. The model chooses a response or structured action, LM Studio parses the action, and HermesAgent executes permitted tools and returns their results.

Each layer has one clear job, so the template can focus on prompt structure while the surrounding applications handle serving, parsing, policy, and execution.

## Current-task continuity

Caduceus keeps the active objective distinct from earlier completed work. Follow-up messages can continue the same objective, correct its direction, or narrow its scope while retaining relevant returned results.

Earlier results remain useful context, while newly requested actions remain part of the current task until their own results arrive. This gives completion language a clear connection to the work performed for the active request.

## Multi-action planning

Caduceus gives Qwen3.6 a compact structure for planning more than one action:

- independent actions with known arguments can be grouped in one assistant turn;
- actions that need an earlier result stay sequential;
- operations that share mutable state remain ordered;
- overlapping files, directories, or resources retain a safe sequence;
- equivalent calls are reused or omitted unless a changed input or outcome makes another call useful.

This structure supports efficient batches while preserving dependency order and clear action boundaries.

## Result-grounded completion

Returned tool results supply the evidence for describing completed work. When every requested action succeeds, the model can summarize the completed objective from those results.

When outcomes differ, the conversation keeps each result attached to its action. The next response can describe successful work, unsuccessful work, and remaining steps with the same ordered context.

## Thinking controls

`enable_thinking` controls current-turn reasoning. It defaults to `true` in both Caduceus versions.

`preserve_thinking` controls replay of historical reasoning fields supplied by the caller. It defaults to `false` in v1.8 and `true` in v1.7.

The controls are independent. A workflow can select the current response style separately from its treatment of supplied historical reasoning, and tool availability does not change either setting.

## Call and result order

Each action contains one JSON-shaped payload with a function name and argument object. Independent actions can appear as adjacent blocks in one assistant turn, with one complete payload per action.

HermesAgent returns tool results in conversation order. Caduceus retains positional association between each historical call and result, giving Qwen3.6 a stable sequence for the next turn.

Order provides the association used by the template and keeps the model-visible history compact.

## History sanitization

Caduceus treats protocol-shaped text at exact supplied-history boundaries as quoted historical content. This keeps caller-provided content separate from the live prompt structure.

Ordinary prose and JSON remain readable. Marker-like text embedded within a larger sentence or value remains part of that content, while exact boundary-shaped text is neutralized during rendering.

Mapped historical string arguments and tool-result text also have configurable size bounds, keeping replay predictable for long conversations.

## Version selection

| Version | Choose it for |
|---|---|
| [Caduceus v1.8](../chat-templates/qwen3.6/qwen3.6-caduceus-v1.8.jinja) | New Qwen3.6 workflows that benefit from current-task grounding, independent batches, dependency-aware ordering, and result-grounded completion. |
| [Caduceus v1.7](../chat-templates/qwen3.6/qwen3.6-caduceus-v1.7.jinja) | Existing workflows that use the earlier Caduceus defaults, including historical-reasoning preservation by default. |

Both versions retain structured tool calls, ordered historical context, independent thinking controls, and exact-boundary sanitization.

## Component responsibilities

| Component | Responsibility |
|---|---|
| Caduceus | Renders prompts, history, thinking boundaries, tool definitions, and call structure. |
| Qwen3.6 | Selects and emits the next response or structured action. |
| LM Studio | Serves Qwen3.6 and parses generated structured calls. |
| HermesAgent | Applies tool policy, executes permitted actions, and returns results. |

## Install and use

See [Caduceus for Qwen3.6](../chat-templates/qwen3.6/README.md) for version selection, LM Studio installation, HermesAgent connection, controls, and workflow examples.

Keep the selected template with the model configuration so each local workflow uses the intended Caduceus behavior consistently.
