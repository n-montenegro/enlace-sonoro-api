# OWASP API Security Top 10 (2023) – Controls in Enlace Sonoro

Reference: OWASP API Security Project, *OWASP API Security Top 10 – 2023*
(https://owasp.org/API-Security/editions/2023/en/0x11-t10/).

We implemented **10 controls**, one for each risk of the list. Every control has code evidence
and at least one automated test.

| # | OWASP risk (2023) | Control implemented | Code evidence | Test |
|---|---|---|---|---|
| 1 | **API1 – Broken Object Level Authorization** | The profile endpoint does not receive a user id: the user is taken from the signed token, so nobody can read another user's profile. The LLM call log (questions of all users) is only visible to ADMIN. | `app/api/routers/auth.py` → `me()` · `app/api/routers/ai.py` → `list_calls` with `require_role(ADMIN)` | `test_user_endpoint_returns_own_profile`, `test_ai_answer_uses_catalog_context` |
| 2 | **API2 – Broken Authentication** | JWT signed with HS256 and a secret from `.env` (min. 32 chars), 30-minute expiration, algorithm pinned on decode (rejects `alg: none`). Passwords hashed with PBKDF2-SHA256, random salt and 600,000 iterations; constant-time comparison. Same error message for wrong user or wrong password. | `app/infrastructure/security/jwt_token_service.py` · `app/infrastructure/security/pbkdf2_hasher.py` · `app/application/auth_service.py` → `login()` | `test_expired_token_is_rejected`, `test_alg_none_token_is_rejected`, `test_hash_is_salted_and_verifiable`, `test_wrong_password_and_unknown_user_get_the_same_message` |
| 3 | **API3 – Broken Object Property Level Authorization** | Registration rejects unknown fields (`extra="forbid"`), so a client cannot send `"role": "ADMIN"` (mass assignment). Responses use `UserOut`, which never includes the password hash. | `app/api/routers/auth.py` → `RegisterRequest`, `UserOut` | `test_register_cannot_choose_role` |
| 4 | **API4 – Unrestricted Resource Consumption** | Rate limiting per client: login/register 5 req/min, AI assistant 10 req/min, open data 30 req/min (HTTP 429 + `Retry-After`). Field length limits with Pydantic and timeouts on every external call. | `app/api/rate_limit.py` · `app/main.py` → `app.state.limiters` | `test_login_is_rate_limited`, `test_rate_limiter_blocks_and_then_recovers` |
| 5 | **API5 – Broken Function Level Authorization** | Role-based access control (RBAC): create, update and delete songs, `/admin/stats` and `/ai/calls` require ADMIN; a USER gets 403. | `app/api/security.py` → `require_role()` · `app/api/routers/songs.py` → `ADMIN_ONLY` | `test_admin_endpoint_rejects_user_and_accepts_admin`, `test_user_can_read_but_not_modify_the_catalog` |
| 6 | **API6 – Unrestricted Access to Sensitive Business Flows** | The AI assistant is a costly business flow (each call to Gemini costs money): it requires login and has its own request limit, independent from Gemini's limit. | `app/api/routers/ai.py` → `dependencies=[require_role(USER), limit("ai")]` | `test_ai_requires_token`, `test_ai_has_its_own_request_limit` |
| 7 | **API7 – Server Side Request Forgery (SSRF)** | External URLs are constants in the code; no user input is used to build a URL or the search term sent to DANE. | `app/infrastructure/opendata/datos_gov_client.py` → `DIVIPOLA_URL` · `dane_client.py` → `DANE_CATALOG_URL`, `search_term` | `test_divipola_returns_records_and_sends_limit`, `test_dane_reads_rows_inside_result` |
| 8 | **API8 – Security Misconfiguration** | CORS restricted to an allow-list from `.env`; security headers (`nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Cache-Control: no-store`); secrets only in `.env`; generic error messages (internal details go to the server log only). | `app/main.py` → `SECURITY_HEADERS`, `CORSMiddleware`, `jwt_secret()` · `app/api/routers/opendata.py` → `UNAVAILABLE_MESSAGE` | `test_security_headers_are_present`, `test_cors_only_allows_known_origins`, `test_503_does_not_leak_internal_error_details` |
| 9 | **API9 – Improper Inventory Management** | All endpoints are versioned (`/api/v1`) and documented with OpenAPI; the interactive docs can be turned off in production with `ENABLE_DOCS=false`. | `app/main.py` → `docs_url=...` | `test_docs_can_be_disabled_in_production` |
| 10 | **API10 – Unsafe Consumption of APIs** | Data from datos.gov.co and DANE is treated as untrusted: timeouts, retry with exponential backoff, circuit breaker (CLOSED/OPEN/HALF_OPEN), only the expected part of the JSON is read, and SQL uses parameterized queries. | `app/infrastructure/resilience/circuit_breaker.py` · `app/infrastructure/opendata/http_source.py` · `sqlite_*_repository.py` (`VALUES (?, ...)`) | `test_three_failed_fetches_open_the_circuit`, `test_retries_after_503_and_connection_error` |

## How to try it (Swagger UI)

1. Create the first administrator: `python scripts/create_user.py admin ADMIN` (the password is typed hidden).
2. Start the API and open `http://127.0.0.1:8000/docs`.
3. Click **Authorize**, type the username and password, and click **Authorize** again.
4. `GET /api/v1/auth/me` (USER test endpoint) and `GET /api/v1/admin/stats` (ADMIN test endpoint).
5. Register a normal account with `POST /api/v1/auth/register`, log in with it and try `GET /api/v1/admin/stats`: the answer is **403 Forbidden**.
