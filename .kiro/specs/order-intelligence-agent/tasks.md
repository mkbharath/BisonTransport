# Tasks - AI-Powered Order Intake & Order Entry Automation Platform

**Version:** 1.0
**Date:** June 2026

---

## Overview

Implementation is organized into 7 phases. **Phase 0 is a local prototype** — the entire platform runs on your laptop with Docker Compose and local service substitutes, no AWS account needed. Once the AI pipeline and UX are validated locally, Phases 1-6 lift the system to AWS for production-grade deployment.

| Phase | Focus | Outcome |
|---|---|---|
| 0 | Local Prototype (Docker Compose) | Full pipeline running locally; all 8 demos executable on laptop |
| 1 | AWS Infrastructure and Data Foundation | AWS resources, DB schema, cloud deployment |
| 2 | AI Agent Pipeline (Cloud) | All 6 agents on ECS Fargate with real SQS/S3/Bedrock |
| 3 | Order Entry Application - Core | Dashboard, Order Mgmt, Inbox, Validation Queue |
| 4 | Order Entry Application - Full | Communications Center, Audit Logs, Administration |
| 5 | Security, Observability and Performance | Auth, RBAC, monitoring, load testing |
| 6 | QA, Demo Preparation and PoC Sign-Off | All 8 demos, acceptance criteria, UAT |

---

## Phase 0 - Local Prototype (Docker Compose)

**Goal:** Run the entire platform on your laptop with zero AWS dependencies. Validate the AI agent pipeline, UX, and all 8 demo scenarios locally before investing in cloud infrastructure. Uses a service adapter pattern so the code lifts cleanly to AWS later.

### Task 0.1 - Monorepo Scaffold and Local Development Tooling
- Initialize monorepo structure:
  ```
  /
  ├── packages/
  │   ├── agents/          # Python 3.12 — all 6 AI agents
  │   ├── api/             # Python FastAPI backend
  │   ├── frontend/        # React 18 + TypeScript + Vite
  │   └── shared/          # Shared Python models + TypeScript types
  ├── infrastructure/
  │   ├── docker/          # Dockerfiles for each service
  │   └── cdk/             # AWS CDK (empty until Phase 1)
  ├── docker-compose.yml   # Full local stack
  ├── .env.example         # All environment variables (no secrets)
  ├── .env.local           # Local development defaults
  └── Makefile             # Common commands: up, down, logs, seed, test
  ```
- Configure `pyproject.toml` with Poetry or uv: Python 3.12, shared dev dependencies (pytest, black, isort, mypy, ruff)
- Configure root `package.json` for frontend: Vite, TypeScript, ESLint, Prettier
- Set up pre-commit hooks: lint + type-check on staged files
- **Acceptance:** `make up` starts all containers; `make test` runs unit tests; repo structure matches above

### Task 0.2 - Docker Compose Full Stack
- Write `docker-compose.yml` with these services:

| Service | Image / Build | Ports | Purpose |
|---|---|---|---|
| `postgres` | `pgvector/pgvector:pg16` | 5432 | Primary database with pgvector extension |
| `redis` | `redis:7-alpine` | 6379 | Cache, session store, queue state |
| `elasticmq` | `softwaremill/elasticmq-native` | 9324, 9325 | SQS-compatible message queue |
| `minio` | `minio/minio` | 9000, 9001 | S3-compatible object storage |
| `mailhog` | `mailhog/mailhog` | 1025, 8025 | SMTP capture with web UI |
| `api` | Build from `packages/api` | 8000 | FastAPI backend |
| `agents` | Build from `packages/agents` | — | All 6 agents (single container, multi-process) |
| `frontend` | Build from `packages/frontend` | 5173 | Vite dev server with HMR |

- Configure `elasticmq.conf` with all 7 queues: `document-processing`, `extraction`, `validation`, `auto-process`, `hitl`, `communication`, `exception` (each with a DLQ)
- Configure MinIO startup script to create buckets: `attachments`, `extracted-text`, `exports`
- Add `healthcheck` to all services; `api` depends on `postgres` + `redis` + `elasticmq` + `minio`
- Write `.env.local` with all configuration defaults
- **Acceptance:** `docker compose up` starts all services healthy within 60 seconds; MinIO console at localhost:9001; MailHog UI at localhost:8025; ElasticMQ dashboard at localhost:9325

### Task 0.3 - Service Adapter Pattern (Pluggable Infrastructure)
- Implement adapter interfaces in `packages/shared/python/adapters/`:
  ```python
  class QueueAdapter(ABC):      # publish_message(), consume_messages()
  class StorageAdapter(ABC):    # upload_file(), download_file(), get_presigned_url()
  class EmailSender(ABC):       # send_email()
  class LLMAdapter(ABC):        # complete(), classify()
  class OCRAdapter(ABC):        # extract_text(), extract_tables()
  class EventBusAdapter(ABC):   # publish_event()
  ```
- Implement local adapters:
  - `ElasticMQAdapter` — boto3 with custom endpoint to ElasticMQ
  - `MinIOStorageAdapter` — boto3 with custom endpoint to MinIO
  - `MailHogEmailSender` — SMTP to localhost:1025; viewable in MailHog UI
  - `AnthropicLLMAdapter` — calls Anthropic API directly; model = claude-sonnet-4-20250514
  - `LocalOCRAdapter` — pytesseract + pdfplumber for text; tabula-py for tables
  - `LocalEventBusAdapter` — in-process asyncio.Queue pub/sub
- Implement AWS adapters (used in Phase 1+):
  - `SQSAdapter`, `S3StorageAdapter`, `SESEmailSender`, `BedrockLLMAdapter`, `TextractOCRAdapter`, `EventBridgeAdapter`
- Adapter selection via `ADAPTER_MODE=local|aws` environment variable; factory function at startup
- **Acceptance:** Agent code uses only adapter interfaces; switching `ADAPTER_MODE=aws` requires zero code changes in agent logic

### Task 0.4 - Database Schema and Seed Data (Local)
- Write Alembic migration files for all tables from design.md (reused directly in Phase 1)
- Create `scripts/seed_local.py`:
  - 20 sample customer profiles (varied configurations)
  - 12 default business rules covering all rule types
  - 4 email templates with realistic Handlebars markup
  - All 60+ field configurations with labels and conditional dependencies
  - 3 test users: agent@test.com, supervisor@test.com, admin@test.com
  - 5 sample orders in various statuses for immediate UI dev
