# Requirements — AI-Powered Order Intake & Order Entry Automation Platform

**Version:** 1.0  
**Domain:** Transportation & Logistics  
**Classification:** Confidential  
**Date:** June 2026

---

## 1. Introduction

### 1.1 Purpose

This document defines the functional and non-functional requirements for the AI-Powered Order Intake & Order Entry Automation Platform (referred to as "the Platform"). The Platform automates the end-to-end process of receiving customer transportation orders via email, extracting and validating order data using an AI agent pipeline, and creating orders in a web-based Order Entry Application — eliminating manual data entry.

### 1.2 Background

The client is a Transportation & Logistics company receiving customer transportation orders exclusively via email. Each order may arrive as plain text or in attachments (PDF, Excel, Word, scanned images). The current manual process is slow, error-prone, and resource-intensive, with a human error rate of 8–12% and processing time of 45–90 minutes per order.

### 1.3 Scope

This specification covers the Proof of Concept (PoC) scope:

**In Scope:**
- Email ingestion from a monitored mailbox (IMAP / Microsoft 365)
- AI extraction from email body, PDF, Excel, Word, PNG/JPG/TIFF images, and scanned documents
- Full order schema extraction covering 60+ fields across 6 categories
- Automated mandatory-field and business-rule validation
- Automated customer email generation for missing information requests
- Automated order creation in the Order Entry Application
- Human-in-the-Loop (HITL) review queue for low-confidence and failed validations
- Web-based Order Entry Application with 7 functional modules
- Audit logging for all agent and user actions
- REST API layer for all platform operations
- Reporting dashboard (operational, AI, and business metrics)
- Administration module for configuring fields, rules, and email templates

**Out of Scope (PoC):**
- Direct TMS integration (Order Entry Application acts as TMS substitute)
- EDI / AS2 ingestion, customer portal, mobile applications, ERP integration
- Carrier dispatch, load tendering, rate quoting, or pricing automation

---

## 2. User Personas

### 2.1 Alex — Operations Agent (Primary User)
- **Goal:** Process orders quickly and accurately with minimal manual work
- **Key Tasks:** Review AI-extracted orders; manage HITL queue; correct extraction errors; create orders manually when needed
- **Tech Comfort:** Medium

### 2.2 Morgan — Operations Supervisor
- **Goal:** Monitor team throughput; ensure SLA compliance; reduce error rates
- **Key Tasks:** Dashboard monitoring; approve escalations; configure business rules; generate reports
- **Tech Comfort:** Medium-High

### 2.3 Sam — System Administrator
- **Goal:** Configure and maintain the platform without developer involvement
- **Key Tasks:** Configure mandatory fields, business rules, and email templates; manage user access; review audit logs
- **Tech Comfort:** High

### 2.4 Casey — Customer (External Stakeholder)
- **Goal:** Submit transportation orders easily and receive fast acknowledgement
- **Key Tasks:** Send order email; respond to missing-information requests; receive order acknowledgements
- **Tech Comfort:** Low-Medium (email only; no platform login required)

---

## 3. Functional Requirements

### 3.1 Email Intake Agent

#### US-001: Email Polling
**As an** Email Intake Agent, **I want to** poll the monitored mailbox every 60 seconds and retrieve unread emails, **so that** orders are detected and processing begins in near real-time without manual checking.

**Acceptance Criteria:**
- [ ] Agent polls at configured interval (default 60s; configurable 30–300s in Administration)
- [ ] New emails retrieved; marked as 'Processing' to prevent duplicate ingestion
- [ ] Email metadata (From, To, Subject, Date, Message-ID, Thread-ID) stored in `emails` table
- [ ] All attachments downloaded to S3; file type, size, and S3 key recorded in `email_attachments` table
- [ ] Processing latency from email receipt to extraction queue < 2 minutes (P95)

