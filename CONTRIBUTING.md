# Contributing

Thanks for helping. The most useful contribution needs no code: a **photo of a face on a real
watch**, because none of these faces is confirmed on one yet. Open a
[face report](https://github.com/jvitorcosta/haylou-faces/issues/new?template=face-report.yml) with
the photo, your firmware and your Hello Haylou version.

## Adding a face

Follow "Add a face" in the [README](README.md): a folder under `faces/` with a `build.py`, its art and
fonts, the built `tbwf/` and `previews/`, a README and tests.

- Art must be your own or licensed for reuse, and is published under [CC BY 4.0](LICENSE-ART).
- Bundle only fonts whose licence allows it, and list them in [THIRD_PARTY.md](THIRD_PARTY.md).
- Commit the built `.tbwf` files: people install them without building.
- Commits use [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): subject`.

## Working on it

```bash
pip install -r requirements.txt
ruff check .
ruff format --check .
python -m pytest
```

The tools that read and write `.tbwf` files live in
[haylou-rt-tools](https://github.com/jvitorcosta/haylou-rt-tools); file format changes go there.
