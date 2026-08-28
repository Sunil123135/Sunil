# moneycontrol-gemini-proxy

Cloudflare Worker that proxies requests to the Google Generative Language (Gemini) API.

Connected to this repository via **Cloudflare Workers Builds**. The worker name in
`wrangler.toml` must match the Worker name in the Cloudflare dashboard.

## Secrets

Configure in Cloudflare → Worker → Settings → Variables:

| Secret | Required | Purpose |
|--------|----------|---------|
| `GEMINI_API_KEY` | Yes | Google AI / Generative Language API key |
| `GEMINI_PROXY_KEY` | No | If set, clients must send `Authorization: Bearer <key>` |

## Local development

```bash
npm install
npx wrangler dev
```

## Deploy

Cloudflare Workers Builds deploys automatically on push when Git integration is enabled.
