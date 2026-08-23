# Controlled Private-Camera Validation

This optional harness validates metadata against one camera that the operator
owns or is explicitly authorized to test. It is disabled by default, forbidden
in production, never runs in CI, and performs no image capture, recording,
stream download, host scan, or WS-Discovery.

## Prerequisites

- Use an isolated lab VLAN or directly controlled private network.
- Obtain written authorization and confirm the test is metadata-only.
- Prefer camera HTTPS with a verified certificate or configured private CA.
- Add one exact egress rule for the device service's scheme, host/IP, port, and
  approved private address range.
- Use the file secret provider only for this local development test.

Create an untracked credential file below an ACL-restricted secret root:

```json
{"username":"lab-user","password":"replace-locally"}
```

Create an untracked manifest:

```json
{
  "version": 1,
  "authorization": {
    "owned_or_authorized": true,
    "operator": "authorized-operator",
    "scope": "metadata-only"
  },
  "camera": {
    "stream_id": "str_00000000000000000000000000000001",
    "camera_id": "private-lab-camera-01",
    "locator": "https://camera.lab.example:443/onvif/media_service",
    "protocol": "https",
    "management_locator": "https://camera.lab.example:443/onvif/device_service",
    "onvif_auth_mode": "wsse_password_digest",
    "secret_ref": "camera-01.json"
  }
}
```

Set the local-only controls and run:

```powershell
$env:HCAM_ENVIRONMENT = "development"
$env:HCAM_PRIVATE_CAMERA_LAB_ENABLED = "true"
$env:HCAM_CAMERA_SECRET_PROVIDER = "file"
$env:HCAM_CAMERA_SECRET_ROOT = "C:\path\to\restricted-secrets"
$env:HCAM_ONVIF_EGRESS_RULES_FILE = "C:\path\to\onvif-egress.json"
$env:HCAM_ONVIF_CA_BUNDLE = "C:\path\to\private-ca.pem"
python tools/phase2_private_camera.py C:\path\to\private-camera.json
```

For a device that supports only HTTP, set
`HCAM_ONVIF_LAB_HTTP_ENABLED=true` in development and include an exact HTTP
rule. Never use that exception in production.

The output contains normalized capability metadata and explicit false flags
for image capture, recording, and network discovery. It does not print the
management locator, media locator, secret reference, username, or password.

This repository's automated evidence validates the harness synthetically. No
physical-camera validation is claimed until an owner supplies an authorized
camera and records the controlled test result outside source control.
