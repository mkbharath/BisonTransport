# Design — AI-Powered Order Intake & Order Entry Automation Platform

**Version:** 1.0  
**Domain:** Transportation & Logistics  
**Date:** June 2026

---

## 1. Architecture Overview

The Platform follows a **microservices architecture with an event-driven backbone**. AI agents are implemented as independent Python services consuming from SQS queues. The web application communicates with backend services exclusively via a REST API Gateway layer.

### 1.1 Layer Summary

| Layer | Components | Technology Stack |
|---|---|---|
| Frontend (SPA) | Order Entry Application | React 18, TypeScript, Tailwind CSS, React Query v5, Socket.io client, PDF.js, Vite |
| API Gateway | REST API, JWT Auth, Rate Limiting, CORS | AWS API Gateway v2 HTTP API + Cognito Authorizer |
| Backend Services | Order, Email, Validation, Communication, Reporting Services | Python FastAPI on ECS Fargate; service-per-domain pattern |
| AI Agent Layer | 6 agents: Email Intake, Document Understanding, Order Extraction, Validation, Customer Communication, Order Creation | Python 3.12 (LangChain / LangGraph) on ECS Fargate |
| LLM Integration | Extraction, classification, email generation | AWS Bedrock (Claude 3.5 Sonnet primary; Haiku for classification); OpenAI GPT-4o fallback |
| OCR Service | PDF/image text and table extraction | AWS Textract (DetectDocumentText + AnalyzeDocument) |
| Message Queue | Async agent-to-agent handoff; backpressure management | Amazon SQS (Standard queues with DLQ; FIFO for ordered operations) |
| Event Bus | Order lifecycle events; future TMS adapter stubs | Amazon EventBridge (custom bus: `order-platform-bus`) |
| Primary Database | Orders, customers, emails, conversations, audit logs, business rules | PostgreSQL 15 on RDS Multi-AZ; pgvector extension for embeddings |
| Object Storage | Email attachments; extracted text; generated emails; exports | Amazon S3 (versioning enabled; Glacier lifecycle after 2 years) |
| Email Integration | Inbound monitoring + outbound transactional | AWS SES (outbound, DKIM-signed); Microsoft Graph API or IMAP (inbound) |
| Cache / Session | API response cache; dashboard counters; session tokens | Amazon ElastiCache Redis 7 (cluster mode) |
| Secrets | API keys, DB passwords, SMTP credentials | AWS Secrets Manager (auto-rotation every 90 days) |
| Infrastructure / IaC | All cloud resources as code; GitOps deployment | AWS CDK TypeScript; CI/CD via GitHub Actions + AWS CodePipeline |

---

## 2. AI Agent Pipeline

### 2.1 Agent Message Flow

```
Customer Email
      │
      ▼
[Email Intake Agent]
  - Polls mailbox every 60s (IMAP / MS Graph API)
  - Classifies email: New Order | Order Update | Customer Response | Cancellation | Other
  - Downloads attachments → S3
  - Persists EmailRecord to DB
  - Publishes to SQS: document-processing-queue
      │
      ▼
[Document Understanding Agent]
  - Consumes document-processing-queue
  - PDF: pdfplumber (digital) or AWS Textract (scanned)
  - Images: AWS Textract DetectDocumentText + AnalyzeDocument
  - Excel: openpyxl — all sheets, LLM header detection
  - Word: python-docx / mammoth
  - Outputs: extracted text corpus + structured key-value pairs + per-field confidence
  - Publishes to SQS: extraction-queue
      │
      ▼
[Order Extraction Agent]
  - Consumes extraction-queue
  - Combines email body + all attachment texts into single corpus
  - Calls Claude 3.5 Sonnet (Bedrock) with structured extraction prompt
  - Returns JSON matching order schema with per-field confidence_score (0–100)
  - Normalizes: dates → ISO 8601, weights → LBS/KGS, addresses de-abbreviated, phone → E.164
  - Self-corrects malformed JSON (up to 2 retries)
  - Publishes to SQS: validation-queue
      │
      ▼
[Validation Agent]
  - Consumes validation-queue
  - Checks all mandatory fields (non-null, non-empty)
  - Applies ordered business rules from business_rules table
  - Validates addresses via SmartyStreets / Google Maps API
  - Detects duplicates: DB query + pgvector cosine similarity (threshold 0.92)
  - Routes based on confidence:
      >= 95% + all mandatory → SQS: auto-process-queue
      80–94%                 → SQS: hitl-queue (Confidence Review)
      missing mandatory      → SQS: communication-queue (if auto-comm enabled) OR hitl-queue
      < 80%                  → SQS: exception-queue (Manual Entry)
      duplicate detected     → SQS: hitl-queue (Duplicate Review)
      │
      ├──▶ [Customer Communication Agent]
      │      - Consumes communication-queue
      │      - LLM generates professional missing-info email
      │      - Sends via AWS SES within 5 minutes
      │      - Sets order status → 'Awaiting Customer Response'
      │      - Schedules follow-up (24h) and timeout escalation (48h)
      │
      └──▶ [Order Creation Agent]
             - Consumes auto-process-queue
             - OR triggered by EventBridge 'hitl.approved' event (HITL path)
             - Inserts order record: status = order_created
             - Generates ORD-YYYYMMDD-XXXXX order number
             - Sends acknowledgement email via SES
             - Publishes 'order.created' event to EventBridge
```

