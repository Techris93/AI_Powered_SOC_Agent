# Security Assessment and Remediation

Date: 2026-03-13
Scope: FastAPI backend, static frontend, Python dependency set, Firebase hosting configuration

## Executive Summary

- High-risk misconfigurations in API exposure were identified and remediated.
- The final AI dependency risk was removed by replacing the LangChain integration with direct OpenAI SDK calls.
- `pip-audit` now reports no known vulnerabilities in the environment.

## Findings and Actions

### High: Overly Permissive CORS Policy

- Risk: `allow_origins=["*"]` with broad methods/headers increased cross-origin abuse risk.
- Remediation:
  - Restricted origins to environment-configured allowlist (`CORS_ALLOW_ORIGINS`).
  - Restricted methods and allowed headers.
  - Disabled credentialed wildcard behavior.
- Status: Fixed.

### High: Missing API Security Headers

- Risk: Reduced browser-side hardening against MIME sniffing and clickjacking.
- Remediation:
  - Added middleware to set `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy`.
- Status: Fixed.

### High: No Access Control Guard on API Endpoints

- Risk: All API endpoints were accessible without any shared secret gate.
- Remediation:
  - Added optional API key enforcement via `SOC_AGENT_API_KEY` for all `/api` routes.
  - Requests without matching `X-API-Key` now return `401 Unauthorized` when enabled.
- Status: Fixed (optional, disabled unless env var is set).

### Medium: Information Leakage Through Raw Exception Messages

- Risk: Internal error details were exposed in HTTP responses.
- Remediation:
  - Replaced raw exception exposure with generic user-facing errors.
  - Added server-side logging for diagnostics.
- Status: Fixed.

### Medium: Weak Request Validation

- Risk: Insufficient bounds and format checks on key request models and query parameters.
- Remediation:
  - Added strict model constraints with `Field` and validators.
  - Added URL validation and HTTPS enforcement for non-local Elasticsearch hosts.
  - Added bounded list/query limits to reduce abuse surface.
- Status: Fixed.

### Medium: Known Vulnerable Dependency Versions

- Initial state: 15 vulnerabilities across FastAPI, Starlette, python-multipart, aiohttp, langchain-core.
- Remediation applied:
  - `fastapi` upgraded to `0.135.1`
  - `starlette` pinned to `0.49.1`
  - `python-multipart` upgraded to `0.0.22`
  - `aiohttp` upgraded to `3.13.3`
  - `urllib3` pinned to `2.6.3`
  - Virtualenv tooling upgraded to `pip 26.0.1` and `setuptools 78.1.1`
  - LangChain packages removed and AI orchestration rewritten against the OpenAI SDK
- Current state: no known vulnerabilities found by `pip-audit`.
- Status: Fixed.

## Verification Performed

- Backend startup validated successfully.
- API health endpoint checks successful (`/docs`, `/api/dashboard/stats`).
- Dependency audit executed with `pip-audit` before and after remediation.
- Final `pip-audit` result: `No known vulnerabilities found`.

## Hardening Variables Added

- `CORS_ALLOW_ORIGINS`
- `ALLOWED_HOSTS`
- `SOC_AGENT_API_KEY`

Example:

```env
CORS_ALLOW_ORIGINS=http://localhost:8000,https://your-frontend-domain
ALLOWED_HOSTS=localhost,127.0.0.1,your-api-domain
SOC_AGENT_API_KEY=replace-with-long-random-secret
```
