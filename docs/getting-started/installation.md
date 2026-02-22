# Installation

## Requirements

- Python 3.11 or later
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

## Install from source

```bash
git clone https://github.com/NoeFischer/data-contract-validator.git
cd data-contract-validator
uv venv && uv pip install -e .
```

This installs the `validate-contract` CLI command.

## Development install

To also install test and lint tools:

```bash
uv pip install -e ".[dev]"
```

## Verify installation

```bash
validate-contract --version
```
