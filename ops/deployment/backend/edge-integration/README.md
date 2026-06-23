# Backend Edge Integration

This component owns Slice 4: routing production frontend API traffic from `lantern.royzhao.dev` through CloudFront to the tunnel-backed backend.

## Target Shape

- browsers call `https://lantern.royzhao.dev/api/*`
- CloudFront routes `/api/*` to `https://lantern-api.royzhao.dev` over HTTPS only
- `lantern-api.royzhao.dev` remains the backend origin hostname
- Cloudflare Access protects `lantern-api.royzhao.dev` from ordinary public requests
- CloudFront authenticates to Cloudflare Access with service-token headers

## Terraform Scope

Implement this in `ops/terraform/lantern-hosting/` so the frontend distribution and backend origin protection are reviewed together:

- Cloudflare Access application for `lantern-api.royzhao.dev`
- Cloudflare Access policy allowing the CloudFront service token
- Cloudflare Access service token
- CloudFront backend origin for `lantern-api.royzhao.dev`
- CloudFront ordered cache behavior for `/api/*`

The Cloudflare Access service token secret will be stored in Terraform state because CloudFront needs it as an origin custom header. Keep the token narrowly scoped to this backend origin and rotate it if exposed.

## API Behavior

The `/api/*` CloudFront behavior should:

- preserve the full viewer request URI without rewriting `/api`
- allow `GET`, `HEAD`, `OPTIONS`, `PUT`, `POST`, `PATCH`, and `DELETE`
- disable caching
- forward all query strings
- forward the `Authorization` header
- not forward cookies unless the backend gains a cookie-based need

Do not expand production CORS for Slice 4. The browser-facing production API is same-origin through `lantern.royzhao.dev`, so CORS should stay limited to the local development path unless a real cross-origin workflow is introduced later.

## Validation

Slice 4 should validate the real production user path rather than adding a public health endpoint on `lantern.royzhao.dev`.

Apply Cloudflare Access protection and CloudFront `/api/*` routing in one Terraform change. Access-first would intentionally break the direct proof endpoint before CloudFront can use it, and CloudFront-first would leave the origin publicly reachable longer than necessary.

Required checks:

- direct unauthenticated requests to `https://lantern-api.royzhao.dev/health/ready` are blocked by Cloudflare Access
- CloudFront can reach the backend origin through the Access service token
- `https://lantern.royzhao.dev/api/v1/...` reaches the backend through CloudFront
- an authenticated production API request succeeds with a Firebase bearer token
