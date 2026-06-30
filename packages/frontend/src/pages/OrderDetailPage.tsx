import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { getOrder, updateOrder } from "../lib/api";
import { ArrowLeft, CheckCircle, Clock, AlertTriangle, XCircle, Pencil, Save, X } from "lucide-react";

// --- Utility types ---

interface Address {
  line1?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
}

// --- Sub-components ---

function ConfidenceBadge({ score }: { score: number | null }) {
  if (score == null) return <span className="text-gray-300 text-xs">—</span>;
  const color =
    score >= 90
      ? "bg-green-100 text-green-700 border-green-200"
      : score >= 70
        ? "bg-yellow-100 text-yellow-700 border-yellow-200"
        : "bg-red-100 text-red-700 border-red-200";
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${color}`}>
      {score.toFixed(1)}%
    </span>
  );
}

function CircularConfidence({ score }: { score: number | null }) {
  if (score == null) return null;
  const circumference = 2 * Math.PI * 18;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 90 ? "#10b981" : score >= 70 ? "#f59e0b" : "#ef4444";
  return (
    <div className="relative w-12 h-12 flex-shrink-0">
      <svg className="w-12 h-12 -rotate-90" viewBox="0 0 40 40">
        <circle cx="20" cy="20" r="18" fill="none" stroke="#e5e7eb" strokeWidth="3" />
        <circle
          cx="20"
          cy="20"
          r="18"
          fill="none"
          stroke={color}
          strokeWidth="3"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-gray-700">
        {score.toFixed(0)}%
      </span>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const statusConfig: Record<string, { icon: typeof CheckCircle; bg: string }> = {
    order_created: { icon: CheckCircle, bg: "bg-green-50 text-green-700 border-green-200" },
    extracted: { icon: Clock, bg: "bg-blue-50 text-blue-700 border-blue-200" },
    pending_review: { icon: AlertTriangle, bg: "bg-yellow-50 text-yellow-700 border-yellow-200" },
    awaiting_customer: { icon: Clock, bg: "bg-orange-50 text-orange-700 border-orange-200" },
    validated: { icon: CheckCircle, bg: "bg-indigo-50 text-indigo-700 border-indigo-200" },
    failed: { icon: XCircle, bg: "bg-red-50 text-red-700 border-red-200" },
  };
  const config = statusConfig[status] || { icon: Clock, bg: "bg-gray-50 text-gray-600 border-gray-200" };
  const Icon = config.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${config.bg}`}>
      <Icon className="w-3.5 h-3.5" />
      {status?.replace(/_/g, " ")}
    </span>
  );
}

const inputClassName =
  "w-full rounded-md border border-gray-300 px-2.5 py-1.5 text-sm text-gray-900 shadow-sm focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500 outline-none transition-colors";

const selectClassName =
  "w-full rounded-md border border-gray-300 px-2.5 py-1.5 text-sm text-gray-900 shadow-sm focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500 outline-none transition-colors bg-white";

