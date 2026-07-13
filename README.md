# Hermes Local AI Stack

**Reusable skills, chat templates, bundles, and utilities for practical local AI agent workflows.**

Hermes Local AI Stack is an independent community collection built around [HermesAgent](https://github.com/NousResearch/hermes-agent), local model runtimes such as [LM Studio](https://lmstudio.ai/), and reusable agent workflows. Each product is packaged so people can adopt it on its own or combine it with other local-stack components.

[Catalog](#catalog) · [Contributing](CONTRIBUTING.md) · [License](LICENSE) · [HermesAgent](https://github.com/NousResearch/hermes-agent) · [LM Studio](https://lmstudio.ai/)

## What lives here

| Asset type | Purpose |
|---|---|
| Skills | Reusable HermesAgent-compatible procedures and supporting assets. |
| Chat templates | Model-specific prompt rendering for conversation history, reasoning, and structured tool use. |
| Bundles | Coordinated collections for complete, repeatable workflows. |
| Utilities | Focused helpers for local-stack setup, operation, and maintenance. |

Products are self-contained and may be installed, adapted, and used independently.

## Catalog

Caduceus is the first shipped product in the repository.

| Product | Asset type | Model family | Purpose | Files |
|---|---|---|---|---|
| Caduceus v1.8 — Recommended | Chat template | Qwen3.6 | Maintains current-task continuity, emits structured tool calls, groups independent actions, sequences dependencies, and grounds completion in returned results. | [Template](chat-templates/qwen3.6/qwen3.6-caduceus-v1.8.jinja) · [Guide](chat-templates/qwen3.6/README.md) |
| Caduceus v1.7 — Compatibility | Chat template | Qwen3.6 | Retains the earlier Caduceus thinking and history defaults for compatible setups. | [Template](chat-templates/qwen3.6/qwen3.6-caduceus-v1.7.jinja) · [Guide](chat-templates/qwen3.6/README.md) |

The [Caduceus architecture guide](docs/caduceus.md) explains how prompt rendering, model output, structured-call parsing, and tool execution fit together.

## Using an asset

1. Choose an item from the catalog.
2. Read the item’s own README or product guide.
3. Copy or install it into the relevant part of your local stack.

Each product documents its dependencies, controls, setup, and integration points close to the files you will use.

## Start with Caduceus

Clone the collection:

```bash
git clone https://github.com/Stacey2911/hermes-local-ai-stack.git
cd hermes-local-ai-stack
```

Then configure Caduceus for a Qwen3.6 model:

1. Load the intended Qwen3.6 model in LM Studio.
2. Open the model under **My Models**.
3. Expose or select the **Prompt Template** field.
4. Select the Jinja template option.
5. Paste the contents of [`qwen3.6-caduceus-v1.8.jinja`](chat-templates/qwen3.6/qwen3.6-caduceus-v1.8.jinja).

Start the LM Studio server from the app or run:

```bash
lms server start --port 1234
```

Configure HermesAgent:

```bash
hermes setup
```

For an existing HermesAgent installation, choose the model provider again:

```bash
hermes model
```

Select LM Studio and the Qwen3.6 model loaded there. The [Caduceus for Qwen3.6 guide](chat-templates/qwen3.6/README.md) covers version selection, controls, and workflow behavior.

Official references:

- [Custom prompt templates in LM Studio](https://lmstudio.ai/docs/app/advanced/prompt-template)
- [HermesAgent with LM Studio](https://lmstudio.ai/docs/integrations/hermes)
- [HermesAgent](https://github.com/NousResearch/hermes-agent)

## Repository layout

```text
chat-templates/<model-family>/   Model-specific chat templates
skills/<category>/<name>/        Reusable skill packages
bundles/<name>/                  Coordinated workflow bundles
tools/<name>/                    Local-stack utilities
docs/                            Product and architecture guides
```

Category directories are added when a product ships in that category, keeping the collection focused on usable assets.

## Contributing

Focused contributions are welcome when they add or improve a reusable asset, its documentation, or its integration instructions. See [CONTRIBUTING.md](CONTRIBUTING.md) for directory conventions, product documentation expectations, publication safety, and the contribution flow.

## Community project

Hermes Local AI Stack is independently maintained for the HermesAgent and local-AI community. Products in the catalog are designed to be understandable, adaptable, and useful in individual local setups.

## License

The repository is licensed under [Apache-2.0](LICENSE). Its templates, skills, bundles, and utilities are provided as-is for users to inspect, adapt, and integrate. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for upstream attribution.
