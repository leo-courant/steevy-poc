Place Thales-related non-code assets here (not committed in repository):

- `genai.tatm.thales.crt` — TLS CA bundle for your Thales deployment. DO NOT
  commit the certificate file. Copy it here on the host where you run the app.

- `tiktoken_cache/` — Local cache for tiktoken. This folder is safe to keep
  (it stores cached tokenization artifacts), but large caches may be ignored
  by your VCS. The path is set by `config.settings.tiktoken_cache_dir`.

How to configure the API key and endpoint (example .env entries):

```
# .env (local, never committed)
THALES_BASE_URL=https://your-thales-host.example.com/v1
THALES_API_KEY=sk-...   # keep secret
```

The project reads `settings.thales_base_url` and `settings.thales_api_key`.
Populate them via environment variables or a local `.env` file.
