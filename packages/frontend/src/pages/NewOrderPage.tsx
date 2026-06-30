import { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { createOrder, getActiveFieldConfigs } from "../lib/api";
import {
  User,
  MapPin,
  Package,
  ClipboardCheck,
  ChevronRight,
  ChevronLeft,
  Check,
  AlertCircle,
} from "lucide-react";

import type { LucideIcon } from "lucide-react";

// --- Types ---

interface FieldConfig {
  id: string;
  field_name: string;
  label: string;
  is_mandatory: boolean;
  is_conditional: boolean;
  conditional_depends_on: string | null;
  conditional_value: string | null;
  display_order: number;
  active: boolean;
}

interface StepConfig {
  id: number;
  label: string;
  icon: LucideIcon;
}

const STEPS: StepConfig[] = [
  { id: 1, label: "Customer Info", icon: User },
  { id: 2, label: "Pickup", icon: MapPin },
  { id: 3, label: "Delivery", icon: MapPin },
  { id: 4, label: "Shipment", icon: Package },
  { id: 5, label: "Review", icon: ClipboardCheck },
];

// --- Section grouping logic ---

function getSectionIndex(fieldName: string): number {
  if (fieldName.startsWith("customer_") || fieldName.startsWith("contact_")) return 0;
  if (fieldName.startsWith("pickup_")) return 1;
  if (fieldName.startsWith("delivery_")) return 2;
  return 3;
}

// --- Input type inference ---

type FieldInputType = "text" | "date" | "email" | "tel" | "select" | "checkbox" | "textarea";

interface SelectOption {
  value: string;
  label: string;
}

const FREIGHT_TYPE_OPTIONS: SelectOption[] = [
  { value: "FTL", label: "Full Truckload (FTL)" },
  { value: "LTL", label: "Less Than Truckload (LTL)" },
  { value: "Partial", label: "Partial" },
  { value: "Intermodal", label: "Intermodal" },
];

const EQUIPMENT_TYPE_OPTIONS: SelectOption[] = [
  { value: "dry_van", label: "Dry Van" },
  { value: "flatbed", label: "Flatbed" },
  { value: "reefer", label: "Reefer" },
  { value: "step_deck", label: "Step Deck" },
  { value: "tanker", label: "Tanker" },
  { value: "lowboy", label: "Lowboy" },
  { value: "conestoga", label: "Conestoga" },
  { value: "other", label: "Other" },
];

const WEIGHT_UNIT_OPTIONS: SelectOption[] = [
  { value: "lbs", label: "Pounds (lbs)" },
  { value: "kgs", label: "Kilograms (kgs)" },
];

const CHECKBOX_FIELDS = new Set([
  "hazmat_indicator",
  "stackable",
  "liftgate_required",
  "team_drive_required",
  "twic_card_required",
]);

const TEXTAREA_FIELDS = new Set([
  "pickup_instructions",
  "delivery_instructions",
  "special_handling_instructions",
  "notes",
  "internal_comments",
]);

function getFieldInputType(fieldName: string): FieldInputType {
  if (CHECKBOX_FIELDS.has(fieldName)) return "checkbox";
  if (TEXTAREA_FIELDS.has(fieldName)) return "textarea";
  if (fieldName === "freight_type" || fieldName === "equipment_type" || fieldName === "weight_unit")
    return "select";
  if (fieldName.endsWith("_date")) return "date";
  if (fieldName.endsWith("_email")) return "email";
  if (fieldName.endsWith("_phone")) return "tel";
  if (fieldName.endsWith("_instructions")) return "textarea";
  return "text";
}

function getSelectOptions(fieldName: string): SelectOption[] {
  switch (fieldName) {
    case "freight_type":
      return FREIGHT_TYPE_OPTIONS;
    case "equipment_type":
      return EQUIPMENT_TYPE_OPTIONS;
    case "weight_unit":
      return WEIGHT_UNIT_OPTIONS;
    default:
      return [];
  }
}

// --- Skeleton Component ---

function FieldSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-6 w-48 bg-gray-200 rounded" />
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="space-y-2">
            <div className="h-4 w-24 bg-gray-200 rounded" />
            <div className="h-10 bg-gray-100 rounded-lg" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="space-y-2">
            <div className="h-4 w-32 bg-gray-200 rounded" />
            <div className="h-10 bg-gray-100 rounded-lg" />
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Dynamic Field Renderer ---

function DynamicField({
  config,
  value,
  onChange,
  error,
}: {
  config: FieldConfig;
  value: string | boolean;
  onChange: (val: string | boolean) => void;
  error?: string;
}) {
  const inputType = getFieldInputType(config.field_name);

  if (inputType === "checkbox") {
    return (
      <div className="flex items-center gap-3">
        <input
          type="checkbox"
          id={config.field_name}
          checked={value === true}
          onChange={(e) => onChange(e.target.checked)}
          className="w-4 h-4 rounded border-gray-300 text-amber-500 focus:ring-amber-500"
        />
        <label htmlFor={config.field_name} className="text-sm font-medium text-gray-700 cursor-pointer">
          {config.label}
          {config.is_mandatory && <span className="text-red-500 ml-0.5">*</span>}
        </label>
      </div>
    );
  }

  if (inputType === "textarea") {
    return (
      <div>
        <label htmlFor={config.field_name} className="block text-sm font-medium text-gray-700 mb-1">
          {config.label}
          {config.is_mandatory && <span className="text-red-500 ml-0.5">*</span>}
        </label>
        <textarea
          id={config.field_name}
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value)}
          rows={3}
          className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500 transition-all resize-none ${
            error ? "border-red-300 bg-red-50" : "border-gray-200"
          }`}
        />
        {error && (
          <p className="mt-1 text-xs text-red-600 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            {error}
          </p>
        )}
      </div>
    );
  }

  if (inputType === "select") {
    const options = getSelectOptions(config.field_name);
    return (
      <div>
        <label htmlFor={config.field_name} className="block text-sm font-medium text-gray-700 mb-1">
          {config.label}
          {config.is_mandatory && <span className="text-red-500 ml-0.5">*</span>}
        </label>
        <select
          id={config.field_name}
          value={typeof value === "string" ? value : ""}
          onChange={(e) => onChange(e.target.value)}
          className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500 transition-all bg-white ${
            error ? "border-red-300 bg-red-50" : "border-gray-200"
          }`}
        >
          <option value="">Select...</option>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {error && (
          <p className="mt-1 text-xs text-red-600 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            {error}
          </p>
        )}
      </div>
    );
  }

  // text, date, email, tel
  return (
    <div>
      <label htmlFor={config.field_name} className="block text-sm font-medium text-gray-700 mb-1">
        {config.label}
        {config.is_mandatory && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      <input
        id={config.field_name}
        type={inputType}
        value={typeof value === "string" ? value : ""}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full px-3 py-2.5 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500 transition-all ${
          error ? "border-red-300 bg-red-50" : "border-gray-200"
        }`}
      />
      {error && (
        <p className="mt-1 text-xs text-red-600 flex items-center gap-1">
          <AlertCircle className="w-3 h-3" />
          {error}
        </p>
      )}
    </div>
  );
}

// --- Review Section ---

function ReviewSection({
  title,
  fields,
}: {
  title: string;
  fields: { label: string; value: string }[];
}) {
  const filledFields = fields.filter((f) => f.value && f.value !== "false");
  if (filledFields.length === 0) return null;

  return (
    <div className="mb-5">
      <h4 className="text-sm font-semibold text-gray-900 mb-2 pb-1 border-b border-gray-100">
        {title}
      </h4>
      <div className="grid grid-cols-2 gap-x-6 gap-y-1.5">
        {filledFields.map((f) => (
          <div key={f.label} className="flex gap-2">
            <span className="text-[12px] text-gray-400 min-w-[120px]">{f.label}:</span>
            <span className="text-[13px] text-gray-700 font-medium">{f.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Main Component ---

export function NewOrderPage() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [formValues, setFormValues] = useState<Record<string, string | boolean>>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Fetch field configs
  const {
    data: configResponse,
    isLoading,
    isError: configError,
  } = useQuery({
    queryKey: ["active-field-configs"],
    queryFn: getActiveFieldConfigs,
  });

  const fieldConfigs: FieldConfig[] = useMemo(() => {
    if (!configResponse?.data) return [];
    return (configResponse.data as FieldConfig[])
      .filter((f) => f.active)
      .sort((a, b) => a.display_order - b.display_order);
  }, [configResponse]);

  // Group fields into sections (4 groups: 0=Customer, 1=Pickup, 2=Delivery, 3=Shipment)
  const sectionFields = useMemo(() => {
    const sections: FieldConfig[][] = [[], [], [], []];
    for (const field of fieldConfigs) {
      const idx = getSectionIndex(field.field_name);
      sections[idx].push(field);
    }
    return sections;
  }, [fieldConfigs]);

  // Determine which conditional fields are visible
  const isFieldVisible = (config: FieldConfig): boolean => {
    if (!config.is_conditional) return true;
    if (!config.conditional_depends_on) return true;
    const dependsValue = formValues[config.conditional_depends_on];
    if (typeof dependsValue === "string") {
      return dependsValue.toLowerCase() === (config.conditional_value ?? "").toLowerCase();
    }
    if (typeof dependsValue === "boolean") {
      return String(dependsValue) === config.conditional_value;
    }
    return false;
  };

  // Get visible fields for a section
  const getVisibleFieldsForSection = (sectionIndex: number): FieldConfig[] => {
    return sectionFields[sectionIndex]?.filter(isFieldVisible) ?? [];
  };

  // Mutation
  const mutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => createOrder(payload),
    onSuccess: (data: Record<string, unknown>) => {
      const orderNumber = (data as Record<string, unknown>)?.order_number || "New Order";
      setSuccessMessage(`Order created: ${orderNumber}`);
      setTimeout(() => navigate("/orders"), 2000);
    },
  });

  // Update form values
  const updateField = (fieldName: string, value: string | boolean) => {
    setFormValues((prev) => ({ ...prev, [fieldName]: value }));
    // Clear error when user types
    if (errors[fieldName]) {
      setErrors((prev) => {
        const next = { ...prev };
        delete next[fieldName];
        return next;
      });
    }
  };

  // Validate current step
  const validateStep = (): boolean => {
    if (currentStep === 5) return true;
    const sectionIndex = currentStep - 1;
    const visibleFields = getVisibleFieldsForSection(sectionIndex);
    const newErrors: Record<string, string> = {};

    for (const field of visibleFields) {
      if (field.is_mandatory) {
        const val = formValues[field.field_name];
        if (val === undefined || val === "" || val === false) {
          newErrors[field.field_name] = `${field.label} is required`;
        }
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Next step handler
  const handleNext = () => {
    if (validateStep()) {
      setCurrentStep((s) => Math.min(5, s + 1));
    }
  };

  // Build submit payload
  const handleSubmit = () => {
    const payload: Record<string, unknown> = {};

    // Collect all field values
    for (const config of fieldConfigs) {
      if (!isFieldVisible(config)) continue;
      const val = formValues[config.field_name];
      if (val === undefined || val === "") continue;
      payload[config.field_name] = val;
    }

    // Group pickup address fields into pickup_address JSONB
    const pickupAddress: Record<string, string> = {};
    if (payload["pickup_address_line1"]) {
      pickupAddress.line1 = payload["pickup_address_line1"] as string;
      delete payload["pickup_address_line1"];
    }
    if (payload["pickup_city"]) {
      pickupAddress.city = payload["pickup_city"] as string;
      delete payload["pickup_city"];
    }
    if (payload["pickup_state"]) {
      pickupAddress.state = payload["pickup_state"] as string;
      delete payload["pickup_state"];
    }
    if (payload["pickup_postal_code"]) {
      pickupAddress.postal_code = payload["pickup_postal_code"] as string;
      delete payload["pickup_postal_code"];
    }
    if (payload["pickup_country"]) {
      pickupAddress.country = payload["pickup_country"] as string;
      delete payload["pickup_country"];
    }
    if (Object.keys(pickupAddress).length > 0) {
      payload["pickup_address"] = pickupAddress;
    }

    // Group delivery address fields into delivery_address JSONB
    const deliveryAddress: Record<string, string> = {};
    if (payload["delivery_address_line1"]) {
      deliveryAddress.line1 = payload["delivery_address_line1"] as string;
      delete payload["delivery_address_line1"];
    }
    if (payload["delivery_city"]) {
      deliveryAddress.city = payload["delivery_city"] as string;
      delete payload["delivery_city"];
    }
    if (payload["delivery_state"]) {
      deliveryAddress.state = payload["delivery_state"] as string;
      delete payload["delivery_state"];
    }
    if (payload["delivery_postal_code"]) {
      deliveryAddress.postal_code = payload["delivery_postal_code"] as string;
      delete payload["delivery_postal_code"];
    }
    if (payload["delivery_country"]) {
      deliveryAddress.country = payload["delivery_country"] as string;
      delete payload["delivery_country"];
    }
    if (Object.keys(deliveryAddress).length > 0) {
      payload["delivery_address"] = deliveryAddress;
    }

    mutation.mutate(payload);
  };

  // Render section fields
  const renderSectionFields = (sectionIndex: number) => {
    const visibleFields = getVisibleFieldsForSection(sectionIndex);
    const sectionTitles = ["Customer Information", "Pickup Details", "Delivery Details", "Shipment Details"];

    // Separate checkboxes from other fields for layout
    const checkboxFields = visibleFields.filter((f) => CHECKBOX_FIELDS.has(f.field_name));
    const otherFields = visibleFields.filter((f) => !CHECKBOX_FIELDS.has(f.field_name));

    return (
      <div className="space-y-4 animate-fade-in">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{sectionTitles[sectionIndex]}</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {otherFields.map((config) => (
            <div
              key={config.field_name}
              className={
                getFieldInputType(config.field_name) === "textarea" ? "sm:col-span-2" : ""
              }
            >
              <DynamicField
                config={config}
                value={formValues[config.field_name] ?? (CHECKBOX_FIELDS.has(config.field_name) ? false : "")}
                onChange={(val) => updateField(config.field_name, val)}
                error={errors[config.field_name]}
              />
            </div>
          ))}
        </div>
        {checkboxFields.length > 0 && (
          <div className="border border-gray-200 rounded-lg p-4 space-y-3">
            {checkboxFields.map((config) => (
              <DynamicField
                key={config.field_name}
                config={config}
                value={formValues[config.field_name] ?? false}
                onChange={(val) => updateField(config.field_name, val)}
                error={errors[config.field_name]}
              />
            ))}
          </div>
        )}
      </div>
    );
  };

  // Render review step
  const renderReview = () => {
    const sectionTitles = ["Customer Info", "Pickup", "Delivery", "Shipment"];

    return (
      <div className="animate-fade-in">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Review Order</h3>
        <div className="bg-slate-50 rounded-lg p-5 border border-gray-100">
          {sectionFields.map((fields, sectionIdx) => {
            const reviewFields = fields
              .filter(isFieldVisible)
              .map((config) => {
                const raw = formValues[config.field_name];
                let display = "";
                if (typeof raw === "boolean") {
                  display = raw ? "Yes" : "";
                } else if (typeof raw === "string") {
                  // For selects, show the label
                  if (getFieldInputType(config.field_name) === "select") {
                    const opts = getSelectOptions(config.field_name);
                    const match = opts.find((o) => o.value === raw);
                    display = match ? match.label : raw;
                  } else {
                    display = raw;
                  }
                }
                return { label: config.label, value: display };
              });

            return (
              <ReviewSection
                key={sectionTitles[sectionIdx]}
                title={sectionTitles[sectionIdx]}
                fields={reviewFields}
              />
            );
          })}
        </div>
      </div>
    );
  };

  const renderStep = () => {
    if (currentStep === 5) return renderReview();
    return renderSectionFields(currentStep - 1);
  };

  return (
    <div className="animate-fade-in max-w-4xl">
      {/* Success Banner */}
      {successMessage && (
        <div className="mb-5 bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex items-center gap-3">
          <Check className="w-5 h-5 text-emerald-600" />
          <p className="text-sm font-medium text-emerald-700">{successMessage}</p>
        </div>
      )}

      {/* Error Banner */}
      {mutation.isError && (
        <div className="mb-5 bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <p className="text-sm font-medium text-red-700">
            Failed to create order: {(mutation.error as Error).message}
          </p>
        </div>
      )}

      {/* Config fetch error */}
      {configError && (
        <div className="mb-5 bg-red-50 border border-red-200 rounded-lg p-4 flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <p className="text-sm font-medium text-red-700">
            Failed to load form configuration. Please refresh and try again.
          </p>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Create New Order</h1>
        <span className="text-sm text-gray-500">
          Step {currentStep} of {STEPS.length}
        </span>
      </div>

      {/* Horizontal Stepper */}
      <div className="flex items-center justify-between mb-8 px-4">
        {STEPS.map((step, index) => {
          const isActive = step.id === currentStep;
          const isComplete = step.id < currentStep;
          const Icon = step.icon;
          return (
            <div key={step.id} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center transition-all ${
                    isComplete
                      ? "bg-emerald-500 text-white"
                      : isActive
                        ? "bg-amber-500 text-white"
                        : "bg-gray-200 text-gray-500"
                  }`}
                >
                  {isComplete ? <Check className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                </div>
                <span
                  className={`text-[11px] mt-2 font-medium whitespace-nowrap ${
                    isActive
                      ? "text-amber-700"
                      : isComplete
                        ? "text-emerald-700"
                        : "text-gray-400"
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {index < STEPS.length - 1 && (
                <div
                  className={`h-0.5 flex-1 mx-3 -mt-5 ${
                    step.id < currentStep ? "bg-emerald-400" : "bg-gray-200"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Form Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 flex flex-col">
        <div className="flex-1">
          {isLoading ? <FieldSkeleton /> : renderStep()}
        </div>

        {/* Navigation Buttons */}
        {!isLoading && (
          <div className="flex items-center justify-between mt-8 pt-5 border-t border-gray-100">
            <button
              onClick={() => {
                setErrors({});
                setCurrentStep((s) => Math.max(1, s - 1));
              }}
              disabled={currentStep === 1}
              className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              <ChevronLeft className="w-4 h-4" />
              Back
            </button>

            {currentStep < 5 ? (
              <button
                onClick={handleNext}
                className="flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 shadow-sm transition-all"
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={mutation.isPending}
                className="flex items-center gap-2 px-6 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition-all"
              >
                {mutation.isPending ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4" />
                    Submit Order
                  </>
                )}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
