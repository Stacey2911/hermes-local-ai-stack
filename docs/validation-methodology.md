# Validation methodology

Public validation is deterministic and runs against the supported Caduceus v1.7 Jinja template and fixture.

Install the declared development dependency before running the suite:

```bash
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -v
```

## Test suite

Run Python compilation from the repository root:

```bash
python3 -m py_compile tests/test_caduceus_v1_7.py
```

The tests cover strict Jinja rendering, both thinking boundaries, independent controls, JSON-shaped historical calls, mapping and serialized arguments, exact supplied-content sanitization, the boundary-replay fixture, truncation, invalid containers, protocol-wrapper structure, and the byte-for-byte v1.7 template hash.

## Review checks

For a working-tree review, also check relative Markdown links, `git diff --check`, the fixed v1.7 template hash, cache/artifact absence, file modes, and staging state. These checks do not establish behavior beyond the deterministic tests above.
