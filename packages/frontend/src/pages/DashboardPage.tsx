import { useQuery } from "@tanstack/react-query";
import { getDashboard } from "../lib/api";
import { Link } from "react-router-dom";

function MetricCard({ label, value, color, to }: { label: string; value: string | number; color?: string; to?: string }) {
  const content = (
    <div className={`bg-white rounded-lg shadow-sm border p-5 hover:shadow-md transition-shadow ${to ? "cursor-pointer" : ""}`}>
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color || "text-gray-900"}`}>{value}</p>
    </div>
  );
  if (to) return <Link to={to}>{content}</Link>;
  return content;
}

export function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
    refetchInterval: 30_000,
  });

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-8 bg-gray-200 rounded w-48" />
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="h-24 bg-gray-200 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return <div className="text-red-600">Failed to load dashboard: {(error as Error).message}</div>;
  }

  if (!data) return null;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        <MetricCard label="Total Orders" value={data.total_orders} to="/orders" />
        <MetricCard label="Pending" value={data.pending} color="text-yellow-600" to="/orders?status=extracted" />
        <MetricCard label="Awaiting Customer" value={data.awaiting_customer} color="text-orange-600" to="/orders?status=awaiting_customer" />
        <MetricCard label="Auto-Processed (STP)" value={data.auto_processed} color="text-green-600" />
        <MetricCard label="STP Rate" value={`${data.stp_rate}%`} color="text-green-700" />
        <MetricCard label="HITL Queue" value={data.hitl_queue_depth} color="text-blue-600" to="/queue" />
        <MetricCard label="Completed" value={data.completed} color="text-green-600" to="/orders?status=order_created" />
        <MetricCard label="Failed" value={data.failed} color="text-red-600" to="/orders?status=failed" />
        <MetricCard label="Avg E2E Time" value={`${data.avg_e2e_time} min`} />
        <MetricCard label="Extraction Accuracy" value={`${data.extraction_accuracy}%`} />
      </div>
    </div>
  );
}
