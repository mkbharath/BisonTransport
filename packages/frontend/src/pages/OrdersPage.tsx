import { useQuery } from "@tanstack/react-query";
import { useSearchParams, Link } from "react-router-dom";
import { getOrders } from "../lib/api";
import { ChevronLeft, ChevronRight, Plus } from "lucide-react";

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
    <div className="flex items-center gap-2 w-[120px]">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.min(score, 100)}%` }} />
      </div>
      <span className="text-[12px] font-bold text-gray-700 w-10 text-right">{score.toFixed(0)}%</span>
    </div>
  );
}

export function OrdersPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = parseInt(searchParams.get("page") || "1");
  const status = searchParams.get("status") || undefined;

  const { data, isLoading } = useQuery({
    queryKey: ["orders", page, status],
    queryFn: () => getOrders({ page, limit: 20, ...(status ? { status } : {}) }),
  });

  const setPage = (newPage: number) => {
    searchParams.set("page", String(newPage));
    setSearchParams(searchParams);
  };

  return (
    <div className="animate-slide-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Orders</h1>
        <Link
          to="/orders/new"
          className="flex items-center gap-2 px-4 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 shadow-sm transition-all"
        >
          <Plus className="w-4 h-4" />
          New Order
        </Link>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 mb-5 overflow-x-auto pb-1">
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

      {isLoading ? (
        <div className="space-y-2 animate-pulse">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-[52px] bg-gray-100 rounded-lg" />
          ))}
        </div>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-gray-200/80 overflow-hidden shadow-sm">
            <table className="w-full text-[13px] table-fixed">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider w-[18%]">Order</th>
                  <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider w-[22%]">Customer</th>
                  <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider w-[12%]">Pickup</th>
                  <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider w-[13%]">Equipment</th>
                  <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider w-[15%]">Status</th>
                  <th className="px-5 py-3 text-left text-[12px] font-bold text-gray-700 uppercase tracking-wider w-[20%]">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {data?.data.map((order: Record<string, unknown>) => {
                  const statusStr = order.status as string;
                  const style = STATUS_STYLES[statusStr] || { bg: "bg-gray-50 text-gray-600", dot: "bg-gray-400" };
                  return (
                    <tr key={order.id as string} className="hover:bg-slate-50/60 transition-colors">
                      <td className="px-5 py-3">
                        <Link to={`/orders/${order.id as string}`} className="text-blue-600 hover:text-blue-800 font-semibold whitespace-nowrap text-[12px]">
                          {order.order_number as string}
                        </Link>
                      </td>
                      <td className="px-5 py-3 text-gray-700 font-medium truncate">{(order.customer_name as string) || "—"}</td>
                      <td className="px-5 py-3 text-gray-600">{(order.pickup_date as string) || "—"}</td>
                      <td className="px-5 py-3 text-gray-600 capitalize">{(order.equipment_type as string)?.replace("_", " ") || "—"}</td>
                      <td className="px-5 py-3">
                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[12px] font-semibold ${style.bg}`}>
                          <span className={`w-2 h-2 rounded-full ${style.dot}`} />
                          {statusStr?.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="px-5 py-3">
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