- Auto-run migrations + seed on `docker compose up` via entrypoint script
- **Acceptance:** All tables populated; queries return expected seed data

### Task 0.5 - Shared Libraries and Domain Models
- Python models: `OrderSchema`, `EmailRecord`, `ValidationResult`, `AgentMessage`, `ExtractionResult` (all Pydantic v2)
- Python utils: `normalizers.py` (dates, weights, addresses, phone), `confidence.py` (weighted avg + routing), `pii_masker.py`, `logger.py` (structured JSON)
- TypeScript types: mirroring all Python models; Zod schemas for API validation; shared constants (status enums, queue names, thresholds)
- Unit tests: 30+ date format fixtures, PII masking, confidence routing boundary tests
- **Acceptance:** All tests pass; models importable from both agent and API packages; TS types compile cleanly

### Task 0.6 - AI Agent Pipeline (Local)
- Implement all 6 agents using adapter interfaces:
  - **Email Intake Agent**: file watcher mode — monitors `./test-emails/inbox/` for new `.eml` files; parses with Python `email` stdlib; classifies via Anthropic API (Claude Haiku)
  - **Document Understanding Agent**: pdfplumber (digital PDF), pytesseract (scanned/images), openpyxl (Excel), python-docx (Word)
  - **Order Extraction Agent**: Anthropic API (Claude Sonnet); same prompt strategy as production; temperature=0
  - **Validation Agent**: business rule engine; address validation mock (always deliverable) or optional Google Maps key; duplicate detection via pgvector
  - **Customer Communication Agent**: LLM generates email; sends via MailHog SMTP; viewable at localhost:8025
  - **Order Creation Agent**: same creation logic; PostgreSQL sequence for order numbers
- Agent runner (`packages/agents/runner.py`): all 6 agents as concurrent asyncio tasks; each polls its ElasticMQ queue
- CLI: `make run-agents`, `make test-email FILE=path/to/email.eml`
- **Acceptance:** Drop `.eml` in inbox dir; order created in DB within 60s (perfect order) or missing-info email in MailHog (incomplete order)

### Task 0.7 - FastAPI Backend (Local)
- Full REST API from design.md: orders, emails, queues, conversations, customers, reports, admin, health
- Local auth: `POST /api/v1/auth/login` returns JWT signed with local secret; no Cognito
- RBAC: same `@require_role()` decorator as production
- WebSocket: `ws://localhost:8000/ws/dashboard` for real-time metric updates
- **Acceptance:** All endpoints work with seed data; JWT auth with seed users; WebSocket delivers updates

### Task 0.8 - React Frontend (Local)
- All 7 UI modules: Dashboard, Order Management, Inbox, Validation Queue, Communication Center, Audit Logs, Administration
- Vite proxy routes `/api/*` to FastAPI container at localhost:8000
- Responsive layout (1280px+ desktop-first for ops agents)
- **Acceptance:** All modules render with seed data; HITL workflow functional; manual order creation validates and saves

### Task 0.9 - Local Demo Rehearsal
- Prepare 8 test email fixtures matching PRD Section 23 demos:
  1. `demo1-perfect-body-only.eml` — all mandatory fields in plain text
  2. `demo2-pdf-attachment.eml` — blank body + 2-page PDF rate confirmation
  3. `demo3-scanned-image.eml` — JPG of handwritten BOL
  4. `demo4-missing-pickup-date.eml` — all fields except pickup_date
  5. `demo5-missing-multiple.eml` — missing delivery address + equipment type
  6. `demo6-customer-reply.eml` — threaded reply to pre-staged awaiting order
  7. `demo7-ambiguous-commodity.eml` — produces ~82% confidence
  8. `demo8-duplicate.eml` — identical to demo1
- Write `scripts/run_demo.sh`: processes each demo email with 30s pause; reports status
- Execute all 8 demos locally; verify expected outcomes match PRD
- **Acceptance:** All 8 demos pass without errors; outcomes match expected behavior; pipeline time < 5 min/order

---

## Phase 1 - AWS Infrastructure (Cloud Migration)

**Goal:** Deploy the already-working local prototype to AWS. All agent code remains unchanged — only adapters switch from local to AWS via `ADAPTER_MODE=aws`.

### Task 1.1 - Project Repository and Monorepo Setup
- Initialize monorepo with workspaces: `packages/agents`, `packages/api`, `packages/frontend`, `packages/shared`, `infrastructure/cdk`
- Configure root `package.json` / `pyproject.toml` for shared tooling
- Set up ESLint, Prettier, Black, isort configs
- Configure GitHub Actions CI pipeline: lint, type-check, unit test on every PR
- Add `.env.example` files for all services with required environment variable keys (no secrets)
- **Acceptance:** CI pipeline passes on empty scaffold; all workspace packages resolve

### Task 1.2 - AWS CDK Infrastructure Scaffolding
- Define CDK app with stacks: `NetworkStack`, `DatabaseStack`, `StorageStack`, `QueueStack`, `SecretsStack`, `EcsStack`, `ApiGatewayStack`
- `NetworkStack`: VPC with public/private/isolated subnets across 2 AZs; NAT Gateway; security groups for ALB, ECS, RDS, Redis
- `StorageStack`: S3 buckets — `attachments-{env}`, `extracted-text-{env}`, `exports-{env}`, `static-{env}`; versioning enabled; lifecycle rule to Glacier after 2 years
- `SecretsStack`: Secrets Manager entries for DB credentials, LLM API keys, mailbox credentials, SES config; placeholders only at this stage
- `QueueStack`: SQS Standard queues — `document-processing`, `extraction`, `validation`, `auto-process`, `hitl`, `communication`, `exception`; each with a paired DLQ (14-day retention)
- **Acceptance:** `cdk synth` produces valid CloudFormation; `cdk deploy` to dev account completes without errors

### Task 1.3 - Database Setup and Schema Migration
- Provision RDS PostgreSQL 15 Multi-AZ instance in private subnet; configure PgBouncer connection pooler on ECS
- Enable `pgvector` extension on the database
- Create read replica for reporting queries
- Write Alembic (Python) migration files for all 12 tables defined in design.md: `emails`, `orders`, `email_attachments`, `customers`, `conversations`, `conversation_messages`, `validation_results`, `order_history`, `agent_execution_logs`, `audit_logs`, `business_rules`, `field_configurations`, `email_templates`, `users`
- Add all indexes defined in design.md; add composite index on `orders(customer_id, pickup_date, delivery_address->>'postal_code')` for duplicate detection
- Seed `field_configurations` table with all 60+ fields from requirements.md Section 4; seed 4 default `email_templates`; seed 12 default `business_rules`
- **Acceptance:** `alembic upgrade head` runs cleanly; all tables and indexes exist; seed data present; pgvector extension active

