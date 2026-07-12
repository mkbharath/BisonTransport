import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Search, Pencil, X, Save, Shield } from "lucide-react";

const API_BASE = "/api/v1";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("token") || sessionStorage.getItem("token");
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers: { ...headers, ...options.headers as Record<string, string> } });
  if (!res.ok) throw new Error(`${res.status}`);
  if (res.status === 204) return null as T;
  return res.json();
}

interface Customer {
  id: string;
  name: string;
  external_id: string | null;
  email_domains: string[] | null;
  always_human_review: boolean;
  default_equipment_type: string | null;
  opt_out: boolean;
  created_at: string;
}

export function CustomersPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<Customer | null>(null);
  const [form, setForm] = useState({ name: "", external_id: "", email_domains: "", always_human_review: false, default_equipment_type: "" });

  const { data, isLoading } = useQuery({
    queryKey: ["customers", search],
    queryFn: () => request<{ data: Customer[]; total_count: number }>(`/customers?limit=50${search ? `&search=${search}` : ""}`),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: Record<string, unknown> }) =>
      request(`/customers/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["customers"] }); setEditing(null); },
  });

  function startEdit(c: Customer) {
    setEditing(c);
    setForm({
      name: c.name,
      external_id: c.external_id || "",
      email_domains: (c.email_domains || []).join(", "),
      always_human_review: c.always_human_review,
      default_equipment_type: c.default_equipment_type || "",
    });
  }

  function handleSave() {
    if (!editing) return;
    const payload: Record<string, unknown> = {
      name: form.name,
      external_id: form.external_id || null,
      email_domains: form.email_domains ? form.email_domains.split(",").map(s => s.trim()).filter(Boolean) : null,
      always_human_review: form.always_human_review,
      default_equipment_type: form.default_equipment_type || null,
    };
    updateMut.mutate({ id: editing.id, payload });
  }

  const customers = data?.data || [];

  return (
    <div className="animate-slide-up">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Customers</h1>
        <span className="text-sm text-gray-500">{data?.total_count ?? 0} customers</span>
      </div>

      {/* Search */}
      <div className="relative max-w-md mb-5">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name or ID..."
          className="w-full pl-10 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500"
        />
      </div>

      {/* Edit Modal */}
      {editing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="bg-white rounded-2xl w-[480px] p-7 shadow-2xl border border-gray-100">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold text-gray-900">Edit Customer</h3>
              <button onClick={() => setEditing(null)} className="p-1 text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">Name</label>
                <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400" />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">External ID</label>
                <input value={form.external_id} onChange={(e) => setForm({ ...form, external_id: e.target.value })} className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400" />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">Email Domains (comma-separated)</label>
                <input value={form.email_domains} onChange={(e) => setForm({ ...form, email_domains: e.target.value })} placeholder="company.com, corp.ca" className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400" />
              </div>
              <div>
                <label className="block text-xs font-bold text-gray-500 uppercase tracking-widest mb-1">Default Equipment</label>
                <select value={form.default_equipment_type} onChange={(e) => setForm({ ...form, default_equipment_type: e.target.value })} className="w-full px-3 py-2.5 border border-gray-200 rounded-xl text-sm bg-white focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-400">
                  <option value="">None</option>
                  <option value="dry_van">Dry Van</option>
                  <option value="reefer">Reefer</option>
                  <option value="flatbed">Flatbed</option>
                  <option value="tanker">Tanker</option>
                  <option value="step_deck">Step Deck</option>
                </select>
              </div>
              <label className="flex items-center gap-3 cursor-pointer p-3 bg-amber-50 border border-amber-200 rounded-xl">
                <input type="checkbox" checked={form.always_human_review} onChange={(e) => setForm({ ...form, always_human_review: e.target.checked })} className="w-4 h-4 rounded border-gray-300 text-amber-500 focus:ring-amber-400" />
                <div>
                  <span className="text-sm font-semibold text-amber-800">Always Require Human Review</span>
                  <p className="text-xs text-amber-600">Orders from this customer will always go to HITL queue</p>
                </div>
              </label>
            </div>
            <div className="flex justify-end gap-3 mt-6">
              <button onClick={() => setEditing(null)} className="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700">Cancel</button>
              <button onClick={handleSave} disabled={updateMut.isPending} className="px-5 py-2 text-sm font-bold text-white bg-gradient-to-r from-teal-500 to-cyan-600 rounded-xl hover:from-teal-600 hover:to-cyan-700 disabled:opacity-50 shadow-md">
                <Save className="w-4 h-4 inline mr-1" />Save
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Table */}
      {isLoading ? (
        <div className="space-y-2 animate-pulse">{Array.from({ length: 5 }).map((_, i) => <div key={i} className="h-12 bg-gray-100 rounded-lg" />)}</div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto shadow-sm">
          <table className="w-full text-[13px] min-w-[700px]">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-4 py-3 text-left text-[11px] font-bold text-gray-500 uppercase tracking-wider">Customer</th>
                <th className="px-4 py-3 text-left text-[11px] font-bold text-gray-500 uppercase tracking-wider">ID</th>
                <th className="px-4 py-3 text-left text-[11px] font-bold text-gray-500 uppercase tracking-wider">Email Domains</th>
                <th className="px-4 py-3 text-center text-[11px] font-bold text-gray-500 uppercase tracking-wider">Equipment</th>
                <th className="px-4 py-3 text-center text-[11px] font-bold text-gray-500 uppercase tracking-wider">HITL</th>
                <th className="px-4 py-3 text-right text-[11px] font-bold text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {customers.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50/60 transition-colors">
                  <td className="px-4 py-3 font-semibold text-gray-800">{c.name}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs font-mono">{c.external_id || "—"}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">{(c.email_domains || []).join(", ") || "—"}</td>
                  <td className="px-4 py-3 text-center text-gray-600 capitalize text-xs">{c.default_equipment_type?.replace("_", " ") || "—"}</td>
                  <td className="px-4 py-3 text-center">
                    {c.always_human_review ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-bold rounded-md bg-amber-50 text-amber-700"><Shield className="w-3 h-3" />Always HITL</span>
                    ) : (
                      <span className="text-gray-400 text-xs">Auto</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => startEdit(c)} className="p-1.5 text-gray-400 hover:text-teal-600 rounded transition-colors"><Pencil className="w-3.5 h-3.5" /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
