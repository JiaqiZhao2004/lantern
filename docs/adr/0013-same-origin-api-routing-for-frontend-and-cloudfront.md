# Same-Origin API Routing For Frontend And CloudFront

The frontend now treats `/api/v1` as its internal API base path and only uses `VITE_BACKEND_HOST` to point development traffic at a local backend. In production, the browser talks to the same origin as the app, and CloudFront is responsible for routing `/api/*` requests to the backend tunnel while all other paths stay on the static frontend origin. We chose this over a separate public API hostname so the app can avoid CORS complexity and keep backend routing as an edge concern instead of a frontend concern.
