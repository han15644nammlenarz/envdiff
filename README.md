# envdiff

Compare `.env` files across environments and report missing, extra, or mismatched keys — with optional secret masking.

---

## Installation

```bash
pip install envdiff
```

Or install from source:

```bash
git clone https://github.com/youruser/envdiff.git
cd envdiff && pip install -e .
```

---

## Usage

```bash
# Compare a base .env against a production env file
envdiff .env .env.production

# Mask secret values in the output
envdiff .env .env.staging --mask-secrets

# Output as JSON
envdiff .env .env.production --format json
```

**Example output:**

```
[MISSING]  DATABASE_URL        present in .env, missing in .env.production
[EXTRA]    DEBUG               present in .env.production, missing in .env
[MISMATCH] APP_PORT            .env=8000 | .env.production=80
```

You can also use `envdiff` as a library:

```python
from envdiff import compare

results = compare(".env", ".env.production", mask_secrets=True)
for diff in results:
    print(diff)
```

---

## Options

| Flag              | Description                          |
|-------------------|--------------------------------------|
| `--mask-secrets`  | Redact values in diff output         |
| `--format`        | Output format: `text` (default), `json` |
| `--ignore-keys`   | Comma-separated list of keys to skip |

---

## License

MIT © 2024 [youruser](https://github.com/youruser)