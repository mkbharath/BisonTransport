import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Settings,
  Plus,
  Pencil,
  Trash2,
  X,
  Save,
} from "lucide-react";
import {
  getFieldConfigs,
  createFieldConfig,
  updateFieldConfig,
  deleteFieldConfig,
  getBusinessRules,
  createBusinessRule,
  updateBusinessRule,
  deleteBusinessRule,
  getEmailTemplates,
  createEmailTemplate,
  updateEmailTemplate,
  deleteEmailTemplate,
  getUsers,
  createUser,
  updateUser,
  deleteUser,
} from "../lib/api";

type TabKey = "fields" | "rules" | "templates" | "thresholds" | "users";

const TABS: { key: TabKey; label: string }[] = [
  { key: "fields", label: "Field Configuration" },
  { key: "rules", label: "Business Rules" },
  { key: "templates", label: "Email Templates" },
  { key: "thresholds", label: "Thresholds" },
  { key: "users", label: "Users" },
];

export function AdminPage() {
  const [activeTab, setActiveTab] = useState<TabKey>("fields");

  return (
    <div className="animate-slide-up">
      <div className="flex items-center gap-3 mb-6">
        <Settings className="w-6 h-6 text-amber-500" />
        <h1 className="text-2xl font-bold text-gray-900">Administration</h1>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1.5 mb-6 overflow-x-auto pb-1">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-[13px] font-medium rounded-lg whitespace-nowrap transition-all ${
              activeTab === tab.key
                ? "bg-[#0f1b2d] text-white shadow-sm"
                : "bg-white text-gray-500 border border-gray-200 hover:border-gray-300 hover:text-gray-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "fields" && <FieldConfigTab />}
      {activeTab === "rules" && <BusinessRulesTab />}
      {activeTab === "templates" && <EmailTemplatesTab />}
      {activeTab === "thresholds" && <ThresholdsTab />}
      {activeTab === "users" && <UsersTab />}
    </div>
  );
}


// ─── Field Configuration Tab ────────────────────────────────────────────────

interface FieldConfig {
  id: string;
  field_name: string;
  label: string;
  is_mandatory: boolean;
  is_conditional: boolean;
  conditional_depends_on: string | null;
  conditional_value: string | null;
  display_order: number;
}

const EMPTY_FIELD: Omit<FieldConfig, "id"> = {
  field_name: "",
  label: "",
  is_mandatory: false,
  is_conditional: false,
  conditional_depends_on: null,
  conditional_value: null,
  display_order: 0,
};

