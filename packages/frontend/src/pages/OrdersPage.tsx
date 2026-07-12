import { useQuery } from "@tanstack/react-query";
import { useSearchParams, Link } from "react-router-dom";
import { useState, useEffect, useRef } from "react";
import { getOrders, approveOrder } from "../lib/api";
import { ChevronLeft, ChevronRight, Plus, Search, CheckSquare, Download } from "lucide-react";

const STATUS_STYLES: Record<string, { bg: string; dot: string }> = {
  order_created: { bg: "bg-emerald-50 text-emerald-700", dot: "bg-emerald-500" },
  extracted: { bg: "bg-blue-50 text-blue-700", dot: "bg-blue-500" },
  pending_review: { bg: "bg-amber-50 text-amber-700", dot: "bg-amber-500" },
  awaiting_customer: { bg: "bg-orange-50 text-orange-700", dot: "bg-orange-500" },
  validated: { bg: "bg-indigo-50 text-indigo-700", dot: "bg-indigo-500" },
  failed: { bg: "bg-red-50 text-red-700", dot: "bg-red-500" },
  cancelled: { bg: "bg-gray-50 text-gray-600", dot: "bg-gray-400" },
};

const FILTER_TABS = [
  { key: "all", label: "All" },
  { key: "order_created", label: "Created" },
  { key: "pending_review", label: "In Review" },
  { key: "awaiting_customer", label: "Awaiting" },
  { key: "extracted", label: "Extracted" },
  { key: "failed", label: "Failed" },
];

function ConfidenceBar({ score }: { score: number | null }) {
  if (score == null) return <span className="text-gray-300 text-xs">—</span>;
  const color = score >= 90 ? "bg-emerald-500" : score >= 80 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-2 w-[100px]">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(score, 100)}%` }} />
      </div>
      <span className="text-[12px] font-bold text-gray-700 w-8 text-right">{score.toFixed(0)}%</span>
    </div>
  );
}