### Task 1.4 - ElastiCache Redis and EventBridge Setup
- Provision ElastiCache Redis 7 cluster (2 nodes, cluster mode) in private subnet
- Create EventBridge custom bus `order-platform-bus`; define event rules for: `order.created`, `order.updated`, `hitl.approved`, `email.classified`
- Add stub Lambda targets for each event (log-only) to validate routing
- **Acceptance:** Redis cluster reachable from ECS security group; EventBridge test events route to stub targets

### Task 1.5 - Shared Python and TypeScript Libraries
- `packages/shared/python`: `OrderSchema` Pydantic model (all 60+ fields + confidence scores); `ValidationResult` model; `AgentMessage` SQS envelope model; DB session factory (SQLAlchemy async); S3 helper (upload, presigned URL); SQS helper (publish, consume); structured logger (JSON, PII masking)
- `packages/shared/typescript`: TypeScript types mirroring order schema; API response envelope types; shared Zod validation schemas for frontend and API
- Write unit tests for PII masking, date normalization utilities, and SQS envelope serialization
- **Acceptance:** All shared library unit tests pass; types importable in both agent and API packages


---

## Phase 2 - AI Agent Pipeline (Cloud Deployment)

**Goal:** Deploy the agents (already working locally from Phase 0) to ECS Fargate with real AWS SQS, S3, Bedrock, and Textract. Add production email ingestion via Microsoft Graph API.

### Task 2.1 - Email Intake Agent
- Implement mailbox polling service: Microsoft Graph API client (OAuth 2.0 client credentials) with IMAP/TLS fallback
- Poll every 60s (configurable via env var `EMAIL_POLL_INTERVAL_SECONDS`); retrieve all unread emails since last processed `Message-ID`
- On each email: check `emails.message_id` for duplicates; if new, persist `EmailRecord` to DB with status `received`; mark email as processing in mailbox (custom folder flag)
- Download all attachments (up to 25 MB each); validate MIME type against allowlist; upload to S3 path `attachments/{year}/{month}/{email_id}/{filename}`; persist `email_attachments` rows
- Implement LLM classification using Claude Haiku: few-shot prompt with subject + sender domain + body snippet (first 500 chars) + thread context; persist classification + confidence to DB
- Publish `AgentMessage` to `document-processing-queue` SQS with `email_id`
- Error handling: mailbox connection failure — retry 3x with 30s backoff; alert SNS after 3 consecutive failures; oversized attachments flagged with status `manual_review`
- Write unit tests: duplicate Message-ID guard, MIME type validation, SQS message format, classification prompt formatting
- **Acceptance:** US-001 and US-002 acceptance criteria met; `email_detection_latency_ms` CloudWatch metric emitted

### Task 2.2 - Document Understanding Agent
- Consume from `document-processing-queue`; retrieve email record and attachment S3 paths
- PDF processing: attempt `pdfplumber` text extraction; if text layer absent (< 100 chars extracted), fall back to AWS Textract `AnalyzeDocument` with `TABLES` and `FORMS` feature types
- Image processing (PNG, JPG, TIFF, BMP): AWS Textract `DetectDocumentText` + `AnalyzeDocument`; extract word-level confidence scores
- Excel processing: `openpyxl` — iterate all worksheets; call Claude Haiku to identify header row index; extract all tables as `[{header: value}]` key-value pairs
- Word processing: `python-docx` for text + table extraction; `mammoth` for complex HTML conversion fallback
- For each document: produce `ExtractedDocument` object — raw text corpus + structured key-value pairs + source coordinates (page/cell) + per-field OCR confidence
- Store extracted text to S3 `extracted-text/{email_id}/{attachment_id}.json`; update `email_attachments.extracted_text_s3_key` and `ocr_confidence`
- Publish combined extraction payload to `extraction-queue`
- Error handling: unsupported file type — log and skip; OCR failure — single retry; persistent failure — route to HITL with raw S3 link
- Write unit tests: text layer detection logic, table extraction from fixture PDFs, Excel multi-sheet merging
- **Acceptance:** US-003 and US-004 acceptance criteria met; AC-003 and AC-004 extraction accuracy targets testable

### Task 2.3 - Order Extraction Agent
- Consume from `extraction-queue`; concatenate email body + all `ExtractedDocument` corpora into single text input
- Implement chunking for documents > 100K tokens: 500-token overlap; run extraction on each chunk; merge results by selecting max-confidence value per field
- Build structured extraction prompt: full field schema from `field_configurations` table, normalization rules, 10 few-shot examples loaded from S3, instruction to return JSON with `confidence_scores` map
- Call Claude 3.5 Sonnet via AWS Bedrock (`anthropic.claude-3-5-sonnet-20241022-v2:0`); temperature = 0; max tokens = 4096
- On malformed JSON response: up to 2 self-correction retries with error context appended to prompt
- On Bedrock failure: fall back to OpenAI GPT-4o API
- Normalize all extracted values: dates (15+ formats + relative dates) to ISO 8601; weights to LBS/KGS; addresses (St/Ave/Blvd abbreviations expanded); phone numbers to E.164
- Compute `overall_confidence_score` as weighted average of all mandatory field confidence scores (equal weights; configurable per field)
- Persist extracted order draft to `orders` table with status `extracted`; store `field_confidence_scores` JSONB; log token usage to `agent_execution_logs`
- Publish to `validation-queue`
- Write unit tests for all normalization functions; parameterized tests covering TC-AI-001 through TC-AI-010 from PRD Section 24.2
- **Acceptance:** US-005 acceptance criteria met; AC-002 >= 90% field accuracy on 50-email labeled test dataset

