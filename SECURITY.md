# Security Policy

## Reporting A Vulnerability

Do not disclose a vulnerability, credential, private endpoint, exploit detail,
or sensitive evidence in a repository issue, pull request, discussion, commit,
test fixture, screenshot, or log.

Contact the `hcam-1-0` organization owners through the private team channel
already established with collaborators. Include only:

- the affected repository, branch, and commit;
- a concise impact and affected component;
- a minimal reproduction using synthetic data when possible;
- recommended containment or rollback;
- whether any secret, private data, camera, provider, or external system may be
  affected.

Do not include actual secret values, private media, Government data, personal
data, or unrestricted URLs. Rotate or revoke exposed credentials through their
own approved operational process; never place replacement credentials in Git.

## Research Boundary

Permission to read this repository is not authorization to test external
services, Sentinel environments, cameras, providers, networks, accounts, or
Government systems. Security validation must stay within generated fixtures
and explicitly owned, authorized environments.

## Maintainer Response

Maintainers should acknowledge the report privately, record a sanitized risk
item, contain exposure, preserve relevant audit evidence, define a bounded fix,
validate the fix, and coordinate disclosure only with authorized parties. Do
not close a security item solely because exploitation was not reproduced.

## Supported Version

Security fixes target the current `main` branch unless a maintainer explicitly
identifies another supported branch. Older snapshots and unmerged branches may
not receive fixes automatically.