### 2.2 Agent Specifications

#### Email Intake Agent

| Attribute | Specification |
|---|---|
| Trigger | Scheduled polling every 60s (configurable 30–300s) or MS Graph webhook push |
| Mailbox Protocol | Microsoft Graph API (M365) or IMAP/TLS |
| Classification Model | Claude 3 Haiku (few-shot: subject + sender domain + body snippet + thread history) |
| Attachment Handling | Download all attachments; validate MIME type; store to `s3://attachments/{year}/{month}/{email_id}/{filename}` |
| Supported MIME Types | PDF, Excel (xls/xlsx), Word (doc/docx), PNG, JPG, JPEG, TIFF, BMP |
| Max Attachment Size | 25 MB per attachment (configurable); oversized files flagged for manual review |
| Duplicate Email Guard | Check Message-ID against `emails` table before processing |
| Error Handling | Mailbox connection failure: retry 3x with 30s backoff; alert via SNS after 3 consecutive failures |
| Concurrency | Up to 20 emails in parallel via SQS + 20 concurrent ECS task workers |

#### Document Understanding Agent

| Attribute | Specification |
|---|---|
| PDF Processing | Digital PDFs: `pdfplumber` direct text extraction. Scanned PDFs: AWS Textract (auto-detected by absence of text layer) |
| Image Processing | AWS Textract `AnalyzeDocument` for structured form extraction on PNG, JPG, TIFF, BMP |
| Excel Processing | `openpyxl`; iterate all worksheets; detect header rows via LLM; extract tables as key-value pairs |
| Word Processing | `python-docx` for text + table extraction; `mammoth` for complex formatting → HTML conversion |
| Table Extraction | Textract Table feature for PDFs/images; openpyxl built-in for Excel; python-docx table API for Word |
| Error Handling | Unsupported type: log and skip. OCR failure: single retry. Persistent failure: route to HITL with raw S3 link |

#### Order Extraction Agent

| Attribute | Specification |
|---|---|
| LLM Model | Claude 3.5 Sonnet (primary) via AWS Bedrock; OpenAI GPT-4o (fallback on Bedrock failure) |
| Prompt Strategy | Structured extraction prompt with full field schema, normalization rules, 10 few-shot examples, JSON output instruction |
| Output Schema | JSON object matching order schema with nested `confidence_scores: {field_name: score_0_to_100}` |
| Normalization | Dates: 15+ formats including relative ('next Monday') → ISO 8601. Weights: detect unit. Addresses: expand abbreviations. Phone: E.164 |
| Long Document Handling | Documents > 100K tokens chunked with 500-token overlap; max-confidence value selected per field across chunks |
| Idempotency | Temperature = 0 for deterministic output |
| Token Budget | Capped at 50,000 tokens per order |

#### Validation Agent

| Attribute | Specification |
|---|---|
| Business Rule Engine | Rules stored in `business_rules` table; evaluated as ordered chain by priority; supports: `required_if`, `valid_enum`, `date_after`, `date_before`, `regex_match`, `address_valid`, `custom_js_expression` |
| Address Validation | SmartyStreets US/CA API or Google Maps Geocoding; status: deliverable (pass), incomplete (warning), invalid (fail) |
| Duplicate Detection | DB query: same `customer_id` + `pickup_date` + `delivery_postal_code` within 72h. Vector: cosine similarity on order description embedding vs. recent orders (threshold 0.92) |
| Conditional Rules | Reefer → temperature min/max required. Hazmat = Y → UN number + hazmat class required. FTL/LTL → num_pallets required |