### Task 2.4 - Validation Agent
- Consume from `validation-queue`; load order + `field_configurations` + `business_rules` (ordered by priority) from DB
- Mandatory field check: for each field where `is_mandatory = true` (or conditional rule satisfied), verify non-null and non-empty; flag failure with `status = fail`
- Conditional rules: Reefer equipment triggers temperature_min_c + temperature_max_c as mandatory; Hazmat = Y triggers UN number + hazmat class; FTL/LTL triggers num_pallets
- Business rule engine: evaluate each active rule in priority order; support rule types: `required_if`, `valid_enum`, `date_after`, `date_before`, `regex_match`, `address_valid`
- Address validation: call SmartyStreets US/CA API for pickup and delivery addresses; map response to pass/warning/fail; cache results in Redis (TTL 24h) to avoid duplicate API calls
- Duplicate detection: DB query for same `customer_id` + `pickup_date` + `delivery_address postal_code` within configured window (default 72h); also compute pgvector embedding of commodity + route description; cosine similarity >= 0.92 = potential duplicate
- Persist all validation results to `validation_results` table
- Confidence routing:
  - >= 95% + all mandatory pass: publish to `auto-process-queue`
  - 80-94%: publish to `hitl-queue` with `queue_type = confidence_review`
  - Missing mandatory + auto-comm threshold met: publish to `communication-queue`
  - Missing mandatory + auto-comm threshold not met: publish to `hitl-queue` with `queue_type = validation_failure`
  - < 80%: publish to `exception-queue`
  - Duplicate detected: publish to `hitl-queue` with `queue_type = duplicate_review`
  - Hazmat = Y: always publish to `hitl-queue` regardless of confidence
- Update order status accordingly; log routing decision to `order_history`
- Write integration tests for every routing path; parameterized rule tests for all 12 default rules
- **Acceptance:** US-006 acceptance criteria met; AC-005 and AC-010 pass

### Task 2.5 - Customer Communication Agent
- Consume from `communication-queue`; load order + validation failures + customer profile from DB
- Identify missing fields: collect all `validation_results` with `status = fail` where field is mandatory; resolve human-readable labels from `field_configurations.label`
- Select active `missing_info` email template from DB; call Claude Haiku to fill `{{variable}}` placeholders (customer_name, missing_fields list, order_reference, response_sla)
- Send email via AWS SES: `From` = configured reply-to address; `In-Reply-To` + `References` headers set to original email `Message-ID`; both HTML and plain-text parts included
- Enforce 5-minute SLA: calculate elapsed time from `emails.received_at`; if > 5 minutes log SLA breach to CloudWatch metric `communication_sla_breach`
- Persist outbound email to `conversation_messages` (direction = outbound); update order status to `awaiting_customer`; update `conversations` record
- Schedule follow-up: write delayed SQS message (24h visibility delay) to `communication-queue` with `action = follow_up`
- Schedule timeout escalation: write delayed SQS message (48h) with `action = timeout_escalation`
- Handle follow-up action: send follow-up email using `follow_up` template
- Handle timeout action: update order status; publish to `hitl-queue` with `queue_type = escalation`; send SNS notification to configured agent recipients
- Write unit tests: template variable substitution, SES call parameters, thread header construction, follow-up scheduling
- **Acceptance:** US-007 acceptance criteria met; AC-006 outbound email within 5 minutes

### Task 2.6 - Order Creation Agent
- Consume from `auto-process-queue` (auto path) OR subscribe to EventBridge `hitl.approved` event (HITL path)
- Idempotency check: query `orders` for existing record with same `source_email_id` + `customer_order_number`; if found, skip creation and log
- Generate order number: atomic DB sequence per day — `ORD-{YYYYMMDD}-{XXXXX}` (zero-padded 5-digit counter reset daily via PostgreSQL sequence per date partition)
- Insert order record with status `order_created`; link `source_email_id`, `conversation_id`; store `validation_results` reference; set `processing_mode` (auto or hitl_review)
- Send acknowledgement email via SES using `acknowledgement` template within 2 minutes of creation; log to `conversation_messages`
- Publish `order.created` EventBridge event with full order payload (for future TMS adapter)
- Append to `order_history`: event_type = `order_created`, triggered_by = `agent` or `user`, actor_id = agent run_id or user_id
- Retry policy: on DB error, retry 3x with exponential backoff (2s, 4s, 8s); on persistent failure, publish to DLQ and route to HITL with error detail
- Write integration tests: auto path happy path, HITL path via EventBridge, idempotency duplicate prevention, DB failure + retry
- **Acceptance:** US-008 acceptance criteria met; AC-008 all 10 perfect test orders auto-created

### Task 2.7 - End-to-End Agent Pipeline Integration Test
- Write pytest integration test suite using testcontainers (PostgreSQL + Redis) and mocked AWS services (localstack for SQS, S3, SES, EventBridge)
- Test the complete pipeline for each of these scenarios: perfect email body only, PDF attachment, missing mandatory field, customer response re-processing, duplicate detection
- Assert correct DB state, SQS routing, and EventBridge events at each pipeline stage
- Measure and assert processing latency < 5 minutes P95 for auto-processed orders
- **Acceptance:** All 5 pipeline scenarios pass; AC-007 customer response re-processed within 3 minutes


---

## Phase 3 - Order Entry Application (Core Modules)

**Goal:** Deliver the 4 core UI modules needed for PoC demos: Dashboard, Order Management, Inbox, and Validation Queue.

### Task 3.1 - React Application Scaffold and Auth
- Initialize Vite + React 18 + TypeScript project in `packages/frontend`; configure Tailwind CSS v3, React Query v5, React Router v6, Socket.io client
- Configure Amazon Cognito hosted UI; implement login/logout flow with JWT access + refresh tokens stored in memory (not localStorage); silent refresh via iframe before expiry
- Implement `AuthContext` and `useAuth` hook; `ProtectedRoute` component that redirects unauthenticated users
- Create base layout: top navigation bar (logo, user avatar, role badge, notifications bell, logout); collapsible left sidebar with module links; main content area with breadcrumbs
- Define role-aware navigation: sidebar items visible based on user role (Agent/Supervisor/Admin/ReadOnly)
- Write Playwright test: login, verify token in memory, access protected route, logout clears session
- **Acceptance:** Login flow works; unauthenticated routes redirect; role badge shows correctly