#### US-002: Email Classification
**As an** Email Intake Agent, **I want to** classify incoming emails as New Order, Order Update, Customer Response, Cancellation, or Other, **so that** only relevant emails trigger order processing, preventing noise in the pipeline.

**Acceptance Criteria:**
- [ ] Classification uses LLM with subject, sender, body snippet (first 500 chars), and thread context as input
- [ ] Classification confidence score stored in `emails.classification_confidence`
- [ ] 'Other' emails logged but not forwarded to the processing queue
- [ ] Misclassification correctable by agent via Inbox module Reclassify action
- [ ] Reclassification triggers reprocessing of the email

---

### 3.2 Document Understanding Agent

#### US-003: PDF Attachment Extraction
**As a** Document Understanding Agent, **I want to** extract text and structured data from PDF attachments including scanned documents, **so that** order details embedded in PDFs are captured automatically without manual reading.

**Acceptance Criteria:**
- [ ] Digital PDFs (with selectable text layer) parsed directly without OCR
- [ ] Scanned/image-based PDFs detected automatically (by absence of text layer) and processed via AWS Textract
- [ ] Tables within PDFs extracted as structured key-value pairs
- [ ] Multi-page PDFs fully processed across all pages
- [ ] Per-field confidence scores from Textract stored with extraction results

#### US-004: Excel and Word Attachment Extraction
**As a** Document Understanding Agent, **I want to** extract data from Excel (XLSX/XLS) and Word (DOCX/DOC) attachments, **so that** orders submitted in spreadsheet or document format are processed automatically.

**Acceptance Criteria:**
- [ ] XLSX/XLS: all sheets processed; tables identified; header rows detected via LLM; data mapped to order schema
- [ ] DOCX/DOC: full text extracted including tables; content passed to Order Extraction Agent
- [ ] Extraction confidence scores assigned per field
- [ ] Password-protected files flagged as unable to process; agent notified; customer optionally asked to re-send without password

---

### 3.3 Order Extraction Agent

#### US-005: Structured Data Extraction from Unstructured Text
**As an** Order Extraction Agent, **I want to** extract structured order data from unstructured text using an LLM, **so that** free-text order emails are converted to structured order records without any manual data entry.

**Acceptance Criteria:**
- [ ] LLM extracts all 60+ fields defined in the order schema from the combined document corpus
- [ ] Values normalized: dates to ISO 8601, weights to configured default unit, addresses de-abbreviated
- [ ] Each field receives an individual confidence score (0–100)
- [ ] Fields not found return null value with 0 confidence score
- [ ] Overall order confidence = weighted average of mandatory field confidence scores
- [ ] Processing returns valid JSON matching order schema on every attempt (self-correction retry on malformed output, up to 2 retries)

---

### 3.4 Validation Agent

#### US-006: Business Rule Validation
**As a** Validation Agent, **I want to** validate all extracted order fields against configured business rules, **so that** invalid or incomplete orders are caught automatically before order creation, reducing downstream errors.

**Acceptance Criteria:**
- [ ] All mandatory fields checked for presence (non-null, non-empty)
- [ ] Field-level business rules applied in configured priority order
- [ ] Address validation performed via external API (SmartyStreets or Google Maps Geocoding)
- [ ] Duplicate detection: same customer + pickup date + delivery postal code within 72 hours flagged as potential duplicate
- [ ] Validation results stored per field: `field_name`, `rule_name`, `status` (pass/fail/warning), `error_message`
- [ ] Confidence routing applied: >= 95% auto-process; 80–94% HITL; < 80% manual entry queue

---

### 3.5 Customer Communication Agent

#### US-007: Automated Missing-Information Email
**As a** Customer Communication Agent, **I want to** generate and send a professional missing-information email to the customer within 5 minutes of detecting mandatory field gaps, **so that** customers are contacted immediately without waiting for an operations agent, reducing cycle time.