export function OrdersPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = parseInt(searchParams.get("page") || "1");
  const status = searchParams.get("status") || undefined;
  const [searchTerm, setSearchTerm] = useState(searchParams.get("search") || "");
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  // Debounced search — updates URL params 300ms after user stops typing
  useEffect(() => {
    debounceRef.current = setTimeout(() => {
      const current = searchParams.get("search") || "";
      if (searchTerm.trim() !== current) {
        if (searchTerm.trim()) {
          searchParams.set("search", searchTerm.trim());
        } else {
          searchParams.delete("search");
        }
        searchParams.set("page", "1");
        setSearchParams(searchParams);
      }
    }, 300);
    return () => clearTimeout(debounceRef.current);
  }, [searchTerm]);

  const { data, isLoading } = useQuery({
    queryKey: ["orders", page, status, searchParams.get("search")],
    queryFn: () => getOrders({ page, limit: 20, ...(status ? { status } : {}), ...(searchParams.get("search") ? { search: searchParams.get("search")! } : {}) }),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
  };

  const setPage = (newPage: number) => {
    searchParams.set("page", String(newPage));
    setSearchParams(searchParams);
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (!data?.data) return;
    if (selectedIds.size === data.data.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(data.data.map((o: Record<string, unknown>) => o.id as string)));
    }
  };

  const handleBulkApprove = async () => {
    if (!confirm(`Approve ${selectedIds.size} selected orders?`)) return;
    for (const id of selectedIds) {
      try { await approveOrder(id); } catch { /* skip failed */ }
    }
    setSelectedIds(new Set());
    window.location.reload();
  };

  const handleExportCSV = () => {
    if (!data?.data) return;
    const selected = data.data.filter((o: Record<string, unknown>) => selectedIds.has(o.id as string));
    const rows = selected.length > 0 ? selected : data.data;
    const headers = ["Order Number", "Customer", "Status", "Pickup Date", "Equipment", "Confidence"];
    const csv = [
      headers.join(","),
      ...rows.map((o: Record<string, unknown>) =>
        [o.order_number, `"${o.customer_name || ""}"`, o.status, o.pickup_date || "", o.equipment_type || "", o.overall_confidence_score || ""].join(",")
      ),
    ].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "orders_export.csv"; a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Orders</h1>
        <div className="flex items-center gap-2">
          <button
            onClick={handleExportCSV}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors shadow-sm"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
          <Link
            to="/orders/new"
          className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          New Order
        </Link>
        </div>
      </div>

      {/* Search + Filter Tabs */}
      <div className="flex items-center gap-3 mb-5">
        <div className="flex items-center gap-1.5 overflow-x-auto">
          {FILTER_TABS.map((tab) => {
            const isActive = (tab.key === "all" && !status) || status === tab.key;
            return (
              <button
                key={tab.key}
                onClick={() => {
                  if (tab.key === "all") searchParams.delete("status");
                  else searchParams.set("status", tab.key);
                  searchParams.set("page", "1");
                  setSearchParams(searchParams);
                }}
                className={`px-3.5 py-1.5 text-[12px] font-medium rounded-md whitespace-nowrap transition-all ${
                  isActive
                    ? "bg-[#0f1b2d] text-white shadow-sm"
                    : "bg-white text-gray-500 border border-gray-200 hover:border-gray-300 hover:text-gray-700"
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </div>
        <form onSubmit={handleSearch} className="ml-auto relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search orders..."
            className="w-[260px] pl-9 pr-8 py-1.5 text-sm border border-gray-200 rounded-md focus:outline-none focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500"
          />
          {searchParams.get("search") && (
            <button type="button" onClick={() => { setSearchTerm(""); searchParams.delete("search"); searchParams.set("page", "1"); setSearchParams(searchParams); }} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs">✕</button>
          )}
        </form>
      </div>

      {isLoading ? (
        <div className="space-y-2 animate-pulse">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-[52px] bg-gray-100 rounded-lg" />
          ))}
        </div>
      ) : (
        <>
          {/* Bulk Actions Bar */}
          {selectedIds.size > 0 && (
            <div className="flex items-center gap-3 mb-3 px-4 py-2 bg-teal-50 border border-teal-200 rounded-xl">
              <span className="text-sm font-medium text-teal-800">{selectedIds.size} selected</span>
              <button onClick={handleBulkApprove} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-white bg-teal-600 rounded-lg hover:bg-teal-700"><CheckSquare className="w-3.5 h-3.5" />Approve All</button>
              <button onClick={handleExportCSV} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-teal-700 bg-white border border-teal-300 rounded-lg hover:bg-teal-50"><Download className="w-3.5 h-3.5" />Export CSV</button>
              <button onClick={() => setSelectedIds(new Set())} className="text-xs text-teal-600 hover:text-teal-800 ml-auto">Clear</button>
            </div>
          )}

          <div className="bg-white rounded-xl border border-gray-200/80 overflow-x-auto shadow-sm">
            <table className="w-full text-[13px] min-w-[800px]">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="px-3 py-3 w-10">
                    <input type="checkbox" checked={data?.data?.length > 0 && selectedIds.size === data.data.length} onChange={toggleAll} className="w-4 h-4 rounded border-gray-300 text-teal-500 focus:ring-teal-400" />
                  </th>
                  <th className="px-4 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Order</th>
                  <th className="px-4 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Customer</th>
                  <th className="px-4 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Pickup</th>
                  <th className="px-4 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Equipment</th>
                  <th className="px-4 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {data?.data.map((order: Record<string, unknown>) => {
                  const statusStr = order.status as string;
                  const style = STATUS_STYLES[statusStr] || { bg: "bg-gray-50 text-gray-600", dot: "bg-gray-400" };
                  const orderId = order.id as string;
                  return (
                    <tr key={orderId} className={`hover:bg-slate-50/60 transition-colors ${selectedIds.has(orderId) ? "bg-teal-50/50" : ""}`}>
                      <td className="px-3 py-3">
                        <input type="checkbox" checked={selectedIds.has(orderId)} onChange={() => toggleSelect(orderId)} className="w-4 h-4 rounded border-gray-300 text-teal-500 focus:ring-teal-400" />
                      </td>
                      <td className="px-4 py-3">
                        <Link to={`/orders/${orderId}`} className="text-blue-600 hover:text-blue-800 font-semibold whitespace-nowrap text-[12px]">
                          {order.order_number as string}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-gray-700 font-medium truncate">{(order.customer_name as string) || "—"}</td>
                      <td className="px-4 py-3 text-gray-600 whitespace-nowrap">{(order.pickup_date as string) || "—"}</td>
                      <td className="px-4 py-3 text-gray-600 capitalize whitespace-nowrap">{(order.equipment_type as string)?.replace("_", " ") || "—"}</td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[12px] font-semibold whitespace-nowrap ${style.bg}`}>
                          <span className={`w-2 h-2 rounded-full ${style.dot}`} />
                          {statusStr?.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <ConfidenceBar score={order.overall_confidence_score as number | null} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-1 mt-5">
              <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page <= 1} className="p-2 rounded-lg text-gray-500 hover:bg-white hover:shadow-sm disabled:opacity-30 transition-all">
                <ChevronLeft className="w-4 h-4" />
              </button>
              {Array.from({ length: Math.min(data.total_pages, 7) }).map((_, i) => (
                <button key={i + 1} onClick={() => setPage(i + 1)} className={`w-8 h-8 rounded-lg text-xs font-medium transition-all ${page === i + 1 ? "bg-[#0f1b2d] text-white" : "text-gray-500 hover:bg-white"}`}>
                  {i + 1}
                </button>
              ))}
              <button onClick={() => setPage(Math.min(data.total_pages, page + 1))} disabled={page >= data.total_pages} className="p-2 rounded-lg text-gray-500 hover:bg-white hover:shadow-sm disabled:opacity-30 transition-all">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