function FieldConfigTab() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<FieldConfig | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<Omit<FieldConfig, "id">>(EMPTY_FIELD);

  const { data, isLoading } = useQuery({
    queryKey: ["admin", "field-configs"],
    queryFn: getFieldConfigs,
  });

  const createMut = useMutation({
    mutationFn: (d: Record<string, unknown>) => createFieldConfig(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["admin", "field-configs"] }); resetForm(); },
  });
  const updateMut = useMutation({
    mutationFn: ({ id, d }: { id: string; d: Record<string, unknown> }) => updateFieldConfig(id, d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["admin", "field-configs"] }); resetForm(); },
  });
  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteFieldConfig(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "field-configs"] }),
  });

  function resetForm() {
    setEditing(null);
    setCreating(false);
    setForm(EMPTY_FIELD);
  }

  function startEdit(item: FieldConfig) {
    setCreating(false);
    setEditing(item);
    setForm({ field_name: item.field_name, label: item.label, is_mandatory: item.is_mandatory, is_conditional: item.is_conditional, conditional_depends_on: item.conditional_depends_on, conditional_value: item.conditional_value, display_order: item.display_order });
  }

  function handleSave() {
    if (editing) {
      updateMut.mutate({ id: editing.id, d: form as unknown as Record<string, unknown> });
    } else {
      createMut.mutate(form as unknown as Record<string, unknown>);
    }
  }

  const fields = (data?.data ?? []) as FieldConfig[];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">Field Configuration</h2>
        <button
          onClick={() => { setEditing(null); setCreating(true); setForm(EMPTY_FIELD); }}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          Add Field
        </button>
      </div>

      {/* Inline Form */}
      {(creating || editing) && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 mb-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-gray-700">{editing ? "Edit Field" : "Add Field"}</h3>
            <button onClick={resetForm} className="p-1 text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Field Name</label>
              <input value={form.field_name} onChange={(e) => setForm({ ...form, field_name: e.target.value })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Label</label>
              <input value={form.label} onChange={(e) => setForm({ ...form, label: e.target.value })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Display Order</label>
              <input type="number" value={form.display_order} onChange={(e) => setForm({ ...form, display_order: parseInt(e.target.value) || 0 })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
            </div>
          </div>

          <div className="flex items-center gap-6 mt-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={form.is_mandatory} onChange={(e) => setForm({ ...form, is_mandatory: e.target.checked })} className="w-4 h-4 rounded border-gray-300 text-amber-500 focus:ring-amber-400" />
              <span className="text-sm text-gray-700">Mandatory</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={form.is_conditional} onChange={(e) => setForm({ ...form, is_conditional: e.target.checked })} className="w-4 h-4 rounded border-gray-300 text-amber-500 focus:ring-amber-400" />
              <span className="text-sm text-gray-700">Conditional</span>
            </label>
          </div>
          {form.is_conditional && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Depends On</label>
                <input value={form.conditional_depends_on || ""} onChange={(e) => setForm({ ...form, conditional_depends_on: e.target.value || null })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Conditional Value</label>
                <input value={form.conditional_value || ""} onChange={(e) => setForm({ ...form, conditional_value: e.target.value || null })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
              </div>
            </div>
          )}
          <div className="flex justify-end mt-5">
            <button onClick={handleSave} disabled={createMut.isPending || updateMut.isPending} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 shadow-sm transition-all disabled:opacity-50">
              <Save className="w-4 h-4" />
              {editing ? "Update" : "Create"}
            </button>
          </div>
        </div>
      )}

      {/* Table */}
      {isLoading ? (
        <div className="space-y-2 animate-pulse">
          {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-[48px] bg-gray-100 rounded-lg" />)}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200/80 overflow-hidden shadow-sm">
          <table className="w-full text-[13px] table-fixed">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider w-[20%]">Field Name</th>
                <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider w-[22%]">Label</th>
                <th className="px-5 py-3 text-center text-[12px] font-bold text-gray-700 uppercase tracking-wider w-[13%]">Mandatory</th>
                <th className="px-5 py-3 text-center text-[12px] font-bold text-gray-700 uppercase tracking-wider w-[13%]">Conditional</th>
                <th className="px-5 py-3 text-center text-[12px] font-bold text-gray-700 uppercase tracking-wider w-[10%]">Order</th>
                <th className="px-5 py-3 text-center text-[12px] font-bold text-gray-700 uppercase tracking-wider w-[12%]">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {fields.map((f) => (
                <tr key={f.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="px-5 py-3 font-medium text-gray-800 truncate">{f.field_name}</td>
                  <td className="px-5 py-3 text-gray-600 truncate">{f.label}</td>
                  <td className="px-5 py-3 text-center">
                    {f.is_mandatory ? (
                      <span className="inline-flex px-2 py-0.5 text-[11px] font-semibold rounded-md bg-amber-50 text-amber-700">Required</span>
                    ) : (
                      <span className="text-gray-400 text-xs">Optional</span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-center">
                    {f.is_conditional ? (
                      <span className="inline-flex px-2 py-0.5 text-[11px] font-semibold rounded-md bg-blue-50 text-blue-700">Yes</span>
                    ) : (
                      <span className="text-gray-400 text-xs">No</span>
                    )}
                  </td>
                  <td className="px-5 py-3 text-center text-gray-600">{f.display_order}</td>
                  <td className="px-5 py-3 text-center">
                    <button onClick={() => startEdit(f)} className="p-1.5 text-gray-400 hover:text-amber-600 rounded transition-colors"><Pencil className="w-3.5 h-3.5" /></button>
                    <button onClick={() => deleteMut.mutate(f.id)} className="p-1.5 text-gray-400 hover:text-red-600 rounded transition-colors ml-1"><Trash2 className="w-3.5 h-3.5" /></button>
                  </td>
                </tr>
              ))}
              {fields.length === 0 && (
                <tr><td colSpan={6} className="px-5 py-8 text-center text-gray-400 text-sm">No field configurations yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}


// ─── Business Rules Tab ─────────────────────────────────────────────────────

interface BusinessRule {
  id: string;
  rule_name: string;
  field_name: string;
  rule_type: string;
  rule_expression: string;
  error_message: string;
  severity: string;
  active: boolean;
  priority: number;
}

const EMPTY_RULE: Omit<BusinessRule, "id"> = {
  rule_name: "",
  field_name: "",
  rule_type: "required_if",
  rule_expression: "",
  error_message: "",
  severity: "error",
  active: true,
  priority: 0,
};

const RULE_TYPES = ["required_if", "valid_enum", "date_after", "date_before", "regex_match"];

function BusinessRulesTab() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<BusinessRule | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<Omit<BusinessRule, "id">>(EMPTY_RULE);

  const { data, isLoading } = useQuery({
    queryKey: ["admin", "business-rules"],
    queryFn: getBusinessRules,
  });

  const createMut = useMutation({
    mutationFn: (d: Record<string, unknown>) => createBusinessRule(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["admin", "business-rules"] }); resetForm(); },
  });
  const updateMut = useMutation({
    mutationFn: ({ id, d }: { id: string; d: Record<string, unknown> }) => updateBusinessRule(id, d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["admin", "business-rules"] }); resetForm(); },
  });
  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteBusinessRule(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "business-rules"] }),
  });

  function resetForm() { setEditing(null); setCreating(false); setForm(EMPTY_RULE); }

  function startEdit(item: BusinessRule) {
    setCreating(false);
    setEditing(item);
    setForm({ rule_name: item.rule_name, field_name: item.field_name, rule_type: item.rule_type, rule_expression: item.rule_expression, error_message: item.error_message, severity: item.severity, active: item.active, priority: item.priority });
  }

  function handleSave() {
    if (editing) {
      updateMut.mutate({ id: editing.id, d: form as unknown as Record<string, unknown> });
    } else {
      createMut.mutate(form as unknown as Record<string, unknown>);
    }
  }

  const rules = (data?.data ?? []) as BusinessRule[];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">Business Rules</h2>
        <button
          onClick={() => { setEditing(null); setCreating(true); setForm(EMPTY_RULE); }}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          Add Rule
        </button>
      </div>

      {/* Inline Form */}
      {(creating || editing) && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 mb-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-gray-700">{editing ? "Edit Rule" : "Add Rule"}</h3>
            <button onClick={resetForm} className="p-1 text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Rule Name</label>
              <input value={form.rule_name} onChange={(e) => setForm({ ...form, rule_name: e.target.value })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Field Name</label>
              <input value={form.field_name} onChange={(e) => setForm({ ...form, field_name: e.target.value })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Rule Type</label>
              <select value={form.rule_type} onChange={(e) => setForm({ ...form, rule_type: e.target.value })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none bg-white">
                {RULE_TYPES.map((t) => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Rule Expression</label>
              <input value={form.rule_expression} onChange={(e) => setForm({ ...form, rule_expression: e.target.value })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Severity</label>
              <select value={form.severity} onChange={(e) => setForm({ ...form, severity: e.target.value })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none bg-white">
                <option value="error">Error</option>
                <option value="warning">Warning</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Priority</label>
              <input type="number" value={form.priority} onChange={(e) => setForm({ ...form, priority: parseInt(e.target.value) || 0 })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
            </div>
          </div>
          <div className="mt-4">
            <label className="block text-xs font-medium text-gray-600 mb-1">Error Message</label>
            <input value={form.error_message} onChange={(e) => setForm({ ...form, error_message: e.target.value })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
          </div>
          <div className="flex justify-end mt-5">
            <button onClick={handleSave} disabled={createMut.isPending || updateMut.isPending} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 shadow-sm transition-all disabled:opacity-50">
              <Save className="w-4 h-4" />
              {editing ? "Update" : "Create"}
            </button>
          </div>
        </div>
      )}

      {/* Table */}
      {isLoading ? (
        <div className="space-y-2 animate-pulse">
          {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-[48px] bg-gray-100 rounded-lg" />)}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200/80 overflow-hidden shadow-sm">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Rule Name</th>
                <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Field</th>
                <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Type</th>
                <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Severity</th>
                <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Active</th>
                <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Priority</th>
                <th className="px-5 py-3 text-right text-[12px] font-bold text-gray-700 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {rules.map((r) => (
                <tr key={r.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="px-5 py-3 font-medium text-gray-800">{r.rule_name}</td>
                  <td className="px-5 py-3 text-gray-600">{r.field_name}</td>
                  <td className="px-5 py-3 text-gray-600 capitalize">{r.rule_type.replace(/_/g, " ")}</td>
                  <td className="px-5 py-3">
                    <span className={`inline-flex px-2 py-0.5 text-[11px] font-semibold rounded-md ${r.severity === "error" ? "bg-red-50 text-red-700" : "bg-amber-50 text-amber-700"}`}>
                      {r.severity}
                    </span>
                  </td>
                  <td className="px-5 py-3">
                    <span className={`inline-flex px-2 py-0.5 text-[11px] font-semibold rounded-md ${r.active ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-500"}`}>
                      {r.active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-gray-600">{r.priority}</td>
                  <td className="px-5 py-3 text-right">
                    <button onClick={() => startEdit(r)} className="p-1.5 text-gray-400 hover:text-amber-600 rounded transition-colors"><Pencil className="w-3.5 h-3.5" /></button>
                    <button onClick={() => deleteMut.mutate(r.id)} className="p-1.5 text-gray-400 hover:text-red-600 rounded transition-colors ml-1"><Trash2 className="w-3.5 h-3.5" /></button>
                  </td>
                </tr>
              ))}
              {rules.length === 0 && (
                <tr><td colSpan={7} className="px-5 py-8 text-center text-gray-400 text-sm">No business rules configured.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}


// ─── Email Templates Tab ────────────────────────────────────────────────────

interface EmailTemplate {
  id: string;
  name: string;
  template_type: string;
  subject_template: string;
  body_html_template: string;
  variables: string[];
  active: boolean;
}

const EMPTY_TEMPLATE: Omit<EmailTemplate, "id"> = {
  name: "",
  template_type: "missing_info",
  subject_template: "",
  body_html_template: "",
  variables: [],
  active: true,
};

const TEMPLATE_TYPES = ["missing_info", "follow_up", "acknowledgement", "duplicate_notification"];

function EmailTemplatesTab() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<EmailTemplate | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState<Omit<EmailTemplate, "id">>(EMPTY_TEMPLATE);
  const [variablesInput, setVariablesInput] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["admin", "email-templates"],
    queryFn: getEmailTemplates,
  });

  const createMut = useMutation({
    mutationFn: (d: Record<string, unknown>) => createEmailTemplate(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["admin", "email-templates"] }); resetForm(); },
  });
  const updateMut = useMutation({
    mutationFn: ({ id, d }: { id: string; d: Record<string, unknown> }) => updateEmailTemplate(id, d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["admin", "email-templates"] }); resetForm(); },
  });
  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteEmailTemplate(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "email-templates"] }),
  });

  function resetForm() { setEditing(null); setCreating(false); setForm(EMPTY_TEMPLATE); setVariablesInput(""); }

  function startEdit(item: EmailTemplate) {
    setCreating(false);
    setEditing(item);
    setForm({ name: item.name, template_type: item.template_type, subject_template: item.subject_template, body_html_template: item.body_html_template, variables: item.variables, active: item.active });
    setVariablesInput((item.variables || []).join(", "));
  }

  function handleSave() {
    const payload = { ...form, variables: variablesInput.split(",").map((v) => v.trim()).filter(Boolean) };
    if (editing) {
      updateMut.mutate({ id: editing.id, d: payload as unknown as Record<string, unknown> });
    } else {
      createMut.mutate(payload as unknown as Record<string, unknown>);
    }
  }

  const templates = (data?.data ?? []) as EmailTemplate[];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">Email Templates</h2>
        <button
          onClick={() => { setEditing(null); setCreating(true); setForm(EMPTY_TEMPLATE); setVariablesInput(""); }}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          Add Template
        </button>
      </div>

      {/* Inline Form */}
      {(creating || editing) && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 mb-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-gray-700">{editing ? "Edit Template" : "Add Template"}</h3>
            <button onClick={resetForm} className="p-1 text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Template Type</label>
              <select value={form.template_type} onChange={(e) => setForm({ ...form, template_type: e.target.value })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none bg-white">
                {TEMPLATE_TYPES.map((t) => <option key={t} value={t}>{t.replace(/_/g, " ")}</option>)}
              </select>
            </div>
          </div>
          <div className="mt-4">
            <label className="block text-xs font-medium text-gray-600 mb-1">Subject Template</label>
            <input value={form.subject_template} onChange={(e) => setForm({ ...form, subject_template: e.target.value })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
          </div>
          <div className="mt-4">
            <label className="block text-xs font-medium text-gray-600 mb-1">Body HTML Template</label>
            <textarea value={form.body_html_template} onChange={(e) => setForm({ ...form, body_html_template: e.target.value })} rows={6} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none font-mono" />
          </div>
          <div className="mt-4">
            <label className="block text-xs font-medium text-gray-600 mb-1">Variables (comma-separated)</label>
            <input value={variablesInput} onChange={(e) => setVariablesInput(e.target.value)} placeholder="customer_name, order_number, missing_fields" className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
          </div>
          <div className="flex justify-end mt-5">
            <button onClick={handleSave} disabled={createMut.isPending || updateMut.isPending} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 shadow-sm transition-all disabled:opacity-50">
              <Save className="w-4 h-4" />
              {editing ? "Update" : "Create"}
            </button>
          </div>
        </div>
      )}

      {/* Cards */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
          {Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-[140px] bg-gray-100 rounded-xl" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {templates.map((t) => (
            <div key={t.id} className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="text-sm font-bold text-gray-800">{t.name}</h4>
                  <span className={`inline-flex mt-1 px-2 py-0.5 text-[11px] font-semibold rounded-md ${t.active ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-500"}`}>
                    {t.active ? "Active" : "Inactive"}
                  </span>
                </div>
                <span className="inline-flex px-2 py-0.5 text-[11px] font-semibold rounded-md bg-indigo-50 text-indigo-700 capitalize">
                  {t.template_type.replace(/_/g, " ")}
                </span>
              </div>
              <p className="text-xs text-gray-500 mb-3 line-clamp-2">{t.subject_template || "No subject"}</p>
              <div className="flex items-center gap-2">
                <button onClick={() => startEdit(t)} className="px-3 py-1.5 text-xs font-medium text-amber-700 bg-amber-50 rounded-lg hover:bg-amber-100 transition-colors">Edit</button>
                <button onClick={() => deleteMut.mutate(t.id)} className="px-3 py-1.5 text-xs font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100 transition-colors">Delete</button>
              </div>
            </div>
          ))}
          {templates.length === 0 && (
            <div className="col-span-full text-center text-gray-400 text-sm py-8">No email templates configured.</div>
          )}
        </div>
      )}
    </div>
  );
}


