# EVE-Healthcare
Backend service for diagnostic test bookings and simulated payments. Built with FastAPI, SQLAlchemy, and PostgreSQL — supports JWT auth, centre/test management, bookings, and a payment webhook designed to be idempotent so retried or duplicate events never corrupt booking state. Docker-ready.
