# Project Standards — Order Intelligence Agent Platform

## Project Overview

AI-Powered Order Intake & Order Entry Automation platform for Transportation & Logistics. Monitors email inbox, extracts order data via AI agents, validates against business rules, and creates orders automatically. Includes a web-based Order Entry Application with HITL workflows.

## Tech Stack

### Backend (Agents + API)
- **Language:** Python 3.12
- **Framework:** FastAPI (async) for API; standalone async services for agents
- **ORM / DB:** SQLAlchemy 2.0 (async) + Alembic migrations
- **Database:** PostgreSQL 16 with pgvector extension
- **Models:** Pydantic v2 for all data models and validation
- **LLM:** Anthropic Claude via `anthropic` SDK (local) or AWS Bedrock (cloud)
- **OCR:** pdfplumber + pytesseract (local) or AWS Textract (cloud)
- **Queue:** ElasticMQ locally, Amazon SQS in cloud (accessed via boto3)
- **Storage:** MinIO locally, Amazon S3 in cloud (accessed via boto3)
- **Email:** MailHog locally (SMTP), AWS SES in cloud
- **Cache:** Redis 7

### Frontend
- **Framework:** React 18 with TypeScript (strict mode)
- **Build:** Vite
- **Styling:** Tailwind CSS v3
- **Data Fetching:** React Query v5 (TanStack Query)
- **Routing:** React Router v6
- **Charts:** Recharts
- **PDF Viewer:** PDF.js
- **Rich Text:** TipTap

### Infrastructure
- **Local:** Docker Compose (postgres, redis, elasticmq, minio, mailhog)
- **Cloud:** AWS (ECS Fargate, RDS, ElastiCache, SQS, S3, SES, EventBridge, Cognito, CDK)
- **IaC:** AWS CDK (TypeScript)

## Architecture Principles

1. **Adapter pattern for all infrastructure:** Agent code depends only on abstract interfaces (`QueueAdapter`, `StorageAdapter`, `LLMAdapter`, `OCRAdapter`, `EmailSender`, `EventBusAdapter`). Implementations swap via `ADAPTER_MODE=local|aws` env var.
2. **Service-per-domain:** Agents are independent async services consuming from dedicated queues. API is a single FastAPI service with domain-separated routers.
3. **Event-driven:** Agents communicate via queues (SQS/ElasticMQ). Order lifecycle events published to EventBridge (or local async pub/sub).
4. **Immutable audit trail:** `audit_logs` and `order_history` tables are append-only. Never issue UPDATE or DELETE on these tables.

## Coding Standards

### Python
- Use `async`/`await` throughout — no blocking I/O in agent or API code
- Type hints on all function signatures; `mypy --strict` must pass
- Format with `black` (line length 100); sort imports with `isort`
- Lint with `ruff`
- Pydantic v2 models for all external data boundaries (API input/output, queue messages, DB records)
- Structured JSON logging via custom logger; always include `run_id`, `email_id`, `order_id` context fields
- Never log PII (emails, phone numbers, names) in plain text — use PII masker utility
- Handle errors explicitly: retry with backoff for transient failures; route to DLQ/HITL for persistent failures
- Test with `pytest` + `pytest-asyncio`; use `testcontainers` for integration tests

### TypeScript / React
- Strict TypeScript (`strict: true` in tsconfig)
- Functional components only; hooks for all state management
- React Query for all server state; no manual `useEffect` for data fetching
- Zod for runtime validation of API responses
- Component files: PascalCase (e.g., `OrderDetail.tsx`); utility files: camelCase
- No `any` types — use `unknown` and narrow with type guards
- Tailwind for styling — no CSS modules or styled-components
- Test with Vitest + React Testing Library; E2E with Playwright

### API Design
- RESTful; all responses JSON with standard envelope `{data, total_count, total_pages, page, limit}` for lists
- Errors: `{error: {code, message, field?, details?}}`
- Pagination: `?page=1&limit=25` on all list endpoints
- Auth: JWT Bearer token on all protected endpoints
- RBAC: role hierarchy `readonly < agent < supervisor < admin`; enforce via `@require_role()` decorator
- Versioned: `/api/v1/` prefix

### Database
- UUIDs for all primary keys (`gen_random_uuid()`)
- Timestamps always `TIMESTAMPTZ` (stored in UTC)
- JSONB for flexible nested structures (addresses, time windows, confidence scores)
- Indexes on all foreign keys and frequently filtered columns
- Alembic for all schema changes — never modify DB directly

## Monorepo Structure

```
/
├── packages/
│   ├── agents/          # Python — 6 AI agents + runner
│   ├── api/             # Python FastAPI backend
│   ├── frontend/        # React 18 + TypeScript + Vite
│   └── shared/          # Shared code
│       ├── python/      # Pydantic models, adapters, utils
│       └── typescript/  # Types, Zod schemas, constants
├── infrastructure/
│   ├── docker/          # Dockerfiles
│   └── cdk/             # AWS CDK stacks
├── scripts/             # Seed data, demo runners, utilities
├── test-emails/         # .eml fixtures for local testing
├── docker-compose.yml
├── .env.example
├── .env.local
└── Makefile
```

## Key Design Decisions

- **Confidence thresholds are configurable at runtime** (stored in DB, loaded by Validation Agent on each run) — never hardcode threshold values
- **Order numbers:** format `ORD-YYYYMMDD-XXXXX` with daily-reset PostgreSQL sequence
- **Duplicate detection:** composite DB query + pgvector cosine similarity (threshold 0.92)
- **Customer communication:** always maintain email thread via `In-Reply-To` / `References` headers
- **All agent actions logged** to `agent_execution_logs` with token usage and duration

## Reference Files

- #[[file:.kiro/specs/order-intelligence-agent/requirements.md]]
- #[[file:.kiro/specs/order-intelligence-agent/design.md]]
- #[[file:.kiro/specs/order-intelligence-agent/tasks.md]]