function FieldRow({
  label,
  value,
  confidence,
  editing,
  fieldKey,
  inputType = "text",
  options,
  editValue,
  onEditChange,
}: {
  label: string;
  value: unknown;
  confidence?: number;
  editing?: boolean;
  fieldKey?: string;
  inputType?: "text" | "select" | "checkbox" | "date" | "textarea";
  options?: { value: string; label: string }[];
  editValue?: unknown;
  onEditChange?: (key: string, val: unknown) => void;
}) {
  if (editing && fieldKey && onEditChange) {
    let input: React.ReactNode;

    if (inputType === "select" && options) {
      input = (
        <select
          className={selectClassName}
          value={(editValue as string) || ""}
          onChange={(e) => onEditChange(fieldKey, e.target.value)}
        >
          <option value="">— Select —</option>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      );
    } else if (inputType === "checkbox") {
      input = (
        <label className="inline-flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            className="w-4 h-4 rounded border-gray-300 text-amber-500 focus:ring-amber-500/40"
            checked={!!editValue}
            onChange={(e) => onEditChange(fieldKey, e.target.checked)}
          />
          <span className="text-sm text-gray-700">{editValue ? "Yes" : "No"}</span>
        </label>
      );
    } else if (inputType === "textarea") {
      input = (
        <textarea
          className={inputClassName + " min-h-[60px] resize-y"}
          value={(editValue as string) || ""}
          onChange={(e) => onEditChange(fieldKey, e.target.value)}
          rows={2}
        />
      );
    } else {
      input = (
        <input
          type={inputType === "date" ? "date" : "text"}
          className={inputClassName}
          value={(editValue as string) || ""}
          onChange={(e) => onEditChange(fieldKey, e.target.value)}
        />
      );
    }

    return (
      <div className="flex items-start py-2.5 border-b border-gray-100 last:border-0">
        <span className="w-44 text-sm text-gray-500 flex-shrink-0 pt-1.5">{label}</span>
        <div className="flex-1">{input}</div>
        {confidence !== undefined && (
          <div className="ml-2 pt-1.5">
            <ConfidenceBadge score={confidence} />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex items-center py-2.5 border-b border-gray-100 last:border-0">
      <span className="w-44 text-sm text-gray-500 flex-shrink-0">{label}</span>
      <span className="flex-1 text-sm text-gray-900 font-medium">
        {value != null && value !== "" ? String(value) : <span className="text-gray-300 italic font-normal">Not provided</span>}
      </span>
      {confidence !== undefined && <ConfidenceBadge score={confidence} />}
    </div>
  );
}

function AddressFields({
  prefix,
  address,
  editing,
  editValues,
  onEditChange,
}: {
  prefix: "pickup_address" | "delivery_address";
  address: Address | null | undefined;
  editing: boolean;
  editValues: Record<string, unknown>;
  onEditChange: (key: string, val: unknown) => void;
}) {
  if (!editing) {
    const display = address
      ? `${address.line1 || ""}, ${address.city || ""}, ${address.state || ""}`
      : null;
    return <FieldRow label="Address" value={display} />;
  }

  const addrVal = (editValues[prefix] as Address) || {};
  const updateField = (field: keyof Address, val: string) => {
    onEditChange(prefix, { ...addrVal, [field]: val });
  };

  return (
    <div className="py-2.5 border-b border-gray-100 last:border-0">
      <span className="block w-44 text-sm text-gray-500 mb-2">Address</span>
      <div className="grid grid-cols-1 gap-2 pl-0">
        <input
          type="text"
          placeholder="Street address"
          className={inputClassName}
          value={addrVal.line1 || ""}
          onChange={(e) => updateField("line1", e.target.value)}
        />
        <div className="grid grid-cols-2 gap-2">
          <input
            type="text"
            placeholder="City"
            className={inputClassName}
            value={addrVal.city || ""}
            onChange={(e) => updateField("city", e.target.value)}
          />
          <input
            type="text"
            placeholder="State"
            className={inputClassName}
            value={addrVal.state || ""}
            onChange={(e) => updateField("state", e.target.value)}
          />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <input
            type="text"
            placeholder="Postal code"
            className={inputClassName}
            value={addrVal.postal_code || ""}
            onChange={(e) => updateField("postal_code", e.target.value)}
          />
          <input
            type="text"
            placeholder="Country"
            className={inputClassName}
            value={addrVal.country || ""}
            onChange={(e) => updateField("country", e.target.value)}
          />
        </div>
      </div>
    </div>
  );
}

interface TimelineEvent {
  timestamp: string;
  event: string;
  details?: string;
}

function Timeline({ events }: { events: TimelineEvent[] }) {
  if (!events || events.length === 0) return null;
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mt-6">
      <h2 className="text-base font-semibold text-gray-800 mb-4">Order History</h2>
      <div className="space-y-4">
        {events.map((event, i) => (
          <div key={i} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div className="w-2.5 h-2.5 rounded-full bg-blue-500 mt-1.5" />
              {i < events.length - 1 && <div className="w-px flex-1 bg-gray-200 mt-1" />}
            </div>
            <div className="pb-4">
              <p className="text-sm font-medium text-gray-800">{event.event}</p>
              {event.details && <p className="text-xs text-gray-500 mt-0.5">{event.details}</p>}
              <p className="text-xs text-gray-400 mt-1">
                {new Date(event.timestamp).toLocaleString()}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Select option constants ---

const FREIGHT_TYPE_OPTIONS = [
  { value: "FTL", label: "FTL" },
  { value: "LTL", label: "LTL" },
  { value: "Partial", label: "Partial" },
  { value: "Intermodal", label: "Intermodal" },
];

const EQUIPMENT_TYPE_OPTIONS = [
  { value: "Dry Van", label: "Dry Van" },
  { value: "Reefer", label: "Reefer" },
  { value: "Flatbed", label: "Flatbed" },
  { value: "Step Deck", label: "Step Deck" },
  { value: "Tanker", label: "Tanker" },
  { value: "Conestoga", label: "Conestoga" },
  { value: "Power Only", label: "Power Only" },
];

const WEIGHT_UNIT_OPTIONS = [
  { value: "lbs", label: "lbs" },
  { value: "kg", label: "kg" },
  { value: "tons", label: "tons" },
];

// --- Main Page Component ---

export function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const { data: order, isLoading } = useQuery({
    queryKey: ["order", id],
    queryFn: () => getOrder(id!),
    enabled: !!id,
  });

  const [editing, setEditing] = useState(false);
  const [editValues, setEditValues] = useState<Record<string, unknown>>({});

  const mutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => updateOrder(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["order", id] });
      setEditing(false);
      setEditValues({});
    },
  });

  const startEditing = useCallback(() => {
    if (!order) return;
    setEditValues({
      customer_name: order.customer_name || "",
      contact_name: order.contact_name || "",
      contact_email: order.contact_email || "",
      contact_phone: order.contact_phone || "",
      commodity: order.commodity || "",
      freight_type: order.freight_type || "",
      equipment_type: order.equipment_type || "",
      total_weight: order.total_weight != null ? String(order.total_weight) : "",
      weight_unit: order.weight_unit || "",
      num_pallets: order.num_pallets != null ? String(order.num_pallets) : "",
      pickup_date: order.pickup_date || "",
      delivery_date: order.delivery_date || "",
      pickup_instructions: order.pickup_instructions || "",
      delivery_instructions: order.delivery_instructions || "",
      notes: order.notes || "",
      hazmat_indicator: !!order.hazmat_indicator,
      pickup_address: order.pickup_address || { line1: "", city: "", state: "", postal_code: "", country: "" },
      delivery_address: order.delivery_address || { line1: "", city: "", state: "", postal_code: "", country: "" },
    });
    setEditing(true);
  }, [order]);

  const cancelEditing = useCallback(() => {
    setEditing(false);
    setEditValues({});
  }, []);

  const handleFieldChange = useCallback((key: string, val: unknown) => {
    setEditValues((prev) => ({ ...prev, [key]: val }));
  }, []);

  const handleSave = useCallback(() => {
    if (!order) return;

    const changedFields: Record<string, unknown> = {};

    // Compare simple fields
    const simpleKeys = [
      "customer_name",
      "contact_name",
      "contact_email",
      "contact_phone",
      "commodity",
      "freight_type",
      "equipment_type",
      "weight_unit",
      "pickup_date",
      "delivery_date",
      "pickup_instructions",
      "delivery_instructions",
      "notes",
    ] as const;

    for (const key of simpleKeys) {
      const edited = (editValues[key] as string) || "";
      const original = (order[key] as string) || "";
      if (edited !== original) {
        changedFields[key] = edited || null;
      }
    }

    // Numeric fields
    const numTotal = editValues.total_weight ? Number(editValues.total_weight) : null;
    const origTotal = order.total_weight ?? null;
    if (numTotal !== origTotal) {
      changedFields.total_weight = numTotal;
    }

    const numPallets = editValues.num_pallets ? Number(editValues.num_pallets) : null;
    const origPallets = order.num_pallets ?? null;
    if (numPallets !== origPallets) {
      changedFields.num_pallets = numPallets;
    }

    // Boolean
    if (!!editValues.hazmat_indicator !== !!order.hazmat_indicator) {
      changedFields.hazmat_indicator = !!editValues.hazmat_indicator;
    }

    // Address fields
    const addrKeys = ["pickup_address", "delivery_address"] as const;
    for (const addrKey of addrKeys) {
      const edited = editValues[addrKey] as Address | undefined;
      const original = (order[addrKey] as Address) || {};
      if (edited && JSON.stringify(edited) !== JSON.stringify(original)) {
        changedFields[addrKey] = edited;
      }
    }

    if (Object.keys(changedFields).length > 0) {
      mutation.mutate(changedFields);
    } else {
      // Nothing changed, just exit edit mode
      setEditing(false);
      setEditValues({});
    }
  }, [order, editValues, mutation]);

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-48" />
        <div className="grid grid-cols-2 gap-6">
          <div className="h-64 bg-gray-200 rounded-xl" />
          <div className="h-64 bg-gray-200 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-100">
        Order not found
      </div>
    );
  }

  const scores = (order.field_confidence_scores || {}) as Record<string, number>;
  const timeline = (order.history || order.timeline || []) as TimelineEvent[];

  return (
    <div>
      {/* Back Button */}
      <Link
        to="/orders"
        className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Orders
      </Link>

      {/* Header */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{order.order_number}</h1>
        <StatusBadge status={order.status} />
        <CircularConfidence score={order.overall_confidence_score} />

        {!editing && (
          <button
            onClick={startEditing}
            className="ml-auto inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm"
          >
            <Pencil className="w-3.5 h-3.5" />
            Edit
          </button>
        )}

        {editing && (
          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={cancelEditing}
              disabled={mutation.isPending}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-lg hover:bg-gray-200 transition-colors disabled:opacity-50"
            >
              <X className="w-3.5 h-3.5" />
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={mutation.isPending}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 transition-all shadow-sm disabled:opacity-50"
            >
              <Save className="w-3.5 h-3.5" />
              {mutation.isPending ? "Saving…" : "Save"}
            </button>
          </div>
        )}
      </div>

      {/* Mutation error */}
      {mutation.isError && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-lg border border-red-100">
          Failed to save changes: {(mutation.error as Error).message}
        </div>
      )}

      {/* Field sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Customer Info */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-6 py-3 bg-blue-50 border-b border-blue-100">
            <h2 className="text-sm font-semibold text-blue-800">Customer Information</h2>
          </div>
          <div className="p-6">
            <FieldRow
              label="Customer Name"
              value={order.customer_name}
              confidence={scores.customer_name}
              editing={editing}
              fieldKey="customer_name"
              editValue={editValues.customer_name}
              onEditChange={handleFieldChange}
            />
            <FieldRow
              label="Contact Name"
              value={order.contact_name}
              confidence={scores.contact_name}
              editing={editing}
              fieldKey="contact_name"
              editValue={editValues.contact_name}
              onEditChange={handleFieldChange}
            />
            <FieldRow
              label="Contact Email"
              value={order.contact_email}
              confidence={scores.contact_email}
              editing={editing}
              fieldKey="contact_email"
              editValue={editValues.contact_email}
              onEditChange={handleFieldChange}
            />
            <FieldRow
              label="Contact Phone"
              value={order.contact_phone}
              confidence={scores.contact_phone}
              editing={editing}
              fieldKey="contact_phone"
              editValue={editValues.contact_phone}
              onEditChange={handleFieldChange}
            />
          </div>
        </div>

        {/* Shipment Info */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-6 py-3 bg-purple-50 border-b border-purple-100">
            <h2 className="text-sm font-semibold text-purple-800">Shipment Details</h2>
          </div>
          <div className="p-6">
            <FieldRow
              label="Commodity"
              value={order.commodity}
              confidence={scores.commodity}
              editing={editing}
              fieldKey="commodity"
              editValue={editValues.commodity}
              onEditChange={handleFieldChange}
            />
            <FieldRow
              label="Freight Type"
              value={order.freight_type}
              confidence={scores.freight_type}
              editing={editing}
              fieldKey="freight_type"
              inputType="select"
              options={FREIGHT_TYPE_OPTIONS}
              editValue={editValues.freight_type}
              onEditChange={handleFieldChange}
            />
            <FieldRow
              label="Equipment"
              value={order.equipment_type}
              confidence={scores.equipment_type}
              editing={editing}
              fieldKey="equipment_type"
              inputType="select"
              options={EQUIPMENT_TYPE_OPTIONS}
              editValue={editValues.equipment_type}
              onEditChange={handleFieldChange}
            />
            <FieldRow
              label="Weight"
              value={order.total_weight ? `${order.total_weight} ${order.weight_unit || ""}` : null}
              confidence={scores.total_weight}
              editing={editing}
              fieldKey="total_weight"
              editValue={editValues.total_weight}
              onEditChange={handleFieldChange}
            />
            {editing && (
              <FieldRow
                label="Weight Unit"
                value={order.weight_unit}
                editing={editing}
                fieldKey="weight_unit"
                inputType="select"
                options={WEIGHT_UNIT_OPTIONS}
                editValue={editValues.weight_unit}
                onEditChange={handleFieldChange}
              />
            )}
            <FieldRow
              label="Pallets"
              value={order.num_pallets}
              editing={editing}
              fieldKey="num_pallets"
              editValue={editValues.num_pallets}
              onEditChange={handleFieldChange}
            />
            <FieldRow
              label="Hazmat"
              value={order.hazmat_indicator ? "Yes" : "No"}
              editing={editing}
              fieldKey="hazmat_indicator"
              inputType="checkbox"
              editValue={editValues.hazmat_indicator}
              onEditChange={handleFieldChange}
            />
          </div>
        </div>

        {/* Pickup */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-6 py-3 bg-green-50 border-b border-green-100">
            <h2 className="text-sm font-semibold text-green-800">Pickup</h2>
          </div>
          <div className="p-6">
            <FieldRow
              label="Location"
              value={order.pickup_location_name}
              confidence={scores.pickup_location_name}
            />
            <FieldRow
              label="Date"
              value={order.pickup_date}
              confidence={scores.pickup_date}
              editing={editing}
              fieldKey="pickup_date"
              inputType="date"
              editValue={editValues.pickup_date}
              onEditChange={handleFieldChange}
            />
            <AddressFields
              prefix="pickup_address"
              address={order.pickup_address}
              editing={editing}
              editValues={editValues}
              onEditChange={handleFieldChange}
            />
            <FieldRow
              label="Instructions"
              value={order.pickup_instructions}
              editing={editing}
              fieldKey="pickup_instructions"
              inputType="textarea"
              editValue={editValues.pickup_instructions}
              onEditChange={handleFieldChange}
            />
          </div>
        </div>

        {/* Delivery */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-6 py-3 bg-orange-50 border-b border-orange-100">
            <h2 className="text-sm font-semibold text-orange-800">Delivery</h2>
          </div>
          <div className="p-6">
            <FieldRow
              label="Location"
              value={order.delivery_location_name}
              confidence={scores.delivery_location_name}
            />
            <FieldRow
              label="Date"
              value={order.delivery_date}
              confidence={scores.delivery_date}
              editing={editing}
              fieldKey="delivery_date"
              inputType="date"
              editValue={editValues.delivery_date}
              onEditChange={handleFieldChange}
            />
            <AddressFields
              prefix="delivery_address"
              address={order.delivery_address}
              editing={editing}
              editValues={editValues}
              onEditChange={handleFieldChange}
            />
            <FieldRow
              label="Instructions"
              value={order.delivery_instructions}
              editing={editing}
              fieldKey="delivery_instructions"
              inputType="textarea"
              editValue={editValues.delivery_instructions}
              onEditChange={handleFieldChange}
            />
          </div>
        </div>

        {/* Notes (full width) */}
        {(editing || order.notes) && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden lg:col-span-2">
            <div className="px-6 py-3 bg-gray-50 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-800">Notes</h2>
            </div>
            <div className="p-6">
              <FieldRow
                label="Notes"
                value={order.notes}
                editing={editing}
                fieldKey="notes"
                inputType="textarea"
                editValue={editValues.notes}
                onEditChange={handleFieldChange}
              />
            </div>
          </div>
        )}
      </div>

      {/* Timeline */}
      <Timeline events={timeline} />
    </div>
  );
}
