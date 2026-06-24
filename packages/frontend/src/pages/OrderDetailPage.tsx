import { useQuery } from "@tanstack/react-query";
import { useParams, Link } from "react-router-dom";
import { getOrder } from "../lib/api";

function ConfidenceBadge({ score }: { score: number | null }) {
  if (score == null) return <span className="text-gray-400">—</span>;
  const color = score >= 90 ? "bg-green-100 text-green-800" : score >= 70 ? "bg-yellow-100 text-yellow-800" : "bg-red-100 text-red-800";
  return <span className={`px-2 py-0.5 rounded text-xs font-medium ${color}`}>{score.toFixed(1)}%</span>;
}

function FieldRow({ label, value, confidence }: { label: string; value: any; confidence?: number }) {
  return (
    <div className="flex items-center py-2 border-b border-gray-100 last:border-0">
      <span className="w-48 text-sm text-gray-500 flex-shrink-0">{label}</span>
      <span className="flex-1 text-sm text-gray-900">{value ?? <span className="text-gray-300 italic">Not provided</span>}</span>
      {confidence !== undefined && <ConfidenceBadge score={confidence} />}
    </div>
  );
}

export function OrderDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data: order, isLoading } = useQuery({
    queryKey: ["order", id],
    queryFn: () => getOrder(id!),
    enabled: !!id,
  });

  if (isLoading) return <div className="animate-pulse h-96 bg-gray-200 rounded-lg" />;
  if (!order) return <div className="text-red-600">Order not found</div>;

  const scores = order.field_confidence_scores || {};

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link to="/orders" className="text-brand-600 hover:underline text-sm">&larr; Orders</Link>
        <h1 className="text-2xl font-bold">{order.order_number}</h1>
        <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 capitalize">
          {order.status?.replace("_", " ")}
        </span>
        <ConfidenceBadge score={order.overall_confidence_score} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Customer Info */}
        <div className="bg-white rounded-lg shadow-sm border p-5">
          <h2 className="font-semibold text-gray-800 mb-3">Customer Information</h2>
          <FieldRow label="Customer Name" value={order.customer_name} confidence={scores.customer_name} />
          <FieldRow label="Contact Name" value={order.contact_name} confidence={scores.contact_name} />
          <FieldRow label="Contact Email" value={order.contact_email} confidence={scores.contact_email} />
          <FieldRow label="Contact Phone" value={order.contact_phone} confidence={scores.contact_phone} />
        </div>

        {/* Shipment Info */}
        <div className="bg-white rounded-lg shadow-sm border p-5">
          <h2 className="font-semibold text-gray-800 mb-3">Shipment Details</h2>
          <FieldRow label="Commodity" value={order.commodity} confidence={scores.commodity} />
          <FieldRow label="Freight Type" value={order.freight_type} confidence={scores.freight_type} />
          <FieldRow label="Equipment" value={order.equipment_type} confidence={scores.equipment_type} />
          <FieldRow label="Weight" value={order.total_weight ? `${order.total_weight} ${order.weight_unit || ""}` : null} confidence={scores.total_weight} />
          <FieldRow label="Pallets" value={order.num_pallets} />
          <FieldRow label="Hazmat" value={order.hazmat_indicator ? "Yes" : "No"} />
        </div>

        {/* Pickup */}
        <div className="bg-white rounded-lg shadow-sm border p-5">
          <h2 className="font-semibold text-gray-800 mb-3">Pickup</h2>
          <FieldRow label="Location" value={order.pickup_location_name} confidence={scores.pickup_location_name} />
          <FieldRow label="Date" value={order.pickup_date} confidence={scores.pickup_date} />
          <FieldRow label="Address" value={order.pickup_address ? `${order.pickup_address.line1}, ${order.pickup_address.city}, ${order.pickup_address.state}` : null} />
          <FieldRow label="Instructions" value={order.pickup_instructions} />
        </div>

        {/* Delivery */}
        <div className="bg-white rounded-lg shadow-sm border p-5">
          <h2 className="font-semibold text-gray-800 mb-3">Delivery</h2>
          <FieldRow label="Location" value={order.delivery_location_name} confidence={scores.delivery_location_name} />
          <FieldRow label="Date" value={order.delivery_date} confidence={scores.delivery_date} />
          <FieldRow label="Address" value={order.delivery_address ? `${order.delivery_address.line1}, ${order.delivery_address.city}, ${order.delivery_address.state}` : null} />
          <FieldRow label="Instructions" value={order.delivery_instructions} />
        </div>
      </div>
    </div>
  );
}