**Acceptance Criteria:**
- [ ] Email generated using configurable template; lists specific missing field names in plain English
- [ ] Sent from configured reply-to address within 5 minutes of validation failure detection
- [ ] Outbound email logged in `conversations` table linked to the order
- [ ] Order status set to 'Awaiting Customer Response' with configurable timeout (default 48 hours)
- [ ] If no response within timeout period, order escalated to human Escalation Queue with agent notification
- [ ] Generated email content is readable and professional; verified by test recipient in UAT

---

### 3.6 Order Creation Agent

#### US-008: Automatic Order Creation
**As an** Order Creation Agent, **I want to** create an order record automatically when all mandatory fields are validated and confidence meets the auto-process threshold, **so that** orders are created in the system without any manual TMS data entry.

**Acceptance Criteria:**
- [ ] Order inserted with status 'Active'; all 60+ extracted/validated fields populated
- [ ] Unique Order Number generated in format `ORD-YYYYMMDD-XXXXX` (zero-padded, auto-incremented per day)
- [ ] Order acknowledgement email sent to customer within 2 minutes of creation
- [ ] Order creation event published to EventBridge for future TMS integration
- [ ] Idempotency: same source email + customer order number cannot create duplicate orders
- [ ] On DB failure: 3 retries with exponential backoff (2s, 4s, 8s); persistent failure routes to HITL queue with error detail

---

### 3.7 Human-in-the-Loop (HITL) Workflow

#### US-009: HITL Validation Queue Review
**As an** Operations Agent Alex, **I want to** review and correct low-confidence orders in the Validation Queue and approve them for order creation, **so that** I can fix AI extraction errors efficiently without re-entering all data, and the correction is tracked for AI improvement.

**Acceptance Criteria:**
- [ ] Queue displays orders with confidence 80–94% or validation failures, sorted by priority (high → low)
- [ ] Each queue item shows: original email body + attachment viewer on left; extracted field form with per-field confidence color indicators on right (green >= 90%, yellow 70–89%, red < 70%)
- [ ] All fields are inline-editable; validation rules enforce on field blur
- [ ] Approve button triggers Order Creation Agent; Reject button presents options: Send Missing-Info Email, Discard
- [ ] All agent corrections recorded: original AI value, corrected value, agent user ID, timestamp
- [ ] Processing time in HITL queue < 30 minutes average

---

### 3.8 Operations Dashboard

#### US-010: Real-Time Operational Dashboard
**As an** Operations Supervisor Morgan, **I want to** view a real-time operational dashboard, **so that** I can monitor the order pipeline health and identify bottlenecks without generating manual reports.

**Acceptance Criteria:**
- [ ] Dashboard loads in < 3 seconds on first visit; < 1 second on subsequent visits (cached)
- [ ] Displays: Total Orders (day/week/month toggle), Pending, Awaiting Customer Response, Auto-Processed (STP), HITL Queue depth, Completed, Failed, Avg E2E Processing Time, STP Rate %
- [ ] Metrics refresh every 30 seconds via WebSocket or polling
- [ ] Clicking any metric card navigates to Order Management with the corresponding pre-applied filter
- [ ] STP Rate trend chart shows last 30 days; downloadable as PNG

---

## 4. Order Schema — Field Definitions

All fields are configurable as Mandatory, Optional, or Conditional via the Administration module.

### 4.1 Customer Information

| Field | Type | Mandatory | Validation Rule |
|---|---|---|---|
| Customer Name | String (255) | Yes | Non-empty; matched against known customer list if available |
| Customer ID | String (50) | Conditional | Required if Customer Name does not uniquely match a customer profile |
| Contact Name | String (255) | Yes | Non-empty string |
| Contact Email | String (255) | Yes | Valid email format (RFC 5321) |
| Contact Phone | String (50) | Optional | E.164 format preferred; normalized on extraction |

### 4.2 Pickup Information

