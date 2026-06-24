import { useQuery } from "@tanstack/react-query";
import { useSearchParams, Link } from "react-router-dom";
import { getOrders } from "../lib/api";

const STATUS_COLORS: Record<string, string> = {
  order_created: "bg-green-100 text-green-800",
  extracted: "bg-blue-100 text-blue-800",
  pending_review: "bg-yellow-100 text-yellow-800",
  awaiting_customer: "bg-orange-100 text-orange-800",
  validated: "bg-indigo-100 text-indigo-800",
  failed: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-600",
};

export function OrdersPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = parseInt(searchParams.get("page") || "1");
  const status = searchParams.get("status") || undefined;

  const { data, isLoading } = useQuery({
    queryKey: ["orders", page, status],
    queryFn: () => getOrders({ page, limit: 20, ...(status ? { status } : {}) }),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Orders</h1>
        <div className="flex gap-2">
          {["all", "extracted", "pending_review", "awaiting_customer", "order_created", "failed"].map((s) => (
            <button
              key={s}
              onClick={() => {
                if (s === "all") searchParams.delete("status");
                else searchParams.set("status", s);
                searchParams.set("page", "1");
                setSearchParams(searchParams);
              }}
              className={`px-3 py-1 text-xs rounded-full border ${
                (s === "all" && !status) || status === s
                  ? "bg-brand-600 text-white border-brand-600"
                  : "bg-white text-gray-600 border-gray-300 hover:border-brand-400"
              }`}
            >
              {s === "all" ? "All" : s.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="animate-pulse space-y-3">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-12 bg-gray-200 rounded" />
          ))}
        </div>
      ) : (
        <>
          <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Order #</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Customer</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Pickup Date</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Equipment</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {data?.data.map((order: any) => (
                  <tr key={order.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <Link to={`/orders/${order.id}`} className="text-brand-600 hover:underline font-medium">
                        {order.order_number}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-700">{order.customer_name || "—"}</td>
                    <td className="px-4 py-3 text-gray-700">{order.pickup_date || "—"}</td>
                    <td className="px-4 py-3 text-gray-700 capitalize">{order.equipment_type?.replace("_", " ") || "—"}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_COLORS[order.status] || "bg-gray-100"}`}>
                        {order.status?.replace("_", " ")}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {order.overall_confidence_score != null ? (
                        <span className={`font-medium ${
                          order.overall_confidence_score >= 95 ? "text-green-600" :
                          order.overall_confidence_score >= 80 ? "text-yellow-600" : "text-red-600"
                        }`}>
                          {order.overall_confidence_score.toFixed(1)}%
                        </span>
                      ) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data && data.total_pages > 1 && (
            <div className="flex justify-center gap-2 mt-4">
              {Array.from({ length: Math.min(data.total_pages, 10) }).map((_, i) => (
                <button
                  key={i}
                  onClick={() => { searchParams.set("page", String(i + 1)); setSearchParams(searchParams); }}
                  className={`px-3 py-1 rounded text-sm ${page === i + 1 ? "bg-brand-600 text-white" : "bg-white border hover:bg-gray-50"}`}
                >
                  {i + 1}
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