#### Customer Communication Agent

| Attribute | Specification |
|---|---|
| Email Generation | LLM generates professional email listing missing fields by human-readable label; includes customer name, order reference, response SLA |
| Template System | Base HTML + plain-text templates in Administration; LLM fills `{{variable}}` placeholders |
| Sending | AWS SES (preferred) or MS Graph Send Mail API; rate limited to 50 emails/minute |
| Thread Continuity | `In-Reply-To` and `References` headers set to original email Message-ID |
| Follow-up Logic | No response in 24h: automated follow-up. No response in 48h: escalate to HITL Escalation Queue |

#### Order Creation Agent

| Attribute | Specification |
|---|---|
| Order Number Format | `ORD-YYYYMMDD-XXXXX` (5-digit zero-padded counter, reset daily) |
| Idempotency Key | Composite key: `source_email_id` + `customer_order_number` |
| Retry Policy | On DB error: 3 retries with exponential backoff (2s, 4s, 8s); persistent failure → DLQ → HITL escalation |
| Order Update Flow | For Order Update emails: match by `customer_order_number` or `conversation.thread_id`; apply field-level patch; record diff in `order_history` |

---

## 3. Data Model

### 3.1 Core Tables

#### `emails`

```sql
CREATE TABLE emails (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id                VARCHAR(500) UNIQUE NOT NULL,   -- SMTP Message-ID; deduplication key
    thread_id                 VARCHAR(500),
    from_address              VARCHAR(255) NOT NULL,
    to_address                VARCHAR(255) NOT NULL,
    subject                   TEXT,
    body_text                 TEXT,
    body_html                 TEXT,                           -- stored sanitized (XSS-safe)
    received_at               TIMESTAMPTZ NOT NULL,
    processed_at              TIMESTAMPTZ,
    classification            VARCHAR(50),                    -- new_order | order_update | customer_response | cancellation | other
    classification_confidence DECIMAL(5,2),                  -- LLM classification confidence 0–100
    status                    VARCHAR(50) NOT NULL,           -- received | processing | processed | failed
    linked_order_id           UUID REFERENCES orders(id),
    conversation_id           UUID REFERENCES conversations(id),
    created_at                TIMESTAMPTZ DEFAULT NOW(),
    updated_at                TIMESTAMPTZ
);
```

#### `orders`

```sql
CREATE TABLE orders (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number                VARCHAR(50) UNIQUE NOT NULL,  -- ORD-YYYYMMDD-XXXXX
    source_email_id             UUID REFERENCES emails(id),
    customer_id                 UUID REFERENCES customers(id),
    status                      VARCHAR(50) NOT NULL,         -- extracted | pending_review | awaiting_customer | validated | order_created | failed | cancelled
    overall_confidence_score    DECIMAL(5,2),                 -- weighted AI confidence 0–100
    processing_mode             VARCHAR(20),                  -- auto | hitl_review | manual_entry
    field_confidence_scores     JSONB,                        -- {field_name: score}
    -- Customer Info
    customer_name               VARCHAR(255),
    customer_external_id        VARCHAR(50),
    contact_name                VARCHAR(255),
    contact_email               VARCHAR(255),
    contact_phone               VARCHAR(50),
    -- Pickup
    pickup_location_name        VARCHAR(255),
    pickup_address              JSONB,                        -- {line1, line2, city, state, postal_code, country}
    pickup_date                 DATE,
    pickup_time_window          JSONB,                        -- {start: HH:MM, end: HH:MM}
    pickup_instructions         TEXT,
    -- Delivery
    delivery_location_name      VARCHAR(255),
    delivery_address            JSONB,
    delivery_date               DATE,
    delivery_time_window        JSONB,
    delivery_instructions       TEXT,
    -- Shipment
    customer_order_number       VARCHAR(100),
    reference_number            VARCHAR(100),
    po_number                   VARCHAR(100),
    commodity                   TEXT NOT NULL,
    freight_type                VARCHAR(50),                  -- ftl | ltl | partial | intermodal
    total_weight                DECIMAL(10,2),
    weight_unit                 VARCHAR(10),                  -- lbs | kgs
    dimensions                  VARCHAR(100),
    total_quantity              INTEGER,
    num_pallets                 INTEGER,
    stackable                   BOOLEAN DEFAULT FALSE,
    -- Transportation
    equipment_type              VARCHAR(50),
    truck_size                  VARCHAR(50),
    temperature_min_c           DECIMAL(5,2),
    temperature_max_c           DECIMAL(5,2),
    hazmat_indicator            BOOLEAN DEFAULT FALSE,
    hazmat_un_number            VARCHAR(10),
    hazmat_class                VARCHAR(50),
    special_handling_instructions TEXT,
    liftgate_required           BOOLEAN DEFAULT FALSE,
    team_drive_required         BOOLEAN DEFAULT FALSE,
    twic_card_required          BOOLEAN DEFAULT FALSE,
    -- Additional
    notes                       TEXT,
    internal_comments           TEXT,
    attachment_references       TEXT[],
    reviewed_by_user_id         UUID REFERENCES users(id),
    reviewed_at                 TIMESTAMPTZ,
    created_at                  TIMESTAMPTZ DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ
);

CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_pickup_date ON orders(pickup_date);
CREATE INDEX idx_orders_order_number ON orders(order_number);
```

