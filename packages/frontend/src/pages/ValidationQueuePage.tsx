import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getHitlQueue, approveOrder, rejectOrder } from "../lib/api";
import { Link } from "react-router-dom";
import { useState } from "react";
import { CheckCircle, XCircle, ClipboardCheck, Search, ArrowUpDown } from "lucide-react";
import { useAuth } from "../hooks/useAuth";

function ConfidenceRing({ score }: { score: number }) {
  const circumference = 2 * Math.PI * 15;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 90 ? "#10b981" : score >= 70 ? "#f59e0b" : "#ef4444";
  return (
    <div className="relative w-11 h-11 flex-shrink-0">
      <svg className="w-11 h-11 -rotate-90" viewBox="0 0 34 34">
        <circle cx="17" cy="17" r="15" fill="none" stroke="#f1f5f9" strokeWidth="2.5" />
        <circle cx="17" cy="17" r="15" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeDasharray={circumference} strokeDashoffset={offset} />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-[10px] font-bold text-gray-700">{score.toFixed(0)}</span>
    </div>
  );
}

export function ValidationQueuePage() {
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const canApprove = user?.role === "agent" || user?.role === "supervisor" || user?.role === "admin";
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("created_desc");

  const { data, isLoading } = useQuery({
    queryKey: ["hitl-queue", searchTerm, sortBy],
    queryFn: () => getHitlQueue({ limit: 50, ...(searchTerm ? { search: searchTerm } : {}), sort: sortBy }),
    refetchInterval: 15_000,
  });

  const approveMutation = useMutation({
    mutationFn: (orderId: string) => approveOrder(orderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hitl-queue"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (orderId: string) => rejectOrder(orderId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hitl-queue"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });

  return (
    <div className="animate-slide-up">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Review Queue</h1>
          <p className="text-sm text-gray-500 mt-0.5">{data?.total_count ?? 0} items pending review</p>
        </div>
      </div>

      {/* Search + Sort */}
      <div className="flex items-center gap-3 mb-5">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by order number or customer..."
            className="w-full pl-10 pr-4 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500/40 focus:border-amber-500"
          />
          {searchTerm && (
            <button onClick={() => setSearchTerm("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 text-xs">Clear</button>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <ArrowUpDown className="w-4 h-4 text-gray-400" />
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="text-sm border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-amber-500/40 bg-white">
            <option value="created_desc">Newest First</option>
            <option value="created_asc">Oldest First</option>
            <option value="confidence_asc">Lowest Confidence</option>
            <option value="confidence_desc">Highest Confidence</option>
          </select>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3 animate-pulse">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-[88px] bg-gray-100 rounded-xl" />
          ))}
        </div>
      ) : data?.data.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-16 text-center">
          <ClipboardCheck className="w-14 h-14 text-gray-200 mx-auto mb-4" />
          <p className="text-lg font-semibold text-gray-600">All caught up!</p>
          <p className="text-sm text-gray-400 mt-1">No orders pending review.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {data?.data.map((item: Record<string, unknown>) => {
            const confidence = item.overall_confidence_score as number | null;
            const borderColor = confidence == null ? "border-l-gray-200" : confidence >= 90 ? "border-l-emerald-400" : confidence >= 70 ? "border-l-amber-400" : "border-l-red-400";
            return (
              <div key={item.id as string} className={`bg-white rounded-xl border border-gray-200/80 p-4 pl-5 border-l-[3px] ${borderColor} hover:shadow-md transition-all`}>
                <div className="flex items-center gap-4">
                  {confidence != null && <ConfidenceRing score={confidence} />}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <Link to={`/orders/${item.id as string}`} className="text-[13px] font-semibold text-blue-600 hover:text-blue-800">
                        {item.order_number as string}
                      </Link>
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200/60 capitalize">
                        {(item.status as string)?.replace(/_/g, " ")}
                      </span>
                    </div>
                    <p className="text-[13px] text-gray-700">
                      <span className="font-medium">{(item.customer_name as string) || "Unknown"}</span>
                      {item.equipment_type && (
                        <span className="text-gray-400 ml-2">· {(item.equipment_type as string).replace(/_/g, " ")}</span>
                      )}
                    </p>
                  </div>
                  {canApprove && (
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => approveMutation.mutate(item.id as string)}
                      disabled={approveMutation.isPending}
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-emerald-600 text-white text-[12px] font-semibold rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors shadow-sm shadow-emerald-500/20"
                    >
                      <CheckCircle className="w-3.5 h-3.5" />
                      Approve
                    </button>
                    <button
                      onClick={() => rejectMutation.mutate(item.id as string)}
                      disabled={rejectMutation.isPending}
                      className="inline-flex items-center gap-1.5 px-3.5 py-2 text-red-600 text-[12px] font-semibold rounded-lg border border-red-200 bg-red-50 hover:bg-red-100 disabled:opacity-50 transition-colors"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      Reject
                    </button>
                  </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
