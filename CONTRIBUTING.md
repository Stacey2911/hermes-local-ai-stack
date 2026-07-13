# Contributing

Hermes Local AI Stack welcomes focused contributions that make practical local-agent workflows easier to install, understand, and reuse. Contributions may introduce a new asset or improve an existing product and its documentation.

## What belongs here

The catalog accepts:

- skills that package reusable HermesAgent-compatible procedures;
- chat templates that shape model-specific conversation and tool behavior;
- bundles that coordinate several assets into a repeatable workflow;
- utilities that help people set up, operate, or maintain a local stack;
- product documentation that makes an asset easier to adopt.

Keep each contribution centered on a practical problem and a reusable solution.

## Where assets go

Use the directory that matches the product:

```text
skills/<category>/<skill-name>/
chat-templates/<model-family>/
bundles/<bundle-name>/
tools/<tool-name>/
docs/
```

A product may keep supporting files inside its own directory when those files are part of the product. Add a category directory when it contains a usable contribution rather than an empty placeholder.

## What each product should include

Every product should provide:

- a clear name and purpose;
- installation or copy instructions;
- practical usage examples;
- documented controls or configuration inputs;
- third-party attribution where applicable;
- a license compatible with the repository;
- an entry in the root catalog;
- a changelog entry for a new product or user-visible version.

Place detailed product instructions beside the asset or in a focused guide under `docs/`.

## Documentation style

Write for someone who wants to use the contribution:

- organize instructions around tasks and outcomes;
- use generic paths and examples that transfer between machines;
- describe capabilities concisely and factually;
- escape protocol-like examples in Markdown or use clear placeholders;
- keep product-specific detail in the product directory instead of expanding the root README.

Commands should be ready to copy when practical, with variables and placeholders clearly identified.

## Publication safety

Exclude local or private material from contributions, including:

- credentials and API tokens;
- local machine paths and private hostnames;
- session exports and logs;
- memory content and personal data;
- generated caches;
- editor backups and temporary files.

Review examples and command output for local details before adding them to a public product guide.

## Attribution and licensing

Repository-original material is distributed under [Apache-2.0](LICENSE). Contributions must use a compatible license and retain applicable third-party copyright, license, and source notices.

Update [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) when an asset adapts or redistributes third-party material that requires attribution.

## Contribution flow

1. Keep one contribution focused on one product or a closely related bundle.
2. Update the root catalog and the relevant product documentation.
3. Review the complete diff for unrelated changes and private material.
4. Open a pull request with a concise explanation of the problem solved and how to use the contribution.

Small, coherent contributions are easier for community users to understand, adapt, and maintain.