### Task 3.2 - REST API Backend (FastAPI)
- Initialize FastAPI application in `packages/api`; configure CORS (app domain only), request ID middleware, structured JSON logging, PII masking middleware
- Implement JWT validation middleware: verify Cognito-issued JWT signature + expiry + audience on every request; extract user_id and role from claims
- Implement RBAC decorator `@require_role(min_role)`: maps role hierarchy (readonly < agent < supervisor < admin); raise HTTP 403 if insufficient
- Implement pagination helper: accept `page`, `limit` query params; return standard envelope `{data, total_count, total_pages, page, limit}`
- Implement standard error handler: map exceptions to `{error: {code, message, field, details}}` envelope; never leak stack traces to client
- Implement `GET /api/v1/health`: return `{status, version, db_connected, queue_connected, cache_connected}`
- Add OpenAPI docs at `/api/v1/docs` (disable in production)
- Write unit tests for JWT validation, RBAC decorator, pagination helper, error envelope
- **Acceptance:** Health endpoint returns 200; RBAC unit tests cover all 4 roles; OpenAPI schema generates without errors

### Task 3.3 - Order Management API Endpoints
- Implement all 10 order endpoints from design.md Section 4.2
- `GET /api/v1/orders`: paginated list with filters (status, date range, customer, equipment_type, freight_type, confidence range, processing_mode); read from DB read replica; cache count queries in Redis (TTL 30s)
- `POST /api/v1/orders`: manual order creation; validate all fields using same business rules as Validation Agent; create order with `processing_mode = manual_entry`; log to `audit_logs`
- `GET /api/v1/orders/:id`: full order detail including `field_confidence_scores`, `validation_results`, linked email summary
- `PATCH /api/v1/orders/:id`: partial update; record old/new values in `audit_logs`; restricted fields (order_number, source_email_id) are immutable
- `DELETE /api/v1/orders/:id` (Supervisor+): soft-delete — set status to `cancelled`; log to `order_history`
- `POST /api/v1/orders/:id/approve`: validate order is in `pending_review`; trigger Order Creation Agent via EventBridge `hitl.approved` event; update status
- `POST /api/v1/orders/:id/reject`: accept `reason_code`; update status; optionally trigger communication queue
- `POST /api/v1/orders/:id/clone`: copy all fields to new draft order with status `extracted`; strip system fields
- `GET /api/v1/orders/:id/history`: return `order_history` rows for this order sorted by `created_at`
- `GET /api/v1/orders/:id/audit` (Supervisor+): return `audit_logs` filtered to this order's entity_id
- Write integration tests with testcontainers PostgreSQL for all endpoints; test RBAC on every restricted endpoint
- **Acceptance:** All order endpoints return correct data; RBAC enforced; pagination works; audit entries created

### Task 3.4 - Dashboard Module (Frontend)
- Implement `DashboardPage` component; fetch KPIs from `GET /api/v1/reports/dashboard`
- Build 10 KPI widgets as reusable `MetricCard` components: value + label + trend indicator; clicking card sets pre-applied filter and navigates to Order Management
- Implement real-time refresh: WebSocket connection via Socket.io to backend; fall back to 30s polling if WebSocket unavailable
- STP Rate trend chart: use Recharts `LineChart`; last 30 days; download as PNG via `html2canvas`
- Implement period toggle (Today / This Week / This Month) — updates all widgets simultaneously
- Loading skeleton screens while data fetches; error boundary with retry button
- Cache last fetched KPIs in React Query; stale-while-revalidate pattern
- Write Playwright tests: all 10 widgets render with data; clicking a metric card navigates with correct filter params
- **Acceptance:** US-010 acceptance criteria met; Dashboard loads in < 3 seconds; metrics refresh every 30s

### Task 3.5 - Order Management Module (Frontend)
- Implement `OrderListPage`: paginated table with sortable columns; status color-coded badge component; inline actions (View, Edit, Clone, Delete with confirmation modal)
- Implement `OrderFilterPanel`: multi-select status, date range pickers, customer searchable dropdown (debounced API call), equipment type + freight type dropdowns, confidence score range slider, processing mode radio
- Implement saved filter presets: save to `localStorage` + sync to user profile via `PATCH /api/v1/users/me/preferences`
- Implement CSV and PDF export: call `GET /api/v1/reports/orders?format=csv` and `format=pdf`; download via blob URL
- Implement `OrderDetailPage`: grouped field sections matching schema; `ConfidenceBadge` component (green/yellow/red); hover tooltip showing source document + page + extraction method; resizable split panel with email viewer
- Implement order status timeline component using `order_history` data
- Implement `ManualOrderFormPage`: all 60+ fields in logical grouped layout; address autocomplete via Google Places; customer type-ahead; conditional field visibility (temperature fields when Reefer selected; UN number when Hazmat checked); 30s auto-save draft; inline validation on blur
- Write Playwright tests: filter panel applies correctly; order detail shows confidence badges; manual form conditional fields appear/disappear
- **Acceptance:** AC-011 agent can review and manage orders end-to-end; manual order creation form validates all rules

### Task 3.6 - Email Inbox Module (Frontend)
- Implement `InboxPage`: paginated email list with From, Subject, Received Date, Classification badge (color by type), Linked Order Number, Processing Status columns
- Implement `EmailDetailPage`: rendered email body (HTML sanitized via DOMPurify); attachment list with file type icons; `GET /api/v1/emails/:id/attachments/:aId/url` for download
- Implement inline attachment viewers: PDF viewer using PDF.js `PDFViewer` component; image lightbox with zoom; Excel/Word rendered as extracted text with sheet/table structure preserved
- Implement `ExtractionResultsPanel`: per-field values with confidence badges; source annotation showing document name + page/cell for each field
- Implement Reclassify action: dropdown to select correct type; `POST /api/v1/emails/:id/reclassify`; show confirmation and status update
- Implement Send to Review button: `POST /api/v1/queues/hitl` with email_id; navigate to Validation Queue
- Write Playwright tests: email detail renders; attachment download URL generated; reclassify updates classification badge
- **Acceptance:** US-002 reclassification flow works; attachment viewers render for PDF, image, and Excel fixtures

### Task 3.7 - Validation Queue Module (Frontend)
- Implement `ValidationQueuePage`: tabbed view for 5 queue types (Confidence Review, Validation Failure, Exception, Duplicate Review, Escalation); each tab shows item count badge
- Each queue list shows: Order Number, Customer Name, Queue Type, Overall Confidence, Time in Queue, Priority badge; sorted by priority then oldest first
- Implement `HITLReviewPage` (the core HITL experience):
  - Resizable split panel: left = original email + attachment viewer (same components as Inbox); right = extracted order form
  - Form fields: all 60+ order fields; inline-editable; validation on blur using same rules as Validation Agent
  - Per-field `ConfidenceBadge`: green >= 90%, yellow 70-89%, red < 70%
  - Validation failure banner above form: lists each failing rule with field name and error message
  - Sticky action footer: Approve Order, Request More Info, Discard (with reason code modal), Escalate to Supervisor (with mandatory notes input)
