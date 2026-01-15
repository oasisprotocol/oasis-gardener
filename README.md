# Oasis Gardener

A simple service that regularly tops up given accounts so they don't dry out.

```shell
cp .env.example .env
# Edit WATCH_ADDRESSES, THRESHOLD and TOPUP_AMOUNT
SECRET_KEY=secp256k1-raw:your-private-key uv run main.py
```