### 3.2 Supporting Tables

#### `email_attachments`

```sql
CREATE TABLE email_attachments (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email_id              UUID NOT NULL REFERENCES emails(id),
    file_name             VARCHAR(500) NOT NULL,
    file_type             VARCHAR(50),                  -- pdf | xlsx | docx | png | jpg | tiff | bmp
    file_size_bytes       BIGINT,
    s3_key                VARCHAR(1000) NOT NULL,
    extracted_text_s3_key VARCHAR(1000),
    ocr_confidence        DECIMAL(5,2),
    processing_status     VARCHAR(50),                  -- pending | processing | completed | failed
    created_at            TIMESTAMPTZ DEFAULT NOW()
);
```

#### `customers`

```sql
CREATE TABLE customers (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                  VARCHAR(255) NOT NULL,
    external_id           VARCHAR(100),
    email_domains         TEXT[],                       -- allowed sender domains
    always_human_review   BOOLEAN DEFAULT FALSE,
    default_equipment_type VARCHAR(50),
    opt_out               BOOLEAN DEFAULT FALSE,
    created_at            TIMESTAMPTZ DEFAULT NOW(),
    updated_at            TIMESTAMPTZ
);
```

#### `conversations`

```sql
CREATE TABLE conversations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id            UUID REFERENCES orders(id),
    customer_id         UUID REFERENCES customers(id),
    thread_message_id   VARCHAR(500),                   -- original email Message-ID for threading
    status              VARCHAR(50),                    -- open | resolved | waiting
    last_message_at     TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

#### `conversation_messages`

```sql
CREATE TABLE conversation_messages (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id  UUID NOT NULL REFERENCES conversations(id),
    direction        VARCHAR(10) NOT NULL,              -- inbound | outbound
    from_address     VARCHAR(255),
    to_address       VARCHAR(255),
    subject          TEXT,
    body_html        TEXT,
    body_text        TEXT,
    template_id      UUID REFERENCES email_templates(id),
    sent_at          TIMESTAMPTZ,
    delivery_status  VARCHAR(50)                        -- sent | bounced | delivered
);
```

#### `validation_results`

```sql
CREATE TABLE validation_results (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id     UUID NOT NULL REFERENCES orders(id),
    field_name   VARCHAR(100) NOT NULL,
    rule_name    VARCHAR(100),
    status       VARCHAR(20) NOT NULL,                  -- pass | fail | warning
    message      TEXT,
    evaluated_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `order_history`

```sql
CREATE TABLE order_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id        UUID NOT NULL REFERENCES orders(id),
    event_type      VARCHAR(100) NOT NULL,
    previous_status VARCHAR(50),
    new_status      VARCHAR(50),
    triggered_by    VARCHAR(20),                        -- agent | user | system
    actor_id        VARCHAR(255),
    detail_json     JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
-- Immutable: no UPDATE or DELETE permitted at application level
```

#### `agent_execution_logs`

```sql
CREATE TABLE agent_execution_logs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_type   VARCHAR(100) NOT NULL,                 -- email_intake | document_understanding | order_extraction | validation | communication | order_creation
    run_id       UUID NOT NULL,
    email_id     UUID REFERENCES emails(id),
    order_id     UUID REFERENCES orders(id),
    action       VARCHAR(100),
    status       VARCHAR(50),                           -- success | failure | retry
    input_tokens INTEGER,
    output_tokens INTEGER,
    duration_ms  INTEGER,
    llm_model    VARCHAR(100),
    error_detail TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

#### `audit_logs`

```sql
CREATE TABLE audit_logs (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_type     VARCHAR(20) NOT NULL,                -- user | agent | system
    actor_id       VARCHAR(255),
    action         VARCHAR(100) NOT NULL,
    entity_type    VARCHAR(100),
    entity_id      UUID,
    old_value_json JSONB,
    new_value_json JSONB,
    ip_address     INET,
    user_agent     TEXT
);
-- Immutable: no UPDATE or DELETE permitted at application level
CREATE INDEX idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor_id, timestamp);
```

#### `business_rules`

```sql
CREATE TABLE business_rules (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_name       VARCHAR(100) NOT NULL,
    field_name      VARCHAR(100),
    rule_type       VARCHAR(50),                        -- required_if | valid_enum | date_after | date_before | regex_match | address_valid | custom_js_expression
    rule_expression TEXT NOT NULL,
    error_message   TEXT,
    severity        VARCHAR(20) DEFAULT 'error',        -- error | warning
    escalate_on_fail BOOLEAN DEFAULT FALSE,
    active          BOOLEAN DEFAULT TRUE,
    priority        INTEGER NOT NULL,                   -- evaluation order (lower = first)
    created_by      UUID REFERENCES users(id),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### `field_configurations`

```sql
CREATE TABLE field_configurations (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_name             VARCHAR(100) UNIQUE NOT NULL,
    label                  VARCHAR(255) NOT NULL,        -- human-readable label for UI and emails
    is_mandatory           BOOLEAN DEFAULT FALSE,
    is_conditional         BOOLEAN DEFAULT FALSE,
    conditional_depends_on VARCHAR(100),                 -- field_name of dependency
    conditional_value      VARCHAR(255),                 -- value that triggers this field becoming mandatory
    display_order          INTEGER,
    active                 BOOLEAN DEFAULT TRUE
);
```

#### `email_templates`

```sql
CREATE TABLE email_templates (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_type       VARCHAR(50) NOT NULL,            -- missing_info | follow_up | acknowledgement | duplicate_notification
    name                VARCHAR(255) NOT NULL,
    subject_template    TEXT NOT NULL,
    body_html_template  TEXT NOT NULL,
    body_text_template  TEXT NOT NULL,
    variables           TEXT[],                          -- list of {{variable}} names used
    active              BOOLEAN DEFAULT TRUE,
    updated_by          UUID REFERENCES users(id),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);
```

#### `users`

```sql
CREATE TABLE users (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email        VARCHAR(255) UNIQUE NOT NULL,
    name         VARCHAR(255) NOT NULL,
    role         VARCHAR(50) NOT NULL,                   -- agent | supervisor | admin | readonly
    active       BOOLEAN DEFAULT TRUE,
    mfa_enabled  BOOLEAN DEFAULT FALSE,
    cognito_sub  VARCHAR(255) UNIQUE,
    last_login_at TIMESTAMPTZ,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 4. API Design

### 4.1 Design Principles

- RESTful design; all request/response bodies are JSON (`Content-Type: application/json`)
- All endpoints require `Authorization: Bearer <JWT_ACCESS_TOKEN>` header
- API versioning prefix: `/api/v1/`
- Pagination: all list endpoints accept `?page=1&limit=25`; response envelope: `{ data[], total_count, total_pages, page, limit }`
- Standard error envelope: `{ error: { code: string, message: string, field?: string, details?: object } }`
- POST endpoints for order creation and email sending accept `Idempotency-Key` header
- Rate limiting: 100 req/min per user; 1,000 req/min per IP

### 4.2 Endpoint Reference

#### Orders

| Method | Endpoint | Description | Min Role |
|---|---|---|---|
| GET | `/api/v1/orders` | List orders; supports filter, sort, pagination | Agent |
| POST | `/api/v1/orders` | Create order manually | Agent |
| GET | `/api/v1/orders/:id` | Order detail with confidence scores and history | Agent |
| PATCH | `/api/v1/orders/:id` | Partial update; changes logged | Agent |
| DELETE | `/api/v1/orders/:id` | Soft-delete → status: cancelled | Supervisor |
| POST | `/api/v1/orders/:id/approve` | Approve from HITL queue → triggers order creation | Agent |
| POST | `/api/v1/orders/:id/reject` | Reject order with `reason_code` | Agent |
| POST | `/api/v1/orders/:id/clone` | Clone order as new draft | Agent |
| GET | `/api/v1/orders/:id/history` | Order status change timeline | Agent |
| GET | `/api/v1/orders/:id/audit` | Full audit log entries for this order | Supervisor |

#### Emails

| Method | Endpoint | Description | Min Role |
|---|---|---|---|
| GET | `/api/v1/emails` | List processed emails with filter/pagination | Agent |
| GET | `/api/v1/emails/:id` | Email detail: body, attachments, extraction results | Agent |
| POST | `/api/v1/emails/:id/reclassify` | Reclassify email type; optionally reprocess | Agent |
| GET | `/api/v1/emails/:id/attachments/:aId/url` | Get presigned S3 download URL (15-min expiry) | Agent |

#### HITL Queues

| Method | Endpoint | Description | Min Role |
|---|---|---|---|
| GET | `/api/v1/queues/hitl` | List HITL queue items; filter by `queue_type` | Agent |
| GET | `/api/v1/queues/hitl/:orderId` | HITL review item detail with extracted fields | Agent |

#### Conversations

| Method | Endpoint | Description | Min Role |
|---|---|---|---|
| GET | `/api/v1/conversations` | List conversations; filter by `order_id` / `customer_id` | Agent |
| GET | `/api/v1/conversations/:id` | Full conversation thread | Agent |
| POST | `/api/v1/conversations/:id/reply` | Send email reply; accepts `template_id` or custom body | Agent |

#### Customers

| Method | Endpoint | Description | Min Role |
|---|---|---|---|
| GET | `/api/v1/customers` | List customers; search by name/email | Agent |
| POST | `/api/v1/customers` | Create customer profile | Supervisor |
| GET | `/api/v1/customers/:id` | Customer detail with order history summary | Agent |
| PATCH | `/api/v1/customers/:id` | Update customer profile and rules | Supervisor |

#### Reports

| Method | Endpoint | Description | Min Role |
|---|---|---|---|
| GET | `/api/v1/reports/dashboard` | Real-time KPI counters | Agent |
| GET | `/api/v1/reports/orders` | Order volume report; group by customer/status/date | Supervisor |
| GET | `/api/v1/reports/ai-performance` | Extraction accuracy, confidence trends, HITL rate | Supervisor |
| GET | `/api/v1/reports/stp-rate` | STP rate trend over configurable date range | Supervisor |

#### Administration

| Method | Endpoint | Description | Min Role |
|---|---|---|---|
| GET/POST/PATCH/DELETE | `/api/v1/admin/field-configs` | CRUD for field configuration settings | Admin |
| GET/POST/PATCH/DELETE | `/api/v1/admin/business-rules` | CRUD for business rule definitions | Admin |
| GET/POST/PATCH/DELETE | `/api/v1/admin/email-templates` | CRUD for email templates | Admin |
| GET/POST/PATCH/DELETE | `/api/v1/admin/users` | CRUD for platform user accounts | Admin |
| POST | `/api/v1/agent/replay/:emailId` | Replay full processing pipeline for an email | Admin |
| GET | `/api/v1/agent/runs` | List agent execution runs with filter | Admin |
| GET | `/api/v1/agent/runs/:runId` | Agent run detail: input, output, token usage, duration | Admin |
| GET | `/api/v1/health` | System health check (no auth required) | None |

---

## 5. Frontend Application Modules

The Order Entry Application is a React 18 + TypeScript SPA built with Vite and Tailwind CSS. All modules are role-gated via RBAC.

### 5.1 Dashboard Module

- Real-time KPI widgets (10 metrics); refresh every 30s via WebSocket
- Clickable metric cards navigate to Order Management with pre-applied filter
- STP Rate trend chart (30 days); downloadable as PNG
- Widgets: Total Orders, Pending, Awaiting Customer Response, Auto-Processed (STP), HITL Queue Depth, Completed, Failed, Avg E2E Time, Extraction Accuracy, STP Rate %

### 5.2 Order Management Module

- Paginated order list: 25/50/100 rows; sortable by any column
- Status color-coded badges: Created=green, Pending=yellow, Awaiting=orange, Failed=red, Cancelled=grey
- Full-text search across: Order Number, Customer Name, PO Number, Reference Number, Commodity
- Filter panel: Status, Date Range, Customer, Equipment Type, Freight Type, Confidence Score slider, Processing Mode
- Saved filter presets per user (localStorage + server sync)
- Export filtered results to CSV and PDF
- Order Detail View: grouped field sections, per-field confidence indicators, source annotation tooltip, original email side panel, status timeline
- Manual Order Creation: full form with address autocomplete, customer type-ahead, conditional fields, 30s auto-save draft

### 5.3 Inbox Module

- Paginated email list: From, Subject, Received Date, Classification badge, Linked Order Number, Processing Status
- Full email body rendered (HTML-sanitized); attachment list with type icon and download link
- In-browser PDF viewer (PDF.js); image lightbox; Excel/Word as extracted text
- Extraction Results Panel: per-field values with confidence badges; source annotation (document, page/cell)
- Reclassify action: corrects email type; triggers reprocessing
- Send to Review: routes email directly to HITL Validation Queue

### 5.4 Validation Queue Module

| Queue | Description | Priority | SLA Target |
|---|---|---|---|
| Confidence Review Queue | Orders with confidence 80–94% | Medium | Review within 2 hours |
| Validation Failure Queue | Missing mandatory fields or failed business rules | High | Review within 1 hour |
| Exception Queue | Confidence < 80%; full manual data re-entry | High | Review within 2 hours |
| Duplicate Review Queue | Potential duplicate orders | High | Review within 1 hour |
| Escalation Queue | Customer timeouts; repeated failures; admin escalations | Critical | Review within 30 minutes |

Each queue item: original email + attachments on left (resizable); extracted order form with confidence indicators on right; validation failure banner; sticky action bar (Approve / Reject / Send to Customer / Escalate / Discard).

### 5.5 Customer Communication Center

- Conversation list grouped by Order/Customer; unread count badge; search
- Full email thread in chronological order; inline attachment download
- Rich text compose with TipTap/Quill; recipient auto-populated; template selector with LLM variable auto-fill
- Response tracking: delivery status, read receipt, response received timestamp
- Customer Profile Panel sidebar: order history, avg response time, opt-out status

### 5.6 Audit & Activity Logs Module

| Log Type | Key Fields |
|---|---|
| Agent Action Log | timestamp, agent_type, run_id, action, order_id, email_id, duration_ms, status, error_detail |
| User Action Log | timestamp, user_id, role, action, entity_type, entity_id, old_value_json, new_value_json, ip_address |
| Order History Log | timestamp, order_id, event_type, previous_status, new_status, triggered_by, actor_id |
| Email Processing Log | timestamp, email_id, classification, classification_confidence, processing_duration_ms |
| Communication Log | timestamp, conversation_id, direction, from, to, template_used, delivery_status |
| Validation Log | timestamp, order_id, field_name, rule_name, result, error_message |

All logs searchable by entity ID, date range, actor, action type. Export to CSV and PDF. Retention: 7 years. Immutable records.

### 5.7 Administration Module

| Section | Configurable Items |
|---|---|
| Field Configuration | Mandatory/Optional/Conditional flags; conditional dependencies; human-readable labels; display order |
| Business Rules | Create/edit/delete rules; priority ordering; severity (error/warning); escalation behavior; enable/disable; test against sample data |
| Email Templates | Missing Info, Follow-up, Acknowledgement, Duplicate Notification; Handlebars syntax; HTML + plain-text; preview before save |
| Confidence Thresholds | Auto-Process, Human Review, Manual Entry, Auto-Communication thresholds; Customer Response Timeout; Follow-up Delay |
| Customer Profiles | Create/edit/delete customers; customer-specific rules; email domain whitelist; opt-out status |
| User Management | Create/edit/deactivate users; assign roles; reset passwords; view last login; notification preferences |
| Mailbox Configuration | OAuth for M365 / IMAP credentials; polling interval; reply-to address; test connection |
| Integration Settings | Address validation API key/provider; LLM provider + model; OCR configuration; SES sender identity |
| Notification Rules | CloudWatch alarm thresholds; SNS topics; alert recipients for queue depth, STP rate drops, failures |

---

## 6. Security Design

### 6.1 RBAC Permission Matrix

| Permission | ReadOnly | Agent | Supervisor | Admin |
|---|---|---|---|---|
| View orders and order details | ✓ | ✓ | ✓ | ✓ |
| Create / edit orders | | ✓ | ✓ | ✓ |
| Approve / reject HITL queue | | ✓ | ✓ | ✓ |
| Delete / cancel orders | | | ✓ | ✓ |
| Send customer emails | | ✓ | ✓ | ✓ |
| View conversations | | ✓ | ✓ | ✓ |
| View audit logs | | | ✓ | ✓ |
| Export data (CSV/PDF) | | | ✓ | ✓ |
| View AI performance reports | | | ✓ | ✓ |
| Configure business rules | | | | ✓ |
| Manage email templates | | | | ✓ |
| Manage field configurations | | | | ✓ |
| Manage users and roles | | | | ✓ |
| Replay agent runs | | | | ✓ |

### 6.2 Authentication & Authorization

- JWT via Amazon Cognito; 1-hour access token TTL; 7-day refresh token TTL
- Token revocation on logout via Redis blocklist
- MFA (TOTP) enforced for Supervisor and Admin roles; optional for Agent
- API Gateway Cognito Authorizer validates Bearer token on all protected endpoints
- RBAC enforced at both API Gateway level and backend service level

### 6.3 Infrastructure Security

- S3 attachments: private ACL; access only via presigned URLs with 15-minute expiry
- RDS: no public endpoint; VPC private subnets only; security group restricts to application tier
- AWS WAF on API Gateway: OWASP Core Rule Set v3.2; rate-based rules; SQL injection + XSS rules active
- All PII masked in CloudWatch logs (email shown as `j***@domain.com`)
- TLS 1.2+ enforced on all ALB listeners; HSTS with 1-year max-age

---

## 7. Observability Design

| Category | Tooling | Key Metrics / Alerts |
|---|---|---|
| Metrics | Amazon CloudWatch | `email_queue_depth`, `e2e_processing_ms`, `extraction_confidence_avg`, `order_creation_rate`, `llm_error_rate`, `api_error_rate_4xx_5xx` |
| Logging | CloudWatch Logs + structured JSON | All agent logs include: `run_id`, `email_id`, `order_id`, `duration_ms`, `status`, `error`; PII stripped |
| Distributed Tracing | AWS X-Ray | End-to-end trace per email: SQS ingestion → LLM call → DB write → EventBridge publish |
| Alerting | CloudWatch Alarms → SNS | Queue depth > 100 for 5 min; Error rate > 5% for 2 min; E2E time > 10 min; LLM circuit breaker open |
| Operational Dashboard | CloudWatch Dashboard | Order pipeline health; agent throughput; queue depths; confidence histogram; STP trend |
| Synthetic Monitoring | CloudWatch Synthetics | Submit test email every 15 min in staging; alert if not processed within 3 min |

---

## 8. Deployment Architecture

```
Internet
    │
    ▼
[AWS WAF]
    │
    ▼
[Application Load Balancer]
    ├── /api/*  → [API Gateway v2] → [Cognito Authorizer]
    │                                        │
    │                    ┌────────────────────┤
    │                    ▼                    ▼
    │          [Order Service]       [Email Service]
    │          [Validation Service]  [Communication Service]
    │          [Reporting Service]   (all on ECS Fargate, min 2 tasks per AZ)
    │
    └── /*      → [S3 Static Hosting / CloudFront] → React SPA
                                    │
                    ┌───────────────┤
                    ▼               ▼
             [ElastiCache     [RDS PostgreSQL
              Redis]           Multi-AZ]
                                    │
                              [Read Replica]
                              (reporting queries)

SQS Queues (ECS Fargate Workers, auto-scale 1–20 tasks):
  document-processing-queue  → Document Understanding Agent
  extraction-queue            → Order Extraction Agent
  validation-queue            → Validation Agent
  auto-process-queue          → Order Creation Agent
  hitl-queue                  → HITL routing (persisted to DB; UI polls)
  communication-queue         → Customer Communication Agent
  exception-queue             → HITL Exception Queue (persisted to DB)
  dead-letter-queues (DLQ)    → All queues have DLQ; 14-day retention; Admin replay

EventBridge (custom bus: order-platform-bus):
  order.created       → (stub) future TMS adapter
  order.updated       → downstream notification
  hitl.approved       → Order Creation Agent trigger
  email.classified    → routing decisions

S3 Buckets:
  attachments-{env}   → raw email attachments (versioned)
  extracted-text-{env}→ OCR / parsed text output
  exports-{env}       → CSV/PDF report exports
  static-{env}        → React SPA assets (CloudFront origin)
```
