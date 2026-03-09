# Redis Integration Task Note

## Objective
Integrate Redis (free plan) into the backend for rate limiting, caching, and potentially JWT denylisting.

## Current State
- Backend runs on FastAPI with PostgreSQL (`asyncpg`, `SQLModel`).
- No KV store is currently used.
- Project uses layered architecture (Routers → Services → Models) as per `backend-dev-guidelines`.

## Plan
1.  **Infrastructure Setup**:
    -   Add `redis` and `slowapi` (for FastAPi rate limiting) to `backend/requirements.txt`.
    -   Update `backend/.env.example` and `backend/app/config.py` to include `REDIS_URL`.
    -   Set up Redis client in `backend/app/database.py` (or a dedicated `redis.py` module).

2.  **Rate Limiting Implementation**:
    -   Configure `slowapi` in `backend/app/main.py`.
    -   Apply rate limiting globally or on specific endpoints (e.g., login, create post) using a Redis backend.

3.  **Caching (Optional/Future)**:
    -   Identify endpoints suitable for caching (e.g., public GET endpoints).
    -   Implement caching logic in the service layer using the Redis client.

4.  **JWT Denylist (Optional/Future)**:
    -   Update auth flow to add tokens to Redis upon logout.
    -   Check Redis for token validity on authenticated routes.

5.  **Testing**:
    -   Ensure `pytest` can mock or use a test Redis instance.
    -   Write tests for rate limiting behavior.
