<<<<<<< HEAD
# EVE Healthcare — Diagnostic Booking & Payments API

A backend service for booking diagnostic tests and simulating payments,
built with **FastAPI**, **SQLAlchemy**, and **PostgreSQL**.

## Tech stack

- FastAPI (API layer, validation, OpenAPI docs)
- SQLAlchemy 2.0 (ORM)
- PostgreSQL 18
- python-jose (JWT auth) + passlib/bcrypt (password hashing)
- Docker & docker-compose (containerized local setup)

## Running the project

There are two ways to run this locally. Docker is the recommended path —
it avoids any local Python/PostgreSQL version issues entirely and is the
easiest way to evaluate the project on a fresh machine.

### Option A: Docker (recommended)

Prerequisites: Docker Desktop installed and running.

git clone <this-repo-url>
cd eve-backend
docker compose up --build

This will:
- Build the API image (Python 3.14)
- Start a PostgreSQL 18 container and wait until it's healthy
- Start the API, which creates all tables automatically on startup

The API is now available at http://localhost:8000, with interactive docs
at http://localhost:8000/docs.

To stop everything:
docker compose down

To also wipe the database and start completely fresh:
docker compose down -v

### Option B: Run locally without Docker

Prerequisites:
- Python 3.11+ (3.14 also works — see the version note below)
- A running PostgreSQL instance

1. Create the database

psql -U postgres -c "CREATE USER eve_user WITH PASSWORD 'eve_pass';"
psql -U postgres -c "CREATE DATABASE eve_db OWNER eve_user;"

(Or create the eve_user login role and eve_db database, owned by
eve_user, via pgAdmin's GUI instead — either works.)

2. Create a virtual environment and install dependencies

python -m venv venv
source venv/bin/activate   (Windows: venv\Scripts\Activate.ps1)
pip install -r requirements.txt

3. Configure environment variables

cp .env.example .env
(edit .env if your DB credentials / JWT secret differ)

4. Run the server

uvicorn app.main:app --reload

Tables are created automatically on startup. The API is now available at
http://localhost:8000, with docs at http://localhost:8000/docs.

A note on Python versions: this project was developed and tested on
Python 3.14. A few dependency versions in requirements.txt are pinned
specifically because older versions don't ship prebuilt wheels for 3.14 and
fail to build from source (pydantic/pydantic-core needs >=2.12.2,
psycopg2-binary needs >=2.9.12, and bcrypt needs to stay at 4.0.1
since passlib 1.7.4 breaks against newer bcrypt releases). If you're on
Python 3.11–3.12, these same pins still work fine.

## API endpoints & example requests

### Auth

Sign up
POST /auth/signup
{ "email": "patient@example.com", "password": "supersecret123" }

Log in (form-encoded, per OAuth2 password flow — username = email)
POST /auth/login
Content-Type: application/x-www-form-urlencoded
username=patient@example.com&password=supersecret123

-> { "access_token": "...", "token_type": "bearer" }

Use the token as Authorization: Bearer <token> on all endpoints below marked (auth).

### Diagnostic centres & tests

POST /centres/                      (auth)   { "name": "CityLab", "location": "Bengaluru" }
GET  /centres/                               list all centres with their tests
GET  /centres/{centre_id}                    single centre with its tests
POST /centres/{centre_id}/tests     (auth)   { "name": "CBC", "price": 499.0 }
GET  /tests/?centre_id=1                     list tests, optionally filtered by centre

### Bookings

POST /bookings/                     (auth)   { "test_id": 1, "appointment_time": "2026-10-01T10:00:00" }
GET  /bookings/                     (auth)   list the current user's bookings
GET  /bookings/{booking_id}         (auth)   fetch a single booking (owner only)
POST /bookings/{booking_id}/cancel  (auth)   cancel a booking (owner only, blocked if already CONFIRMED)

A new booking starts in PENDING status.

### Payments (simulated)

POST /payments/                     (auth)   { "booking_id": 1 }

Simulates a payment attempt for a PENDING booking. Resolves immediately to
SUCCESS or FAILED (weighted by PAYMENT_SUCCESS_RATE), updates the
booking to CONFIRMED or FAILED, and returns a provider_reference that a
webhook can later refer back to.

POST /payments/webhook/
{
  "event_id": "evt_123",
  "booking_id": 1,
  "provider_reference": "...optional, from a prior /payments/ call...",
  "status": "SUCCESS"
}

Simulates an asynchronous status push from a payment provider.
Idempotent by design: every processed event is recorded by its
event_id; a repeated delivery of the same event_id is detected and
short-circuited (no duplicate payment rows, no re-applied booking state).

## Database / schema design

- users — auth accounts.
- diagnostic_centres — a centre (name, location).
- diagnostic_tests — belongs to a centre; carries its own price.
- bookings — belongs to a user, references a test and (denormalized)
  its centre_id for cheap querying; snapshots amount from the test price
  at booking time (so a later price change doesn't retroactively change past
  bookings); status is one of PENDING / CONFIRMED / FAILED / CANCELLED.
- payments — one row per payment attempt on a booking (a booking can
  have more than one, e.g. a failed attempt followed by a retry). Carries a
  unique provider_reference so a webhook can match it back to a specific
  attempt.
- webhook_events — append-only idempotency ledger, keyed by the provider's
  event_id. This is the mechanism that makes /payments/webhook/ safe to
  call more than once.

## Important assumptions

- Anyone with a valid JWT can create centres/tests (no separate admin role).
  In a real system these would be gated behind an admin/staff permission —
  called out here rather than built, to keep scope tight.
- POST /payments/ resolves the outcome synchronously (rather than only
  returning a "pending" state and waiting for the webhook) so the API is
  fully exercisable without standing up an external caller. The webhook path
  is still fully implemented and idempotent, since a provider retrying
  delivery of the same event is the realistic failure mode being tested,
  independent of which endpoint originates the first update.
- A CONFIRMED (paid) booking cannot be cancelled or paid for again; a
  CANCELLED booking cannot be paid for, and a late webhook for it is
  recorded (so retries of that event are still idempotent) but never flips
  its status back.
- Tables are created via Base.metadata.create_all rather than Alembic
  migrations, to keep local setup to one command for this assignment.
- The Docker Postgres and any local (non-Docker) Postgres install are
  entirely separate databases — running one doesn't populate the other.

## What I'd improve with more time

- Tests. This submission does not include an automated test suite.
  Given more time, the first priority would be unit tests for the webhook
  idempotency logic specifically (repeated event_id, out-of-order
  delivery, webhook arriving for a cancelled booking), since that's the
  highest-risk piece of business logic, plus integration tests for the
  auth → booking → payment happy path.
- Alembic migrations instead of create_all, plus a proper admin role for
  managing centres/tests.
- Move the "resolve payment outcome" step out of POST /payments/ and into
  a background job, with /payments/ only enqueueing it — closer to how a
  real gateway integration behaves — plus retry/backoff handling on the
  webhook consumer side.
- Rate limiting on /auth/login and structured logging around the payment
  and webhook paths, since those are the endpoints most worth auditing.
- Swagger/OpenAPI docs already come for free from FastAPI at /docs; would
  add richer example payloads and response schemas per endpoint.
=======
# EVE-Healthcare
Backend service for diagnostic test bookings and simulated payments. Built with FastAPI, SQLAlchemy, and PostgreSQL — supports JWT auth, centre/test management, bookings, and a payment webhook designed to be idempotent so retried or duplicate events never corrupt booking state. Docker-ready.
>>>>>>> 042ac52c28d3e1db2857fac81a942639ca7e2501