| Field | Type | Mandatory | Validation Rule |
|---|---|---|---|
| Pickup Location Name | String (255) | Yes | Non-empty string |
| Pickup Address Line 1 | String (255) | Yes | Non-empty; validated via address validation API |
| Pickup City | String (100) | Yes | Non-empty string |
| Pickup State/Province | String (50) | Yes | Valid state or province code |
| Pickup Postal Code | String (20) | Yes | Valid format for country |
| Pickup Country | String (50) | Yes | ISO 3166-1 country code; defaults to CA or US |
| Pickup Date | Date | Yes | Must be today or a future date; normalized to YYYY-MM-DD |
| Pickup Time Window Start | Time | Optional | HH:MM 24-hour format |
| Pickup Time Window End | Time | Optional | Must be after Start if both provided |
| Pickup Instructions | Text | Optional | Free text special instructions |

### 4.3 Delivery Information

| Field | Type | Mandatory | Validation Rule |
|---|---|---|---|
| Delivery Location Name | String (255) | Yes | Non-empty string |
| Delivery Address Line 1 | String (255) | Yes | Non-empty; validated via address validation API |
| Delivery City | String (100) | Yes | Non-empty string |
| Delivery State/Province | String (50) | Yes | Valid state or province code |
| Delivery Postal Code | String (20) | Yes | Valid format for country |
| Delivery Country | String (50) | Yes | ISO 3166-1 country code |
| Delivery Date | Date | Yes | On or after Pickup Date; normalized to YYYY-MM-DD |
| Delivery Time Window Start | Time | Optional | HH:MM 24-hour format |
| Delivery Time Window End | Time | Optional | Must be after Start if both provided |
| Delivery Instructions | Text | Optional | Free text special instructions |

### 4.4 Shipment Information

| Field | Type | Mandatory | Validation Rule |
|---|---|---|---|
| Customer Order Number | String (100) | Optional | Used as primary key for duplicate detection |
| Reference Number | String (100) | Optional | Carrier or broker reference |
| PO Number | String (100) | Optional | Customer purchase order number |
| Commodity Description | Text | Yes | Non-empty free text |
| Freight Type | Enum | Yes | FTL \| LTL \| Partial \| Intermodal |
| Total Weight | Decimal | Yes | Positive number; unit normalized to lbs or kg |
| Weight Unit | Enum | Yes | LBS \| KGS; defaults to LBS if not specified |
| Dimensions (L x W x H) | String (100) | Optional | Format: LxWxH with unit |
| Total Quantity / Pieces | Integer | Optional | Positive integer |
| Number of Pallets | Integer | Conditional | Required for FTL and LTL |
| Stackable | Boolean | Optional | Y/N; defaults to N |

### 4.5 Transportation Details

| Field | Type | Mandatory | Validation Rule |
|---|---|---|---|
| Equipment Type | Enum | Yes | Dry Van \| Flatbed \| Reefer \| Step Deck \| Tanker \| Lowboy \| Conestoga \| Other |
| Truck Size | Enum | Optional | 53ft \| 48ft \| Straight Truck \| Sprinter \| B-Train \| Other |
| Temperature Min (°C) | Decimal | Conditional | Required if Equipment Type = Reefer |
| Temperature Max (°C) | Decimal | Conditional | Required if Equipment Type = Reefer; must be >= Min |
| Hazmat Indicator | Boolean | Yes | Y/N; defaults to N |
| UN Number | String (10) | Conditional | Required if Hazmat = Y; format UN + 4 digits |
| Hazmat Class | String (50) | Conditional | Required if Hazmat = Y; valid DOT hazmat class |
| Special Handling Instructions | Text | Optional | Free text |
| Liftgate Required | Boolean | Optional | Y/N; defaults to N |
| Team Drive Required | Boolean | Optional | Y/N; defaults to N |
| TWIC Card Required | Boolean | Optional | Y/N; defaults to N |

### 4.6 Additional / System Fields

