# Caduceus for Qwen3.6

Caduceus is a Qwen3.6 chat-template family for structured tool workflows through LM Studio and HermesAgent.

The templates render conversation history, thinking boundaries, tool definitions, structured actions, and returned results into a consistent prompt for Qwen3.6.

## Choose a version

| Version | Use |
|---|---|
| [v1.8 — Recommended](qwen3.6-caduceus-v1.8.jinja) | Current-task grounding, independent call batches, dependency-aware sequencing, and result-grounded completion. |
| [v1.7 — Compatibility](qwen3.6-caduceus-v1.7.jinja) | Earlier Caduceus behavior with the original historical-reasoning default. |

Start with v1.8 for new Qwen3.6 setups. Choose v1.7 when an existing workflow depends on the earlier history-preservation behavior.

## What Caduceus improves

- **Consistent structured calls:** each action carries one JSON-shaped function name and argument object.
- **Active-task continuity:** follow-up turns continue, narrow, or correct the current objective without confusing it with earlier work.
- **Ordered history:** calls and returned results retain their sequence and positional relationship.
- **Independent batching:** actions with known arguments and independent effects can share one assistant turn.
- **Dependency-aware sequencing:** actions that depend on results or touch conflicting state remain ordered.
- **Mixed-result reporting:** completion language reflects the outcome of each returned action.
- **Supplied-history sanitization:** protocol-shaped boundaries in caller-provided history are neutralized while ordinary prose and JSON stay readable.
- **Configurable thinking:** current-turn reasoning and historical-reasoning replay use separate controls.

## Install in LM Studio

Apply Caduceus as a per-model Jinja prompt-template override:

1. Download or clone this repository.
2. Open LM Studio and load the intended Qwen3.6 model.
3. Go to **My Models** and open the model’s settings.
4. Find the **Prompt Template** field. If the field is hidden, expose the advanced model settings.
5. Select the Jinja template option.
6. Open the chosen Caduceus file and copy its complete contents.
7. Paste the contents into the Prompt Template field and save the model settings.

Use [`qwen3.6-caduceus-v1.8.jinja`](qwen3.6-caduceus-v1.8.jinja) for the recommended setup or [`qwen3.6-caduceus-v1.7.jinja`](qwen3.6-caduceus-v1.7.jinja) for compatibility.

LM Studio documents the model-level editor in [Customizing the Prompt Template](https://lmstudio.ai/docs/app/advanced/prompt-template).

## Connect HermesAgent

For a new HermesAgent setup, run:

```bash
hermes setup
```

For an existing installation, choose the model provider and model again:

```bash
hermes model
```

Select LM Studio, then select the Qwen3.6 model loaded in LM Studio. Start the LM Studio server before beginning the agent workflow.

The [LM Studio Hermes integration guide](https://lmstudio.ai/docs/integrations/hermes) covers the connection flow.

## Controls

| Control | v1.8 default | v1.7 default | Purpose |
|---|---:|---:|---|
| `enable_thinking` | `true` | `true` | Controls current-turn reasoning. |
| `preserve_thinking` | `false` | `true` | Replays historical reasoning fields supplied by the caller. |
| `max_tool_arg_chars` | `8000` | `8000` | Bounds historical mapped string argument values. |
| `max_tool_response_chars` | `16000` | `16000` | Bounds historical tool-result text. |
| `add_vision_id` | `false` | `false` | Adds numbered labels to rendered visual inputs when enabled. |

These controls remain independent of whether tools are present. `enable_thinking` affects the current response; `preserve_thinking` affects supplied historical reasoning.

## Caduceus v1.8 workflow

### Active task

Caduceus carries the active objective across follow-up messages. A user can continue, narrow, or correct the work while the prompt distinguishes the current request from completed earlier work.

### Independent actions

When several permitted actions have known arguments and independent effects, Qwen3.6 can emit them together as adjacent structured blocks. This keeps multi-file reads, independent lookups, and similar work compact.

### Dependent actions

An action that needs an earlier result stays sequential. The same ordering applies to conflicting operations, shared mutable state, and overlapping resources.

### Tool results

HermesAgent returns each action result to the conversation. Caduceus preserves call and result order so the next model turn can use the returned information in the active objective.

### Mixed outcomes

When a group contains different outcomes, the next response reports each outcome accurately and bases completion on the successful returned work.

### Thinking boundaries

Thinking-enabled responses keep current-turn reasoning in its dedicated region. Brief user-facing narration may introduce the first structured action, while adjacent actions remain contiguous. Thinking-disabled responses move directly to the response or action content.

## Tool-call shape

Each structured action contains one JSON payload:

```json
{"name":"function_name","arguments":{"parameter":"value"}}
```

Every action uses its own call block. Independent actions may be emitted as adjacent blocks in one assistant turn, preserving a simple one-action-per-payload structure.

## Historical context

Historical calls remain ordered, and returned results retain positional association with those calls. This gives later turns a readable sequence of actions and outcomes.

Protocol-shaped supplied history is neutralized at exact boundaries. Ordinary prose and JSON remain readable, including marker-like text that appears as part of a larger string.

`preserve_thinking` controls only reasoning fields supplied by the caller. Current-turn reasoning remains under `enable_thinking`.

## Component roles

| Component | Responsibility |
|---|---|
| Caduceus | Renders prompts, tool definitions, thinking boundaries, and historical context. |
| Qwen3.6 | Produces the next response or structured action. |
| LM Studio | Serves the model and parses generated structured calls. |
| HermesAgent | Applies tool policy, executes actions, and returns results. |

## More information

- [How Caduceus works](../../docs/caduceus.md)
- [Repository changelog](../../CHANGELOG.md)
- [Third-party notices](../../THIRD_PARTY_NOTICES.md)

## License

Caduceus templates are provided as-is under the repository’s [Apache-2.0 license](../../LICENSE). See [THIRD_PARTY_NOTICES.md](../../THIRD_PARTY_NOTICES.md) for upstream attribution.
