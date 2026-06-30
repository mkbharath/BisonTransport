import { useQuery } from "@tanstack/react-query";
import { getDashboard, getStpTrend } from "../lib/api";
import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { Plus } from "lucide-react";
import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";

export function DashboardPage() {
  const { user } = useAuth();

  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
    refetchInterval: 30_000,
  });

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="grid grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-20 bg-gray-200 rounded" />)}
        </div>
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-48 bg-gray-200 rounded" />)}
        </div>
      </div>
    );
  }

  if (error) return <div className="bg-red-50 text-red-700 p-4 rounded text-sm">Dashboard load failed</div>;
  if (!data) return null;

  const total = data.total_orders || 1;
  const completedPct = Math.round((data.completed / total) * 100);
  const awaitingPct = Math.round((data.awaiting_customer / total) * 100);
  const hitlPct = Math.round((data.hitl_queue_depth / total) * 100);
  const failedPct = Math.round((data.failed / total) * 100);
  const pendingPct = 100 - completedPct - awaitingPct - hitlPct - failedPct;

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Title Row */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-bold text-gray-900">Order Intelligence Dashboard</h1>
          <p className="text-xs text-gray-500">Real-time pipeline metrics • Auto-refreshes every 30s</p>
        </div>
        <Link to="/orders/new" className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-amber-500 to-amber-600 rounded-lg hover:from-amber-600 hover:to-amber-700 shadow-sm transition-all">
          <Plus className="w-4 h-4" />
          New Order
        </Link>
      </div>

      {/* KPI Row — 5 tiles like Power BI scorecard */}
      <div className="grid grid-cols-5 gap-4">
        <KPITile label="TOTAL ORDERS" value={data.total_orders} color="#1e40af" bgColor="bg-blue-50" />
        <KPITile label="COMPLETED" value={data.completed} color="#047857" bgColor="bg-emerald-50" to="/orders?status=order_created" />
        <KPITile label="STP RATE" value={`${data.stp_rate}%`} color="#b45309" bgColor="bg-amber-50" />
        <KPITile label="AVG E2E TIME" value={`${data.avg_e2e_time}m`} color="#7e22ce" bgColor="bg-purple-50" />
        <KPITile label="ACCURACY" value={`${data.extraction_accuracy}%`} color="#0e7490" bgColor="bg-cyan-50" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-12 gap-3">
        {/* Donut Chart — Order Status Distribution */}
        <div className="col-span-5 bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-[11px] font-bold text-gray-700 uppercase tracking-wider mb-4">Order Status Distribution</h3>
          <div className="flex items-center justify-center gap-10">
            <DonutChart
              segments={[
                { value: data.completed, color: "#10b981", label: "Completed" },
                { value: data.awaiting_customer, color: "#f97316", label: "Awaiting" },
                { value: data.hitl_queue_depth, color: "#8b5cf6", label: "In Review" },
                { value: data.pending, color: "#f59e0b", label: "Pending" },
                { value: data.failed, color: "#ef4444", label: "Failed" },
              ]}
              total={data.total_orders}
            />
            <div className="space-y-3 text-sm">
              <Legend color="#10b981" label="Completed" value={data.completed} />
              <Legend color="#f97316" label="Awaiting Customer" value={data.awaiting_customer} />
              <Legend color="#8b5cf6" label="In Review (HITL)" value={data.hitl_queue_depth} />
              <Legend color="#f59e0b" label="Pending" value={data.pending} />
              <Legend color="#ef4444" label="Failed" value={data.failed} />
            </div>
          </div>
        </div>

        {/* Horizontal Bar — Pipeline Breakdown */}
        <div className="col-span-4 bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-[11px] font-bold text-gray-700 uppercase tracking-wider mb-4">Pipeline Breakdown</h3>
          <div className="space-y-5">
            <HBar label="Completed" value={data.completed} max={total} color="#10b981" to="/orders?status=order_created" />
            <HBar label="Awaiting Customer" value={data.awaiting_customer} max={total} color="#f97316" to="/orders?status=awaiting_customer" />
            <HBar label="HITL Queue" value={data.hitl_queue_depth} max={total} color="#8b5cf6" to="/queue" />
            <HBar label="Auto-Processed" value={data.auto_processed} max={total} color="#06b6d4" />
            <HBar label="Pending" value={data.pending} max={total} color="#f59e0b" to="/orders?status=extracted" />
            <HBar label="Failed" value={data.failed} max={total} color="#ef4444" to="/orders?status=failed" />
          </div>
        </div>

        {/* Stacked Bar — STP vs HITL */}
        <div className="col-span-3 bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-[11px] font-bold text-gray-700 uppercase tracking-wider mb-4">Processing Mode</h3>
          {/* Stacked progress bar */}
          <div className="h-5 rounded-full overflow-hidden flex bg-gray-100 mb-3">
            {data.auto_processed > 0 && (
              <div style={{ width: `${(data.auto_processed / total) * 100}%` }} className="bg-emerald-500 transition-all duration-500" />
            )}
            {data.hitl_queue_depth > 0 && (
              <div style={{ width: `${(data.hitl_queue_depth / total) * 100}%` }} className="bg-indigo-500 transition-all duration-500" />
            )}
            {data.awaiting_customer > 0 && (
              <div style={{ width: `${(data.awaiting_customer / total) * 100}%` }} className="bg-orange-400 transition-all duration-500" />
            )}
          </div>
          <div className="space-y-2 text-xs">
            <Legend color="#059669" label="Auto (STP)" value={data.auto_processed} />
            <Legend color="#6366f1" label="Human Review" value={data.hitl_queue_depth} />
            <Legend color="#fb923c" label="Customer Reply" value={data.awaiting_customer} />
          </div>

          {/* Gauge */}
          <div className="mt-4 pt-3 border-t border-gray-100">
            <p className="text-[11px] text-gray-700 uppercase tracking-wider font-semibold mb-2">STP Target: 80%</p>
            <div className="h-3 rounded-full bg-gray-100 overflow-hidden relative">
              <div
                className="h-full rounded-full bg-gradient-to-r from-amber-400 to-emerald-500 transition-all duration-700"
                style={{ width: `${Math.min(data.stp_rate, 100)}%` }}
              />
              {/* Target marker */}
              <div className="absolute top-0 bottom-0 w-0.5 bg-gray-800" style={{ left: "80%" }} />
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-[10px] text-gray-400">0%</span>
              <span className="text-[10px] font-bold text-gray-700">{data.stp_rate}%</span>
              <span className="text-[10px] text-gray-400">100%</span>
            </div>
          </div>
        </div>
      </div>

      {/* STP Trend Chart */}
      <STPTrendChart />

      {/* Bottom Row — Metrics Table */}
      <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-4 py-2.5 text-left font-bold text-gray-700 uppercase tracking-wider">Metric</th>
              <th className="px-4 py-2.5 text-right font-bold text-gray-700 uppercase tracking-wider">Value</th>
              <th className="px-4 py-2.5 text-left font-bold text-gray-700 uppercase tracking-wider">Target</th>
              <th className="px-4 py-2.5 text-left font-bold text-gray-700 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            <MetricRow metric="STP Rate" value={`${data.stp_rate}%`} target="≥ 80%" met={data.stp_rate >= 80} />
            <MetricRow metric="Extraction Accuracy" value={`${data.extraction_accuracy}%`} target="≥ 90%" met={data.extraction_accuracy >= 90} />
            <MetricRow metric="Avg E2E Time" value={`${data.avg_e2e_time} min`} target="< 5 min" met={data.avg_e2e_time < 5} />
            <MetricRow metric="Failed Orders" value={String(data.failed)} target="0" met={data.failed === 0} />
            <MetricRow metric="HITL Queue Depth" value={String(data.hitl_queue_depth)} target="< 5" met={data.hitl_queue_depth < 5} />
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* --- Components --- */