- Approve action: `POST /api/v1/orders/:id/approve`; record all field corrections (original AI value vs. agent value) in request body for audit logging
- Request More Info: slides in compose panel pre-populated with identified missing fields; agent can edit before sending; `POST /api/v1/conversations/:id/reply`
- Discard action: reason code modal (Duplicate, Invalid Request, Test Email, Other); optional customer notification
- Escalate action: text area for mandatory escalation notes; `POST /api/v1/orders/:id/escalate`
- Duplicate Review Queue: side-by-side comparison of two order records; Confirm Duplicate or Mark as Unique actions
- Write Playwright tests: full HITL workflow for confidence review, validation failure, and duplicate review scenarios
- **Acceptance:** US-009 and AC-009 acceptance criteria met; all 5 queue types functional with correct routing


---

## Phase 4 - Order Entry Application (Remaining Modules)

**Goal:** Complete the web application with Customer Communication Center, Audit Logs, and Administration module.

### Task 4.1 - Customer Communication Center (API + Frontend)
- Backend: implement conversations and messages endpoints from design.md (`GET /conversations`, `GET /conversations/:id`, `POST /conversations/:id/reply`)
- `POST /api/v1/conversations/:id/reply`: validate agent role; accept `template_id` or `custom_body`; call Communication Agent logic to fill template variables via LLM; send via SES; persist to `conversation_messages`; set correct `In-Reply-To` threading headers
- Frontend `CommunicationCenterPage`: conversation list grouped by Order/Customer; unread count badges; last message preview + timestamp; search by customer name or order number
- Thread view: full chronological email thread; inbound emails (left-aligned); outbound emails (right-aligned); collapsed email headers expanded on click; inline attachment download
- Compose panel: TipTap rich text editor; recipient auto-populated from order contact; CC/BCC optional fields; character limit warning at 2000 chars
- Template selector: dropdown of active templates by type; on selection, call `POST /api/v1/communications/preview` to render LLM-filled variables; show preview before inserting
- Response tracking indicators per outbound email: Sent / Bounced / Delivered; response received timestamp with link to reply message
- Customer Profile sidebar: order history count (clickable to filtered Order Management), avg response time, opt-out status badge
- **Acceptance:** Agent can compose, send, and track customer emails; threading maintains correct Message-ID chain

### Task 4.2 - Audit and Activity Logs Module (API + Frontend)
- Backend: implement `GET /api/v1/audit-logs` with filters: entity_type, entity_id, actor_id, action, date range, actor_type; paginated; read from `audit_logs` + `agent_execution_logs` + `order_history`
- Backend: implement `GET /api/v1/agent/runs` and `GET /api/v1/agent/runs/:runId` (Admin only): return agent execution logs with input summary, output summary, token usage, LLM model, duration
- Frontend `AuditLogsPage`: tabbed log types (Agent Actions, User Actions, Order History, Email Processing, Communication, Validation)
- Each log table: searchable by entity ID, actor, action, date range; sortable columns; syntax-highlighted JSON diff viewer for `old_value_json` vs `new_value_json`
- Export to CSV and PDF: `GET /api/v1/audit-logs?format=csv`
- Agent Runs viewer (Admin only): list of agent execution runs; detail view showing full input/output JSON, token counts, duration timeline, error detail if failed
- DLQ management (Admin): list messages in each SQS DLQ; view message body; replay individual message (`POST /api/v1/agent/replay/:emailId`) or bulk replay
- **Acceptance:** AC-013 all 20 test actions verifiable in audit log; Admin can replay failed emails from DLQ

### Task 4.3 - Administration Module (API + Frontend)
- Backend: implement all admin CRUD endpoints for `field-configs`, `business-rules`, `email-templates`, `users` with Admin role enforcement
- Frontend `AdminPage` with sub-sections:

  **Field Configuration:** draggable field list to set display_order; toggle Mandatory/Optional/Conditional per field; set conditional dependency (parent field + trigger value); edit human-readable label; changes take immediate effect on next order processed

  **Business Rules:** create/edit rule form with fields: rule_name, field_name, rule_type dropdown, rule_expression input with syntax hint, error_message, severity toggle, escalate_on_fail checkbox; drag-and-drop priority reordering; enable/disable toggle; Test Rule button — submit sample JSON order and display pass/fail result

  **Email Templates:** template editor with HTML tab + plain-text tab; Handlebars variable picker sidebar listing available `{{variables}}`; live preview pane showing rendered output with sample data; active/inactive toggle; version history showing last 5 saved versions

  **Confidence Thresholds:** sliders for all 7 configurable thresholds with valid range enforcement; save confirmation dialog ("Changes take effect immediately for all new orders"); current vs. default value indicators

  **Customer Profiles:** searchable customer list; create/edit form with: name, external_id, email_domains (tag input), always_human_review toggle, default_equipment_type, opt_out toggle; order history summary table per customer

  **User Management:** user list with role badges and last login; create user form (email, name, role); edit role; deactivate/reactivate toggle; reset password (sends Cognito reset email); per-user notification preferences

  **Mailbox Configuration:** OAuth connect button for M365 (opens Cognito-managed flow); IMAP credential form as fallback; polling interval slider; reply-to address; email signature; Test Connection button (calls `POST /api/v1/admin/mailbox/test` — returns success/failure with error detail)

  **Integration Settings:** LLM provider radio (Bedrock/OpenAI); model selector per provider; token limit inputs; address validation API provider + key; SES sender identity verified status indicator

- **Acceptance:** AC-014 admin adds mandatory field; Validation Agent enforces it on next order; all admin CRUD operations logged to audit_logs


---

## Phase 5 - Security, Observability and Performance

**Goal:** Harden the platform for PoC demonstration: complete security controls, observability stack, and performance validation.

