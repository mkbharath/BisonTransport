import type {
  OrderStatus,
  EmailClassification,
  FreightType,
  EquipmentType,
  UserRole,
  ProcessingMode,
  HitlQueueType,
} from "./constants";

// --- API Response Envelope ---
export interface ApiListResponse<T> {
  data: T[];
  total_count: number;
  total_pages: number;
  page: number;
  limit: number;
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    field?: string;
    details?: Record<string, unknown>;
  };
}

// --- Address ---
export interface Address {
  line1: string;
  line2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
}

// --- Time Window ---
export interface TimeWindow {
  start: string; // HH:MM
  end: string; // HH:MM
}

// --- Order ---
export interface Order {
  id: string;
  order_number: string;
  source_email_id: string | null;
  customer_id: string | null;
  status: OrderStatus;
  overall_confidence_score: number | null;
  processing_mode: ProcessingMode | null;
  field_confidence_scores: Record<string, number> | null;
  // Customer Info
  customer_name: string | null;
  customer_external_id: string | null;
  contact_name: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  // Pickup
  pickup_location_name: string | null;
  pickup_address: Address | null;
  pickup_date: string | null;
  pickup_time_window: TimeWindow | null;
  pickup_instructions: string | null;
  // Delivery
  delivery_location_name: string | null;
  delivery_address: Address | null;
  delivery_date: string | null;
  delivery_time_window: TimeWindow | null;
  delivery_instructions: string | null;
  // Shipment
  customer_order_number: string | null;
  reference_number: string | null;
  po_number: string | null;
  commodity: string;
  freight_type: FreightType | null;
  total_weight: number | null;
  weight_unit: string | null;
  dimensions: string | null;
  total_quantity: number | null;
  num_pallets: number | null;
  stackable: boolean;
  // Transportation
  equipment_type: EquipmentType | null;
  truck_size: string | null;
  temperature_min_c: number | null;
  temperature_max_c: number | null;
  hazmat_indicator: boolean;
  hazmat_un_number: string | null;
  hazmat_class: string | null;
  special_handling_instructions: string | null;
  liftgate_required: boolean;
  team_drive_required: boolean;
  twic_card_required: boolean;
  // Additional
  notes: string | null;
  internal_comments: string | null;
  attachment_references: string[] | null;
  reviewed_by_user_id: string | null;
  reviewed_at: string | null;
  created_at: string;
  updated_at: string | null;
}

// --- Email ---
export interface Email {
  id: string;
  message_id: string;
  thread_id: string | null;
  from_address: string;
  to_address: string;
  subject: string | null;
  body_text: string | null;
  body_html: string | null;
  received_at: string;
  processed_at: string | null;
  classification: EmailClassification | null;
  classification_confidence: number | null;
  status: string;
  linked_order_id: string | null;
  conversation_id: string | null;
  created_at: string;
}

// --- Email Attachment ---
export interface EmailAttachment {
  id: string;
  email_id: string;
  file_name: string;
  file_type: string | null;
  file_size_bytes: number | null;
  s3_key: string;
  ocr_confidence: number | null;
  processing_status: string | null;
}

// --- Customer ---
export interface Customer {
  id: string;
  name: string;
  external_id: string | null;
  email_domains: string[];
  always_human_review: boolean;
  default_equipment_type: string | null;
  opt_out: boolean;
  created_at: string;
  updated_at: string | null;
}

// --- Conversation ---
export interface Conversation {
  id: string;
  order_id: string | null;
  customer_id: string | null;
  thread_message_id: string | null;
  status: string;
  last_message_at: string | null;
  created_at: string;
}

// --- Conversation Message ---
export interface ConversationMessage {
  id: string;
  conversation_id: string;
  direction: "inbound" | "outbound";
  from_address: string | null;
  to_address: string | null;
  subject: string | null;
  body_html: string | null;
  body_text: string | null;
  template_id: string | null;
  sent_at: string | null;
  delivery_status: string | null;
}

// --- Validation Result ---
export interface ValidationResult {
  id: string;
  order_id: string;
  field_name: string;
  rule_name: string | null;
  status: "pass" | "fail" | "warning";
  message: string | null;
  evaluated_at: string;
}

// --- Order History Event ---
export interface OrderHistoryEvent {
  id: string;
  order_id: string;
  event_type: string;
  previous_status: string | null;
  new_status: string | null;
  triggered_by: "agent" | "user" | "system";
  actor_id: string | null;
  detail_json: Record<string, unknown> | null;
  created_at: string;
}

// --- HITL Queue Item ---
export interface HitlQueueItem {
  order_id: string;
  order_number: string;
  customer_name: string | null;
  queue_type: HitlQueueType;
  overall_confidence_score: number | null;
  time_in_queue_minutes: number;
  priority: "low" | "medium" | "high" | "critical";
  validation_failures: ValidationResult[];
}

// --- Dashboard KPIs ---
export interface DashboardKPIs {
  total_orders: number;
  pending_orders: number;
  awaiting_customer: number;
  auto_processed: number;
  stp_rate_percent: number;
  hitl_queue_depth: number;
  completed_orders: number;
  failed_orders: number;
  avg_e2e_processing_minutes: number;
  extraction_accuracy_percent: number;
}

// --- User ---
export interface User {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  active: boolean;
  mfa_enabled: boolean;
  last_login_at: string | null;
  created_at: string;
}

// --- Auth ---
export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
}