function STPTrendChart() {
  const [days, setDays] = useState(7);

  const { data, isLoading } = useQuery({
    queryKey: ["stp-trend", days],
    queryFn: () => getStpTrend(days),
  });

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-[11px] font-bold text-gray-700 uppercase tracking-wider">STP Rate Trend</h3>
        <div className="flex items-center gap-1">
          {[7, 14, 30].map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={`px-2.5 py-1 text-[11px] font-medium rounded-md transition-all ${
                days === d
                  ? "bg-[#0f1b2d] text-white"
                  : "text-gray-500 hover:bg-gray-100"
              }`}
            >
              {d}d
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="h-[200px] bg-gray-50 rounded-lg animate-pulse" />
      ) : (
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data?.data || []} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="date"
              tick={{ fontSize: 11, fill: "#94a3b8" }}
              tickFormatter={(val: string) => {
                const d = new Date(val);
                return `${d.getMonth() + 1}/${d.getDate()}`;
              }}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontSize: 11, fill: "#94a3b8" }}
              tickFormatter={(val: number) => `${val}%`}
            />
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e2e8f0" }}
              formatter={(value: number) => [`${value}%`, "STP Rate"]}
              labelFormatter={(label: string) => new Date(label).toLocaleDateString()}
            />
            <ReferenceLine y={80} stroke="#9ca3af" strokeDasharray="4 4" label={{ value: "Target 80%", position: "right", fontSize: 10, fill: "#9ca3af" }} />
            <Line
              type="monotone"
              dataKey="stp_rate"
              stroke="#f59e0b"
              strokeWidth={2.5}
              dot={{ r: 4, fill: "#f59e0b", stroke: "#fff", strokeWidth: 2 }}
              activeDot={{ r: 6, fill: "#f59e0b" }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

function KPITile({ label, value, color, bgColor, to }: { label: string; value: string | number; color: string; bgColor: string; to?: string }) {
  const content = (
    <div className={`${bgColor} border border-gray-200 rounded-xl px-5 py-5 hover:shadow-lg transition-shadow`}>
      <p className="text-[11px] font-bold text-gray-700 uppercase tracking-wider mb-2">{label}</p>
      <p className="text-3xl font-black" style={{ color }}>{value}</p>
    </div>
  );
  if (to) return <Link to={to}>{content}</Link>;
  return content;
}

function DonutChart({ segments, total }: { segments: { value: number; color: string; label: string }[]; total: number }) {
  const size = 240;
  const strokeWidth = 36;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  let cumulativeOffset = 0;

  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        {segments.map((seg, i) => {
          const pct = total > 0 ? seg.value / total : 0;
          const dashLength = pct * circumference;
          const offset = cumulativeOffset;
          cumulativeOffset += dashLength;
          return (
            <circle
              key={i}
              cx={size / 2}
              cy={size / 2}
              r={radius}
              fill="none"
              stroke={seg.color}
              strokeWidth={strokeWidth}
              strokeDasharray={`${dashLength} ${circumference - dashLength}`}
              strokeDashoffset={-offset}
              className="transition-all duration-500"
            />
          );
        })}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-4xl font-black text-gray-900">{total}</span>
        <span className="text-[11px] text-gray-500 uppercase font-medium">Total</span>
      </div>
    </div>
  );
}