### Task 5.1 - Security Hardening
- Configure AWS WAF on API Gateway: attach OWASP Core Rule Set v3.2; add rate-based rule (100 req/10s per IP); configure SQL injection + XSS managed rules; enable logging to S3
- Configure Cognito User Pool: enforce MFA (TOTP) for Supervisor and Admin roles via Cognito user pool MFA policy; set password policy (min 12 chars, complexity required); set access token TTL = 1 hour, refresh token TTL = 7 days
- Implement token revocation on logout: add JWT `jti` claim to Redis blocklist on logout; add middleware check against blocklist on every authenticated request
- Configure S3 bucket policies: deny all public access; add bucket policy restricting GetObject to application IAM role only; validate presigned URL expiry at 15 minutes
- Configure RDS: verify no public endpoint; restrict security group inbound to ECS task security group only on port 5432; enable RDS Performance Insights
- PII masking audit: review all CloudWatch log groups; verify email addresses masked as `j***@domain.com`, phone numbers as `***-***-XXXX` in all agent and API logs
- Configure HSTS header in ALB response headers policy: `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- Enable SES inbound SPF/DKIM/DMARC verification; flag emails failing verification with `spf_failed = true` in `emails` table; show warning badge in Inbox
- Run OWASP ZAP baseline scan against staging API; remediate all critical and high findings
- **Acceptance:** WAF blocks SQL injection test payload; MFA required for Supervisor login; PII absent from CloudWatch log samples; ZAP scan: zero critical/high unmitigated

### Task 5.2 - Observability Stack
- Configure structured JSON logging for all Python agents and FastAPI service: every log line includes `run_id`, `email_id`, `order_id`, `duration_ms`, `status`, `agent_type`; PII fields stripped
- Create CloudWatch Log Groups per service: `/order-platform/email-intake`, `/order-platform/document-understanding`, `/order-platform/order-extraction`, `/order-platform/validation`, `/order-platform/communication`, `/order-platform/order-creation`, `/order-platform/api`
- Define CloudWatch metric filters extracting: `e2e_processing_ms`, `extraction_confidence_avg`, `order_creation_rate`, `llm_error_rate`, `communication_sla_breach` from log streams
- Configure AWS X-Ray tracing: add X-Ray SDK to all Python agents and FastAPI; annotate segments with `email_id`, `order_id`; configure sampling rule (100% for staging, 5% for production)
- Create CloudWatch Alarms: SQS queue depth > 100 for 5 min; API error rate > 5% for 2 min; E2E processing time > 10 min (P95); LLM circuit breaker open; DB connection pool > 80% utilization; all alarms publish to SNS topic
- Create CloudWatch Dashboard: panels for order pipeline throughput (orders/hour), queue depths (all 7 queues), confidence score histogram, STP rate (7-day trend), LLM latency (avg/P95), API latency (avg/P95)
- Implement `GET /api/v1/health` to return real connection status for DB, Redis, SQS (test queue visibility), and LLM API (lightweight ping)
- Configure CloudWatch Synthetics canary: submit test email to staging every 15 minutes; assert processed within 3 minutes; alert if not
- **Acceptance:** X-Ray traces visible end-to-end for a test email; all 6 CloudWatch alarms fire correctly against simulated thresholds; canary passes every cycle

### Task 5.3 - Performance Validation
- Write k6 load test script: 50 virtual users; 5-minute sustained run; exercise all primary CRUD endpoints (GET orders, GET order detail, PATCH order, GET dashboard KPIs, GET queue items)
- Assert P95 response time < 500ms for all endpoints under 50 VU load; assert zero 5xx errors during test
- Write email throughput test script: inject 500 test emails into SQS `document-processing-queue` over 1 hour; assert all processed within 5 minutes each; assert ECS tasks auto-scale to handle load
- Profile and optimize any endpoint exceeding 200ms at P50: add DB indexes if missing, add Redis caching for hot read paths, add DB query EXPLAIN ANALYZE logging for slow queries
- Configure PgBouncer connection pooling: pool_mode = transaction; max_client_conn = 200; default_pool_size = 20; verify pool metrics in CloudWatch
- Test LLM circuit breaker: simulate Bedrock failures; verify circuit opens after 5 consecutive failures within 60s; verify fallback to GPT-4o; verify circuit half-opens after 60s
- **Acceptance:** AC-015 k6 test passes (P95 < 500ms, 50 VUs, 5 minutes); 500 emails/hour throughput test passes; circuit breaker behavior confirmed


---

## Phase 6 - QA, Demo Preparation and PoC Sign-Off

**Goal:** Execute all acceptance criteria, prepare the 8 PoC demo scenarios, conduct UAT, and achieve formal PoC sign-off.

### Task 6.1 - AI Extraction Test Suite
- Assemble labeled test dataset: 50 email samples (body-only orders), 30 PDF samples, 20 image/scanned document samples with ground-truth field values in JSON
- Write custom pytest harness: load each sample, run through Order Extraction Agent, compare extracted JSON vs. ground truth, compute per-field accuracy and overall accuracy
- Run test suite; capture baseline accuracy scores per field; identify fields below 90% accuracy
- For underperforming fields: update extraction prompt with additional few-shot examples targeting those fields; re-run suite until accuracy targets met
- Validate all 10 AI test cases from PRD Section 24.2 (TC-AI-001 through TC-AI-010): date normalization, weight unit conversion, multi-page PDF table extraction, ambiguous commodity HITL routing, Reefer without temperature, Hazmat without UN number, Excel multi-sheet extraction, vector semantic duplicate detection, address normalization, relative date in attachment
- **Acceptance:** AC-002 >= 90% on 50 emails; AC-003 >= 85% on 30 PDFs; AC-004 >= 80% on 20 images; all 10 TC-AI cases pass

### Task 6.2 - Functional Acceptance Test Execution
- Execute each of the 15 functional acceptance criteria (AC-001 to AC-015) in staging environment with live LLM and OCR:
  - AC-001: Send test email; measure CloudWatch `email_detection_latency_ms` < 2 minutes
  - AC-005: Submit order violating each of the 12 default business rules; verify each rejection
  - AC-006: Trigger mandatory field failure; measure outbound email timestamp vs. `emails.received_at`; verify < 5 minutes
  - AC-007: Reply to missing-info thread; measure time to order status update; verify < 3 minutes
  - AC-008: Submit 10 pre-crafted perfect orders (>= 95% confidence); verify all auto-created without HITL
  - AC-009: Submit order designed for 82% confidence; verify appearance in Confidence Review Queue within 2 minutes
  - AC-010: Submit identical order twice; verify duplicate flag and Duplicate Review Queue routing
  - AC-012: Log in as Agent, Supervisor, Admin, ReadOnly; verify each role sees correct modules and actions
  - AC-013: Perform 20 defined actions (10 user actions, 10 agent actions); verify each audit log entry with correct actor, timestamp, old/new values
  - AC-014: Admin adds new mandatory field "Carrier Reference" via Administration module; submit order without it; verify Validation Agent rejects
- Document pass/fail status for each AC; log any defects with reproduction steps
- **Acceptance:** All 15 ACs pass on first execution (PoC success criteria per PRD Section 20.2)

### Task 6.3 - Demo Environment Preparation
- Deploy staging environment with all services healthy; verify CloudWatch Synthetics canary passing
- Pre-load demo data: 20 sample customer profiles; 12 configured business rules; 4 email templates (Missing Info, Follow-up, Acknowledgement, Duplicate Notification); configure demo mailbox `orders-poc@[client-domain].com`
- Prepare and test all 8 demo email payloads:
  - Demo 1: Perfect plain-text order email (all mandatory fields; expect confidence >= 97%)
  - Demo 2: Email with blank body + 2-page PDF rate confirmation (tables on both pages)
  - Demo 3: Email with JPG image of a handwritten Bill of Lading
  - Demo 4: Complete order email missing only pickup_date
  - Demo 5: Order email missing delivery_address (all sub-fields) and equipment_type
  - Demo 6: Pre-stage an awaiting-customer-response order; prepare threaded reply
  - Demo 7: Ambiguous commodity email designed to produce 82% overall confidence
  - Demo 8: Two identical order emails to trigger duplicate detection
- Rehearse all 8 demos end-to-end; document step-by-step demo scripts with expected UI state at each step; record screen capture for backup
- Reset demo environment to clean state after each rehearsal run
- **Acceptance:** All 8 demos execute without critical failures in 2 consecutive dry runs

### Task 6.4 - User Acceptance Testing (UAT)
- Conduct UAT sessions with at least 2 operations agents (Alex persona) and 1 supervisor (Morgan persona):
  - Session 1 - Agent UAT: HITL review workflow (Demo 7); email inbox and reclassify; manual order creation; validation queue navigation; customer communication compose and send
  - Session 2 - Supervisor UAT: Dashboard monitoring and metric card drilldown; STP trend chart download; audit log review; export orders to CSV; Administration — confidence threshold adjustment
  - Session 3 - Admin UAT: add business rule; configure email template; add mandatory field; create new user and assign role; test mailbox connection
- Collect satisfaction ratings (1-5 scale) per workflow from each participant
- Document all usability issues; prioritize and fix issues rated as blockers before sign-off
- Re-test fixed issues with original participants
- **Acceptance:** Average satisfaction rating >= 4.0/5.0; all blocker-level usability issues resolved; UAT sign-off obtained from each participant

### Task 6.5 - PoC Sign-Off Package
- Compile PoC results report: AC-001 to AC-015 pass/fail table; AI accuracy scores vs. targets; KPI measurement results (STP rate, E2E time, extraction accuracy) from demo dataset; k6 performance test summary
- Prepare executive summary: actual vs. target for each KPI in Section 20.1; projected production benefits (manual effort reduction, STP rate, processing time improvement)
- Document all known limitations and out-of-scope items with Phase 2 roadmap references
- Prepare Phase 2 scope proposal: TMS integration, EDI 204, customer portal, SMS/Teams channels
- Present to Executive Sponsor; obtain formal sign-off for production progression
- Archive all demo recordings, test results, and acceptance evidence in project repository
- **Acceptance:** Executive Sponsor formally approves PoC; all PoC success criteria from PRD Section 20.2 met and documented

---

## Dependency Map

```
Phase 0 (Local Prototype - Docker Compose)
    |
    +---> Task 0.1 Monorepo Scaffold
    +---> Task 0.2 Docker Compose (parallel with 0.1)
    +---> Task 0.3 Service Adapters [requires 0.1]
    +---> Task 0.4 DB Schema + Seed [requires 0.2]
    +---> Task 0.5 Shared Libraries [requires 0.1, 0.3]
    +---> Task 0.6 AI Agents (Local) [requires 0.3, 0.4, 0.5]
    +---> Task 0.7 FastAPI Backend [requires 0.4, 0.5]
    +---> Task 0.8 React Frontend [requires 0.7]
    +---> Task 0.9 Local Demo Rehearsal [requires 0.6, 0.8]
    |
    | *** LOCAL PROTOTYPE COMPLETE — Demo-ready on laptop ***
    |
    ▼
