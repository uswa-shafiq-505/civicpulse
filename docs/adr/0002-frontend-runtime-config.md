# ADR-0002: Frontend runtime configuration — same-origin `/api` proxy, no baked-in URL

Status: Accepted · Date: <today> · Deciders: <both names>

## Context
Vite replaces `import.meta.env.*` with literals at build time. If the API URL is baked in, the image is
environment-specific and build-once-deploy-many is broken for the frontend.

## Options considered
| Option | Pros | Cons |
|---|---|---|
| A. `VITE_API_URL` at build time | Trivial | One image per environment; rebuild to change URL — rejected |
| B. `/config.js` generated from env at container start | Works with any absolute backend URL; supports cross-origin APIs | Needs entrypoint templating, CORS config, one more moving part |
| C. nginx proxies `/api` → `backend` (relative URLs) | Frontend needs *no* URL; no CORS; same nginx.conf works in Compose and Kubernetes because the Service is also named `backend`; browser never sees backend hostname | Backend must be reachable from the nginx pod; long-running requests need proxy timeouts set |

## Decision
Option C. `frontend/src/api/client.ts` uses `BASE = '/api'` (relative). `frontend/nginx.conf` `location /api/`
proxies to `http://backend:8000`. In Kubernetes the Ingress also routes `/api` directly to the backend Service.

## Consequences
- One image runs on a laptop, in CI, and on the cluster. Nothing to inject, nothing secret in the bundle.
- The backend's client-IP rate limiter must trust `X-Forwarded-For` from the proxy (see backend `--proxy-headers`),
  otherwise every user shares nginx's IP.
- If we ever host the API on a different origin, we add Option B without breaking existing deployments.