// ─── Thresholds Tab ─────────────────────────────────────────────────────────

interface ThresholdConfig {
  auto_process_threshold: number;
  human_review_lower_bound: number;
  auto_communication_threshold: number;
  customer_response_timeout_hours: number;
  follow_up_delay_hours: number;
  duplicate_detection_window_hours: number;
}

const DEFAULT_THRESHOLDS: ThresholdConfig = {
  auto_process_threshold: 95,
  human_review_lower_bound: 70,
  auto_communication_threshold: 85,
  customer_response_timeout_hours: 48,
  follow_up_delay_hours: 24,
  duplicate_detection_window_hours: 72,
};

function ThresholdsTab() {
  const [thresholds, setThresholds] = useState<ThresholdConfig>(DEFAULT_THRESHOLDS);
  const [saved, setSaved] = useState(false);

  function handleSave() {
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  }

  function updateVal(key: keyof ThresholdConfig, val: number) {
    setThresholds((prev) => ({ ...prev, [key]: val }));
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">Thresholds</h2>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm max-w-2xl">
        <p className="text-xs text-gray-500 mb-6">
          These values are currently loaded from environment variables. Changes here will take effect after agents restart.
        </p>

        <div className="space-y-6">
          <ThresholdSlider label="Auto-Process Threshold" value={thresholds.auto_process_threshold} onChange={(v) => updateVal("auto_process_threshold", v)} min={50} max={100} unit="%" />
          <ThresholdSlider label="Human Review Lower Bound" value={thresholds.human_review_lower_bound} onChange={(v) => updateVal("human_review_lower_bound", v)} min={0} max={100} unit="%" />
          <ThresholdSlider label="Auto-Communication Threshold" value={thresholds.auto_communication_threshold} onChange={(v) => updateVal("auto_communication_threshold", v)} min={50} max={100} unit="%" />
          <ThresholdInput label="Customer Response Timeout" value={thresholds.customer_response_timeout_hours} onChange={(v) => updateVal("customer_response_timeout_hours", v)} unit="hours" />
          <ThresholdInput label="Follow-up Delay" value={thresholds.follow_up_delay_hours} onChange={(v) => updateVal("follow_up_delay_hours", v)} unit="hours" />
          <ThresholdInput label="Duplicate Detection Window" value={thresholds.duplicate_detection_window_hours} onChange={(v) => updateVal("duplicate_detection_window_hours", v)} unit="hours" />
        </div>

        <div className="flex items-center gap-3 mt-8">
          <button onClick={handleSave} className="flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 shadow-sm transition-all">
            <Save className="w-4 h-4" />
            Save
          </button>
          {saved && (
            <span className="text-sm text-emerald-600 font-medium animate-fade-in">
              Saved — restart agents to apply
            </span>
          )}
        </div>
      </div>
    </div>
  );
}