| Field | Type | Mandatory | Notes |
|---|---|---|---|
| General Notes | Text | Optional | From email body or attachment notes |
| Internal Comments | Text | Optional | Agent-only; never shared with customer |
| Attachment References | Array[String] | Optional | File names of all processed attachments |
| Source Email ID | UUID | System | Auto-populated; immutable |
| Extraction Confidence Score | Decimal (0-100) | System | Overall weighted AI confidence |
| Processing Status | Enum | System | Extracted \| Pending Review \| Awaiting Customer \| Validated \| Order Created \| Failed |

---

## 5. HITL Trigger Conditions

| Trigger Condition | Queue | Priority | Configurable |
|---|---|---|---|
| Confidence 80–94% | Confidence Review Queue | Medium | Yes |
| Confidence < 80% | Exception Queue (Manual Entry) | High | Yes |
| Missing mandatory field(s) | Validation Failure Queue | High | Yes |
| Business rule validation failure | Validation Failure Queue | High | Yes |
| Potential duplicate detected | Duplicate Review Queue | High | Yes |
| Customer non-response timeout | Escalation Queue | Critical | Yes |
| Agent processing exception | Exception Queue | High | No |
| Hazmat Indicator = Y | Validation Failure Queue | High | Yes |
| Customer profile: always HITL | Confidence Review Queue | High | Yes |
| Supervisor manual escalation | Escalation Queue | Critical | No |

---

## 6. Configurable Thresholds

| Parameter | Default | Configurable Range | Description |
|---|---|---|---|
| Auto-Process Threshold | 95% | 85%–100% | Minimum confidence for fully automatic order creation |
| Human Review Lower Bound | 80% | 60%–94% | Confidence below this triggers Exception Queue |
| Auto-Communication Threshold | 70% | 50%–100% | Minimum confidence to send automated missing-info email |
| Customer Response Timeout | 48 hours | 4h–168h | Hours before auto-escalating unanswered customer request |
| Follow-up Email Delay | 24 hours | 1h–72h | Hours before sending first automated follow-up |
| Duplicate Detection Window | 72 hours | 1h–720h | Lookback period for duplicate detection |
| Max HITL Queue Age Before Critical | 4 hours | 1h–24h | Time before queue item priority escalates to Critical |

---

## 7. Non-Functional Requirements

### 7.1 Performance SLAs

| Metric | Target | Measurement |
|---|---|---|
| Email detection latency | < 2 minutes (P95) | CloudWatch: `email_detection_latency_ms` |
| Document extraction time | < 90 seconds per email (body + up to 5 attachments) | CloudWatch: `extraction_duration_ms` |
| Order creation time | < 30 seconds after validation pass | CloudWatch: `order_creation_duration_ms` |
| End-to-end (auto-processed orders) | < 5 minutes total (P95) | CloudWatch: `e2e_processing_ms` |
| API response time | < 500ms (P95) for all CRUD operations | APM: P95 response time per endpoint |
| Dashboard load time | < 3 seconds on first visit | Synthetic canary: page load time |
| Concurrent email processing | 20 emails simultaneously | Load test: 20 parallel workers |

### 7.2 Scalability

- All backend services stateless; horizontally scalable on ECS Fargate with auto-scaling
- Email processing via SQS; consumers auto-scale from 1 to 20 ECS tasks based on queue depth
- PostgreSQL RDS Multi-AZ with read replica for reporting; PgBouncer connection pooling
- Target sustained throughput: 500 emails/hour; burst: 1,000 emails/hour for up to 15 minutes

### 7.3 Reliability & Availability

- Target uptime: 99.5% monthly
- Email processing uptime: 99.9% (critical path; secondary polling worker in standby)
- All agent operations: 3 retries with exponential backoff; persistent failures to SQS DLQ
- Circuit breaker on LLM API calls: open after 5 consecutive failures within 60s

### 7.4 Security

