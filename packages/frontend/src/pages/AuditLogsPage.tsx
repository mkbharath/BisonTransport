import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { getAuditLogs } from "../lib/api";
import {
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Download,
  Search,
} from "lucide-react";

const TABS = [
  { key: "all", label: "All" },
  { key: "agent_actions", label: "Agent Actions" },
  { key: "user_actions", label: "User Actions" },
  { key: "order_history", label: "Order History" },
  { key: "validations", label: "Validations" },
];

const ACTOR_BADGE_STYLES: Record<string, string> = {
  user: "bg-blue-50 text-blue-700",
  agent: "bg-amber-50 text-amber-700",
  system: "bg-gray-100 text-gray-600",
};

function formatTimestamp(ts: string): string {
  const d = new Date(ts);
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function truncateId(id: string | null): string {
  if (!id) return "—";
  return id.length > 12 ? `${id.slice(0, 8)}...` : id;
}

function JsonDiffViewer({
  oldValue,
  newValue,
}: {
  oldValue: unknown;
  newValue: unknown;
}) {
  const formatJson = (val: unknown): string => {
    if (val == null) return "null";
    if (typeof val === "string") {
      try {
        return JSON.stringify(JSON.parse(val), null, 2);
      } catch {
        return val;
      }
    }
    return JSON.stringify(val, null, 2);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
      <div>
        <p className="text-[11px] font-semibold text-red-600 uppercase tracking-wide mb-1">
          Previous
        </p>
        <pre className="bg-red-50 border border-red-100 rounded p-3 text-xs font-mono text-red-900 overflow-x-auto max-h-64 overflow-y-auto whitespace-pre-wrap">
          {formatJson(oldValue)}
        </pre>
      </div>
      <div>
        <p className="text-[11px] font-semibold text-emerald-600 uppercase tracking-wide mb-1">
          Current
        </p>
        <pre className="bg-emerald-50 border border-emerald-100 rounded p-3 text-xs font-mono text-emerald-900 overflow-x-auto max-h-64 overflow-y-auto whitespace-pre-wrap">
          {formatJson(newValue)}
        </pre>
      </div>
    </div>
  );
}

export function AuditLogsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState(searchParams.get("search") || "");
  const [dateFrom, setDateFrom] = useState(searchParams.get("date_from") || "");
  const [dateTo, setDateTo] = useState(searchParams.get("date_to") || "");
  const [actorFilter, setActorFilter] = useState(searchParams.get("actor_type") || "all");

  const page = parseInt(searchParams.get("page") || "1");
  const tab = searchParams.get("tab") || "all";

  const queryParams: Record<string, string | number> = { page, limit: 50 };
  if (searchParams.get("search")) queryParams.search = searchParams.get("search")!;
  if (searchParams.get("actor_type") && searchParams.get("actor_type") !== "all") {
    queryParams.actor_type = searchParams.get("actor_type")!;
  }
  if (searchParams.get("date_from")) queryParams.date_from = searchParams.get("date_from")!;
  if (searchParams.get("date_to")) queryParams.date_to = searchParams.get("date_to")!;
  if (tab !== "all") queryParams.tab = tab;

  const { data, isLoading } = useQuery({
    queryKey: ["audit-logs", queryParams],
    queryFn: () => getAuditLogs(queryParams),
  });

  const setPage = (newPage: number) => {
    searchParams.set("page", String(newPage));
    setSearchParams(searchParams);
  };

  const applyFilters = () => {
    if (searchInput) searchParams.set("search", searchInput);
    else searchParams.delete("search");
    if (dateFrom) searchParams.set("date_from", dateFrom);
    else searchParams.delete("date_from");
    if (dateTo) searchParams.set("date_to", dateTo);
    else searchParams.delete("date_to");
    if (actorFilter !== "all") searchParams.set("actor_type", actorFilter);
    else searchParams.delete("actor_type");
    searchParams.set("page", "1");
    setSearchParams(searchParams);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") applyFilters();
  };

  const exportCsv = () => {
    if (!data?.data?.length) return;
    const headers = ["Timestamp", "Actor Type", "Actor ID", "Action", "Entity Type", "Entity ID"];
    const rows = data.data.map((row: Record<string, unknown>) => [
      row.timestamp as string,
      row.actor_type as string,
      row.actor_id as string,
      row.action as string,
      row.entity_type as string,
      row.entity_id as string,
    ]);
    const csv = [headers, ...rows].map((r) => r.map((c) => `"${String(c ?? "").replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `audit-logs-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Audit Logs</h1>
        <button
          onClick={exportCsv}
          disabled={!data?.data?.length}
          className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 shadow-sm transition-all disabled:opacity-40"
        >
          <Download className="w-4 h-4" />
          Export CSV
        </button>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1.5 mb-5 overflow-x-auto pb-1">
        {TABS.map((t) => {
          const isActive = tab === t.key;
          return (
            <button
              key={t.key}
              onClick={() => {
                if (t.key === "all") searchParams.delete("tab");
                else searchParams.set("tab", t.key);
                searchParams.set("page", "1");
                setSearchParams(searchParams);
              }}
              className={`px-3.5 py-1.5 text-[12px] font-medium rounded-md whitespace-nowrap transition-all ${
                isActive
                  ? "bg-[#0f1b2d] text-white shadow-sm"
                  : "bg-white text-gray-500 border border-gray-200 hover:border-gray-300 hover:text-gray-700"
              }`}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-3 mb-5 bg-white rounded-xl border border-gray-200/80 p-4 shadow-sm">
        <div className="flex-1 min-w-[200px]">
          <label className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wide mb-1">
            Search
          </label>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search actor, action, entity..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-400"
            />
          </div>
        </div>
        <div className="w-[150px]">
          <label className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wide mb-1">
            From
          </label>
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => setDateFrom(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-400"
          />
        </div>
        <div className="w-[150px]">
          <label className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wide mb-1">
            To
          </label>
          <input
            type="date"
            value={dateTo}
            onChange={(e) => setDateTo(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-400"
          />
        </div>
        <div className="w-[140px]">
          <label className="block text-[11px] font-semibold text-gray-500 uppercase tracking-wide mb-1">
            Actor Type
          </label>
          <select
            value={actorFilter}
            onChange={(e) => setActorFilter(e.target.value)}
            className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-400 bg-white"
          >
            <option value="all">All</option>
            <option value="user">User</option>
            <option value="agent">Agent</option>
            <option value="system">System</option>
          </select>
        </div>
        <button
          onClick={applyFilters}
          className="px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 shadow-sm transition-all"
        >
          Apply
        </button>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-2 animate-pulse">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-[48px] bg-gray-100 rounded-lg" />
          ))}
        </div>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-gray-200/80 overflow-hidden shadow-sm">
            <table className="w-full text-[13px]">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="px-2 py-3 w-[30px]" />
                  <th className="px-3 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Timestamp</th>
                  <th className="px-3 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Actor Type</th>
                  <th className="px-3 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Actor ID</th>
                  <th className="px-3 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Action</th>
                  <th className="px-3 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider">Entity</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {data?.data?.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-5 py-12 text-center text-gray-400 text-sm">
                      No audit logs found.
                    </td>
                  </tr>
                )}
                {data?.data?.map((row: Record<string, unknown>) => {
                  const id = row.id as string;
                  const isExpanded = expandedRow === id;
                  const actorType = (row.actor_type as string) || "system";
                  const badgeStyle =
                    ACTOR_BADGE_STYLES[actorType.toLowerCase()] || ACTOR_BADGE_STYLES.system;

                  return (
                    <>
                      <tr
                        key={id}
                        className="hover:bg-slate-50/60 transition-colors cursor-pointer"
                        onClick={() => setExpandedRow(isExpanded ? null : id)}
                      >
                        <td className="px-2 py-3 w-[30px]">
                          {isExpanded ? (
                            <ChevronUp className="w-4 h-4 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-gray-400" />
                          )}
                        </td>
                        <td className="px-3 py-3 text-gray-600 text-[13px]">
                          {row.timestamp ? formatTimestamp(row.timestamp as string) : "—"}
                        </td>
                        <td className="px-3 py-3">
                          <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold capitalize ${badgeStyle}`}>
                            {actorType}
                          </span>
                        </td>
                        <td className="px-3 py-3 text-gray-600 font-mono text-[12px]">
                          {(row.actor_id as string) || "—"}
                        </td>
                        <td className="px-3 py-3 text-gray-900 font-semibold text-[13px]">
                          {(row.action as string)?.replace(/_/g, " ") || "—"}
                        </td>
                        <td className="px-3 py-3 text-gray-600 text-[13px]">
                          <span className="text-gray-700 font-medium">{row.entity_type as string}</span>
                          {row.entity_id && (
                            <span className="ml-2 font-mono text-[11px] text-gray-500">
                              {(row.entity_id as string)?.slice(0, 16)}...
                            </span>
                          )}
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr key={`${id}-detail`}>
                          <td colSpan={6} className="px-5 pb-4 pt-1 border-t border-gray-100 bg-slate-50/40">
                            <JsonDiffViewer
                              oldValue={row.previous_status ?? row.old_value_json ?? null}
                              newValue={row.new_status ?? row.detail_json ?? row.new_value_json ?? null}
                            />
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-1 mt-5">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page <= 1}
                className="p-2 rounded-lg text-gray-500 hover:bg-white hover:shadow-sm disabled:opacity-30 transition-all"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              {Array.from({ length: Math.min(data.total_pages, 7) }).map((_, i) => (
                <button
                  key={i + 1}
                  onClick={() => setPage(i + 1)}
                  className={`w-8 h-8 rounded-lg text-xs font-medium transition-all ${
                    page === i + 1
                      ? "bg-[#0f1b2d] text-white"
                      : "text-gray-500 hover:bg-white"
                  }`}
                >
                  {i + 1}
                </button>
              ))}
              <button
                onClick={() => setPage(Math.min(data.total_pages, page + 1))}
                disabled={page >= data.total_pages}
                className="p-2 rounded-lg text-gray-500 hover:bg-white hover:shadow-sm disabled:opacity-30 transition-all"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
