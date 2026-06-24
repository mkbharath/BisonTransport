// --- Order Statuses ---
export const ORDER_STATUS = {
  EXTRACTED: "extracted",
  PENDING_REVIEW: "pending_review",
  AWAITING_CUSTOMER: "awaiting_customer",
  VALIDATED: "validated",
  ORDER_CREATED: "order_created",
  FAILED: "failed",
  CANCELLED: "cancelled",
} as const;

export type OrderStatus = (typeof ORDER_STATUS)[keyof typeof ORDER_STATUS];

// --- Email Classifications ---
export const EMAIL_CLASSIFICATION = {
  NEW_ORDER: "new_order",
  ORDER_UPDATE: "order_update",
  CUSTOMER_RESPONSE: "customer_response",
  CANCELLATION: "cancellation",
  OTHER: "other",
} as const;

export type EmailClassification =
  (typeof EMAIL_CLASSIFICATION)[keyof typeof EMAIL_CLASSIFICATION];

// --- Queue Names ---
export const QUEUES = {
  DOCUMENT_PROCESSING: "document-processing",
  EXTRACTION: "extraction",
  VALIDATION: "validation",
  AUTO_PROCESS: "auto-process",
  HITL: "hitl",
  COMMUNICATION: "communication",
  EXCEPTION: "exception",
} as const;

// --- HITL Queue Types ---
export const HITL_QUEUE_TYPE = {
  CONFIDENCE_REVIEW: "confidence_review",
  VALIDATION_FAILURE: "validation_failure",
  EXCEPTION: "exception",
  DUPLICATE_REVIEW: "duplicate_review",
  ESCALATION: "escalation",
} as const;

export type HitlQueueType = (typeof HITL_QUEUE_TYPE)[keyof typeof HITL_QUEUE_TYPE];

// --- Freight Types ---
export const FREIGHT_TYPE = {
  FTL: "ftl",
  LTL: "ltl",
  PARTIAL: "partial",
  INTERMODAL: "intermodal",
} as const;

export type FreightType = (typeof FREIGHT_TYPE)[keyof typeof FREIGHT_TYPE];

// --- Equipment Types ---
export const EQUIPMENT_TYPE = {
  DRY_VAN: "dry_van",
  FLATBED: "flatbed",
  REEFER: "reefer",
  STEP_DECK: "step_deck",
  TANKER: "tanker",
  LOWBOY: "lowboy",
  CONESTOGA: "conestoga",
  OTHER: "other",
} as const;

export type EquipmentType = (typeof EQUIPMENT_TYPE)[keyof typeof EQUIPMENT_TYPE];

// --- User Roles ---
export const USER_ROLE = {
  READONLY: "readonly",
  AGENT: "agent",
  SUPERVISOR: "supervisor",
  ADMIN: "admin",
} as const;

export type UserRole = (typeof USER_ROLE)[keyof typeof USER_ROLE];

// --- Confidence Thresholds (defaults) ---
export const DEFAULT_THRESHOLDS = {
  AUTO_PROCESS: 95,
  HUMAN_REVIEW: 80,
  AUTO_COMMUNICATION: 70,
  CUSTOMER_RESPONSE_TIMEOUT_HOURS: 48,
  FOLLOWUP_DELAY_HOURS: 24,
  DUPLICATE_DETECTION_WINDOW_HOURS: 72,
} as const;

// --- Processing Modes ---
export const PROCESSING_MODE = {
  AUTO: "auto",
  HITL_REVIEW: "hitl_review",
  MANUAL_ENTRY: "manual_entry",
} as const;

export type ProcessingMode = (typeof PROCESSING_MODE)[keyof typeof PROCESSING_MODE];