Phase 1 (AWS Infrastructure)
    |  - Same DB schema (Alembic migrations from Phase 0)
    |  - Same agent code (adapter swap to AWS)
    |
    +---> Phase 2 (Cloud Deployment) [adapters switch to SQS/S3/Bedrock/Textract/SES]
    |         |
    |         +---> Task 2.1-2.6: Deploy agents to ECS Fargate
    |         +---> Task 2.7: E2E integration test on AWS
    |
    +---> Phase 3 (Core UI on AWS) [same React app; API points to AWS backend]
    |         |
    |         +---> Task 3.1 Auth (Cognito replaces local JWT)
    |         +---> Task 3.2-3.7 (same UI code; deployed to CloudFront/S3)
    |
    +---> Phase 4 (Full UI) [requires Phase 3]
    |
    +---> Phase 5 (Security + Perf) [requires Phase 4]
    |
    +---> Phase 6 (QA + Sign-Off) [requires Phase 5]
```

---

## Effort Estimate

| Phase | Tasks | Estimated Duration |
|---|---|---|
| Phase 0 - Local Prototype | 9 tasks | 2 weeks |
| Phase 1 - AWS Infrastructure | 5 tasks | 1 week |
| Phase 2 - AI Agents (Cloud) | 7 tasks | 1.5 weeks |
| Phase 3 - Core UI Modules | 7 tasks | 2 weeks |
| Phase 4 - Full UI Modules | 3 tasks | 1.5 weeks |
| Phase 5 - Security + Performance | 3 tasks | 1 week |
| Phase 6 - QA + Sign-Off | 5 tasks | 1 week |
| **Total** | **39 tasks** | **~10 weeks** |

Phase 0 delivers a fully working local demo in 2 weeks. Phases 1-2 are faster because all agent code is already written and tested — just swapping adapters and deploying. Phases 2-3 can still run in parallel (infra team + frontend team).