- Authentication: JWT tokens via Amazon Cognito; MFA enforced for Supervisor and Admin roles
- Authorization: RBAC enforced at API Gateway and backend service level
- Encryption at rest: AES-256 on RDS; SSE-S3 on S3
- All credentials in AWS Secrets Manager with 90-day automatic rotation
- PII masked in all application logs

### 7.5 Compliance & Data Governance

- Data retention: order records 7 years; email body/attachments 2 years; audit logs 7 years
- PIPEDA/GDPR readiness: PII deletion on verified request within 30 days
- Audit trail: immutable append-only log; no update or delete operations permitted at application level
- Hazmat orders: mandatory HITL review regardless of confidence threshold

---

## 8. Acceptance Criteria (PoC Sign-Off)

| ID | Acceptance Criterion | Test Method |
|---|---|---|
| AC-001 | System detects and ingests a new order email within 2 minutes of receipt | CloudWatch log timestamp measurement |
| AC-002 | Order data extracted from email body with >= 90% field accuracy on 50-email test dataset | AI test against labeled ground truth |
| AC-003 | Order data extracted from PDF attachments with >= 85% field accuracy on 30-sample test set | AI test: labeled PDF samples |
| AC-004 | Order data extracted from image/scanned documents with >= 80% accuracy on 20-sample test set | AI test: labeled image samples |
| AC-005 | All mandatory field validation rules fire correctly for 100% of defined test cases | Functional test: submit order violating each rule |
| AC-006 | Missing-information email generated and sent within 5 minutes of validation failure | Functional test: measure outbound email timestamp |
| AC-007 | Customer response re-processed and order status updated within 3 minutes of reply receipt | Functional test: reply to thread; measure reprocessing time |
| AC-008 | Orders with >= 95% confidence and all mandatory fields auto-created without human intervention | Functional test: submit 10 perfect orders |
| AC-009 | Orders with 80–94% confidence appear in HITL Confidence Review Queue within 2 minutes | Functional test: submit low-confidence order |
| AC-010 | Duplicate order detection fires for same customer + pickup date + delivery postal code within 72h | Functional test: submit identical order twice |
| AC-011 | Agent can review, correct, and approve a HITL queue item end-to-end in the UI | UAT: agent reviews queue item; order created; audit logged |
| AC-012 | All 7 application modules accessible and functional with correct RBAC enforcement | UAT: walkthrough with Agent, Supervisor, and Admin roles |
| AC-013 | All user and agent actions recorded in audit logs with actor, timestamp, and changed values | Functional test: perform 20 defined actions; verify each entry |
| AC-014 | Admin can configure a new mandatory field and Validation Agent enforces it on next order | UAT: admin adds field; submit order without it; verify rejection |
| AC-015 | API response time (P95) < 500ms under 50 concurrent users for all primary CRUD endpoints | k6 load test: 50 VUs for 5 minutes |

---

## 9. Success Metrics (KPI Framework)

| KPI | Target | Measurement |
|---|---|---|
| Straight-Through Processing (STP) Rate | >= 80% | % of orders auto-created without HITL |
| Overall Extraction Accuracy | >= 90% | % of fields correctly extracted |
| Mandatory Field Accuracy | >= 95% | % of mandatory fields correct on auto-processed orders |
| Avg E2E Time (Auto-Processed) | < 5 minutes | Email receipt → order acknowledgement |
| Avg E2E Time (HITL Path) | < 30 minutes | Email receipt → order creation via agent review |
| Human Intervention Rate | <= 20% | % of orders routed to HITL or manual entry |
| Manual Effort Reduction | >= 50% | Ops agent hours pre-PoC vs. post-PoC |
| Order Creation Success Rate | >= 99% | % of orders reaching 'Order Created' status |
| System Availability | >= 99.5% | Uptime monitored via CloudWatch |
| Email Processing Latency P95 | < 2 minutes | P95 time: email receipt → extraction queue entry |