function Legend({ color, label, value }: { color: string; label: string; value: number }) {
  return (
    <div className="flex items-center gap-3">
      <div className="w-3 h-3 rounded flex-shrink-0" style={{ backgroundColor: color }} />
      <span className="text-gray-700 flex-1 text-[13px]">{label}</span>
      <span className="font-bold text-gray-900 text-[13px]">{value}</span>
    </div>
  );
}

function HBar({ label, value, max, color, to }: { label: string; value: number; max: number; color: string; to?: string }) {
  const pct = max > 0 ? (value / max) * 100 : 0;
  const content = (
    <div className="group py-1">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[13px] text-gray-700 font-medium">{label}</span>
        <span className="text-[13px] font-bold text-gray-900">{value}</span>
      </div>
      <div className="h-5 bg-gray-100 rounded-md overflow-hidden">
        <div
          className="h-full rounded-md transition-all duration-500 group-hover:opacity-80"
          style={{ width: `${Math.max(pct, 1)}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
  if (to) return <Link to={to}>{content}</Link>;
  return content;
}

function MetricRow({ metric, value, target, met }: { metric: string; value: string; target: string; met: boolean }) {
  return (
    <tr className="hover:bg-gray-50">
      <td className="px-4 py-2.5 text-gray-700 font-medium">{metric}</td>
      <td className="px-4 py-2.5 text-right font-bold text-gray-900">{value}</td>
      <td className="px-4 py-2.5 text-gray-500">{target}</td>
      <td className="px-4 py-2.5">
        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold ${met ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${met ? "bg-emerald-500" : "bg-red-500"}`} />
          {met ? "ON TARGET" : "BELOW"}
        </span>
      </td>
    </tr>
  );
}