// ─── Shared Components ──────────────────────────────────────────────────────

function ThresholdSlider({ label, value, onChange, min, max, unit }: { label: string; value: number; onChange: (v: number) => void; min: number; max: number; unit: string }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-gray-700">{label}</label>
        <span className="text-sm font-bold text-gray-800">{value}{unit}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value))}
        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-amber-500"
      />
      <div className="flex justify-between mt-1">
        <span className="text-[11px] text-gray-400">{min}{unit}</span>
        <span className="text-[11px] text-gray-400">{max}{unit}</span>
      </div>
    </div>
  );
}

function ThresholdInput({ label, value, onChange, unit }: { label: string; value: number; onChange: (v: number) => void; unit: string }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      <div className="flex items-center gap-2">
        <input
          type="number"
          value={value}
          onChange={(e) => onChange(parseInt(e.target.value) || 0)}
          className="w-32 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none"
        />
        <span className="text-sm text-gray-500">{unit}</span>
      </div>
    </div>
  );
}


// ─── Users Tab ──────────────────────────────────────────────────────────────

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  active: boolean;
  created_at: string;
}

const ROLES = ["readonly", "agent", "supervisor", "admin"];

const EMPTY_USER = { email: "", name: "", password: "", role: "agent", active: true };

function UsersTab() {
  const queryClient = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [form, setForm] = useState(EMPTY_USER);

  const { data, isLoading } = useQuery({
    queryKey: ["admin", "users"],
    queryFn: getUsers,
  });

  const createMut = useMutation({
    mutationFn: (d: Record<string, unknown>) => createUser(d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["admin", "users"] }); resetForm(); },
  });
  const updateMut = useMutation({
    mutationFn: ({ id, d }: { id: string; d: Record<string, unknown> }) => updateUser(id, d),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["admin", "users"] }); resetForm(); },
  });
  const deleteMut = useMutation({
    mutationFn: (id: string) => deleteUser(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin", "users"] }),
  });

  function resetForm() { setEditing(null); setCreating(false); setForm(EMPTY_USER); }

  function startEdit(user: User) {
    setCreating(false);
    setEditing(user);
    setForm({ email: user.email, name: user.name, password: "", role: user.role, active: user.active });
  }

  function handleSave() {
    if (editing) {
      const payload: Record<string, unknown> = { email: form.email, name: form.name, role: form.role, active: form.active };
      if (form.password) payload.password = form.password;
      updateMut.mutate({ id: editing.id, d: payload });
    } else {
      createMut.mutate({ email: form.email, name: form.name, password: form.password || "changeme", role: form.role, active: form.active });
    }
  }

  const users = (data?.data ?? []) as User[];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-gray-800">User Management</h2>
        <button
          onClick={() => { setEditing(null); setCreating(true); setForm(EMPTY_USER); }}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          Add User
        </button>
      </div>

      {/* Inline Form */}
      {(creating || editing) && (
        <div className="bg-white border border-gray-200 rounded-xl p-5 mb-5 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-bold text-gray-700">{editing ? "Edit User" : "Add User"}</h3>
            <button onClick={resetForm} className="p-1 text-gray-400 hover:text-gray-600"><X className="w-4 h-4" /></button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Name</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">{editing ? "New Password (leave blank to keep)" : "Password"}</label>
              <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder={editing ? "••••••••" : ""} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Role</label>
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-400 focus:border-amber-400 outline-none bg-white">
                {ROLES.map((r) => <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>)}
              </select>
            </div>
          </div>
          <div className="flex items-center gap-4 mt-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={form.active} onChange={(e) => setForm({ ...form, active: e.target.checked })} className="w-4 h-4 rounded border-gray-300 text-amber-500 focus:ring-amber-400" />
              <span className="text-sm text-gray-700">Active</span>
            </label>
          </div>
          <div className="flex justify-end mt-5">
            <button onClick={handleSave} disabled={createMut.isPending || updateMut.isPending} className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 shadow-sm transition-all disabled:opacity-50">
              <Save className="w-4 h-4" />
              {editing ? "Update" : "Create"}
            </button>
          </div>
        </div>
      )}

      {/* Table */}
      {isLoading ? (
        <div className="space-y-2 animate-pulse">
          {Array.from({ length: 3 }).map((_, i) => <div key={i} className="h-[48px] bg-gray-100 rounded-lg" />)}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200/80 overflow-hidden shadow-sm">
          <table className="w-full text-[13px]">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Name</th>
                <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Email</th>
                <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Role</th>
                <th className="px-5 py-3 text-center text-[12px] font-bold text-gray-700 uppercase tracking-wider">Status</th>
                <th className="px-5 py-3 text-right text-[12px] font-bold text-gray-700 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="px-5 py-3 font-medium text-gray-800">{u.name}</td>
                  <td className="px-5 py-3 text-gray-600">{u.email}</td>
                  <td className="px-5 py-3">
                    <span className={`inline-flex px-2 py-0.5 text-[11px] font-semibold rounded-md ${
                      u.role === "admin" ? "bg-purple-50 text-purple-700" :
                      u.role === "supervisor" ? "bg-blue-50 text-blue-700" :
                      u.role === "agent" ? "bg-emerald-50 text-emerald-700" :
                      "bg-gray-100 text-gray-600"
                    }`}>
                      {u.role.charAt(0).toUpperCase() + u.role.slice(1)}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-center">
                    <span className={`inline-flex px-2 py-0.5 text-[11px] font-semibold rounded-md ${u.active ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>
                      {u.active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-right">
                    <button onClick={() => startEdit(u)} className="p-1.5 text-gray-400 hover:text-amber-600 rounded transition-colors"><Pencil className="w-3.5 h-3.5" /></button>
                    <button onClick={() => deleteMut.mutate(u.id)} className="p-1.5 text-gray-400 hover:text-red-600 rounded transition-colors ml-1"><Trash2 className="w-3.5 h-3.5" /></button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr><td colSpan={5} className="px-5 py-8 text-center text-gray-400 text-sm">No users configured.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
