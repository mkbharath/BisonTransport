import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getHitlQueue, approveOrder, rejectOrder } from "../lib/api";
import { Link } from "react-router-dom";

export function ValidationQueuePage() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["hitl-queue"],
    queryFn: () => getHitlQueue({ limit: 50 }),
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
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Validation Queue</h1>
        <span className="text-sm text-gray-500">
          {data?.total_count ?? 0} items pending review
        </span>
      </div>

      {isLoading ? (
        <div className="animate-pulse space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-20 bg-gray-200 rounded-lg" />
          ))}
        </div>
      ) : data?.data.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
          <p className="text-gray-400 text-lg">Queue is empty</p>
          <p className="text-gray-400 text-sm mt-1">All orders are processed or awaiting customer response.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {data?.data.map((item: any) => (
            <div key={item.id} className="bg-white rounded-lg shadow-sm border p-4 flex items-center gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <Link to={`/orders/${item.id}`} className="font-medium text-brand-600 hover:underline">
                    {item.order_number}
                  </Link>
                  <span className="px-2 py-0.5 rounded-full text-xs bg-yellow-100 text-yellow-800 capitalize">
                    {item.status?.replace("_", " ")}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {item.customer_name || "Unknown Customer"} — {item.equipment_type?.replace("_", " ") || "N/A"}
                </p>
              </div>
              <div className="text-right flex-shrink-0">
                <div className={`text-lg font-bold ${
                  (item.overall_confidence_score || 0) >= 90 ? "text-green-600" :
                  (item.overall_confidence_score || 0) >= 70 ? "text-yellow-600" : "text-red-600"
                }`}>
                  {item.overall_confidence_score != null ? `${Number(item.overall_confidence_score).toFixed(1)}%` : "—"}
                </div>
                <p className="text-xs text-gray-400">confidence</p>
              </div>
              <div className="flex gap-2 flex-shrink-0">
                <button
                  onClick={() => approveMutation.mutate(item.id)}
                  disabled={approveMutation.isPending}
                  className="px-3 py-1.5 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:opacity-50"
                >
                  Approve
                </button>
                <button
                  onClick={() => rejectMutation.mutate(item.id)}
                  disabled={rejectMutation.isPending}
                  className="px-3 py-1.5 bg-red-100 text-red-700 text-xs rounded hover:bg-red-200 disabled:opacity-50"
                >
                  Reject
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
