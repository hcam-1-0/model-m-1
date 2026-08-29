# Security Policy

## Reporting A Vulnerability

Do not open a public issue for vulnerabilities, credentials, private camera locators, or sensitive operational data. Use the repository's **Security → Report a vulnerability** flow to create a private security advisory:

https://github.com/hcam-1-0/model-m-1/security/advisories/new

Include a concise impact statement, affected commit or version, safe reproduction steps, and a suggested mitigation when available. Replace real identifiers and data with synthetic examples. Do not attach camera footage, government records, authentication material, or production database exports.

## Supported Code

Security fixes are prioritized for the `main` branch and any explicitly active integration branch. Experimental branches are supported only while their linked GitHub Project item remains active.

## Security Boundaries

- Authentication and authorization must fail closed.
- Camera egress is restricted to explicit allow-lists.
- Recording, analytics, camera control, and retention require explicit scope and review.
- Secrets belong in local ignored files or an approved secret store, never Git history or workflow YAML.
- Security test evidence must be sanitized before it is attached to an issue, pull request, release, or Actions artifact.

Maintainers will acknowledge a complete private report, assess severity and exposure, coordinate a fix, and publish only the minimum safe advisory information after remediation.
