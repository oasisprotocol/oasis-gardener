# Oasis Gardener

A simple service that regularly tops up given accounts so they don't dry out.


![Oasis Gardener](./docs/gardener.png)

## Installation and Setup

Requires locally installed [Oasis CLI] and [uv].

[Oasis CLI]: https://github.com/oasisprotocol/cli/pull/677
[uv]: https://github.com/astral-sh/uv

```shell
cp .env.example .env
# Edit .env: Change WATCH_ADDRESSES and SECRET_KEYS
uv run main.py
```

