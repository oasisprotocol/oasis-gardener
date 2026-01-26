# Oasis Gardener

A simple service that regularly tops up given accounts so they don't dry out.


![Oasis Gardener](./docs/gardener.png)

## Installation and Setup

Requires locally installed [Oasis CLI] and [uv].

[Oasis CLI]: https://github.com/oasisprotocol/cli/pull/677
[uv]: https://github.com/astral-sh/uv

```shell
cp .env.example .env
# Edit .env:
# - Add monitoring addresses to WATCH_ADDRESSES
# - Add monitoring of ROFL machines to WATCH_ROFL_MACHINES
# - Add payment secret keys to SECRET_KEYS
uv run main.py
```

