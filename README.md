# MindBridge AI — runnable foundation

A full-stack starter for the MindBridge AI web platform:
- HTML/CSS/vanilla JavaScript frontend
- FastAPI backend
- PostgreSQL database
- JWT authentication and role-based access
- Profile creation/listing with organization scoping
- Docker Compose development environment

This is a secure-minded foundation, **not a clinically validated or production-approved healthcare system**.
Use synthetic data only until privacy, security, legal and professional reviews are complete.

## Requirements
- Docker Desktop + Docker Compose
- VS Code
- (Optional) Python 3.11+ for running the backend outside Docker

## Run
1. Copy `.env.example` to `.env`.
2. Replace `SECRET_KEY` with a long random secret before running.
3. From this folder run:

   ```bash
   docker compose up --build
   ```

4. Open http://localhost:8000
5. API documentation: http://localhost:8000/docs

The first account can be registered at the UI. For this development starter, the first registered account becomes `platform_admin`; subsequent accounts become `professional`.
Do not expose this bootstrap behavior publicly. Replace it with invitation-based onboarding before deployment.

## Demo flow
1. Register an account.
2. Log in.
3. Create a fictional profile.
4. View the profile in the dashboard.

## Important limitations
- No real clinical diagnosis, treatment recommendation or automated clinical decision-making.
- AI features are intentionally not connected yet. Add a provider only after privacy review, data minimization, retention controls and appropriate contracts.
- Consent records, comprehensive audit coverage, account recovery, email verification, rate limiting, backups, monitoring, penetration testing and formal tenant-isolation testing are required before real deployment.
- This starter uses a simple role model. A production system needs relationship- and purpose-based permissions, granular field visibility and revocation workflows.
