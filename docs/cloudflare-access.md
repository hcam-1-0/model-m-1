# Cloudflare Access for H-CAM GIS

H-CAM production API access is authenticated with Cloudflare Access. The API
requires the signed `Cf-Access-Jwt-Assertion`; browser-provided identity
headers are never accepted outside local development.

## Required H-CAM configuration

```text
HCAM_ENVIRONMENT=production
HCAM_CLOUDFLARE_ACCESS_ENABLED=true
HCAM_CLOUDFLARE_ACCESS_TEAM_DOMAIN=https://your-team.cloudflareaccess.com
HCAM_CLOUDFLARE_ACCESS_AUDIENCE=<Access application AUD tag>
HCAM_CLOUDFLARE_ACCESS_GROUP_MAPPING={"hcam-viewers":{"roles":["camera.viewer"],"departments":["traffic"]},"hcam-admins":{"roles":["platform.admin"],"departments":["*"]}}
```

The dashboard BFF and H-CAM API must be covered by the same Access application
or have an assertion audience that exactly matches this configuration. Configure
the identity provider so the Access JWT includes the required `groups` claim.
Use explicit role/department grants; unmatched groups have no H-CAM access.

H-CAM verifies the Access JWT signature using Cloudflare's published rotating
JWKS, then checks issuer, audience, expiry and token type before mapping any
groups. See [Cloudflare's origin validation guidance](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/).
