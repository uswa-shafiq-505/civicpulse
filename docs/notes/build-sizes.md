# Build sizes

## Frontend (civicpulse-frontend:dev)
- Final image size: 74.2 MB (disk usage); 21.1 MB compressed content
- Base image: nginx:1.27-alpine accounts for ~50 MB of this
- Multi-stage confirmed: no Node, no source, no node_modules in final image
  - `docker run --rm --entrypoint sh civicpulse-frontend:dev -c "which node"` → empty
  - `docker run --rm --entrypoint sh civicpulse-frontend:dev -c "ls /app"` → No such file or directory
- Runs as non-root: uid=101(nginx) gid=101(nginx)
- Build context with .dockerignore: 232.77 kB (first uncached build) / 1.28 kB cached

## Backend
(fill in after you measure the backend image the same way — Step 5.4 of the guide)