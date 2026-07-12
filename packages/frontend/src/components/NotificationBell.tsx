import { useState, useEffect, useRef } from "react";
import { Bell } from "lucide-react";

interface Notification {
  id: string;
  order_number: string;
  customer_name: string;
  event_type: string;
  new_status: string;
  triggered_by: string;
  created_at: string;
}

const EVENT_LABELS: Record<string, string> = {
  "order_created": "Order Created",
  "validation_complete": "Validation Complete",
  "order.approved": "Order Approved",
  "order.rejected": "Order Rejected",
  "missing_info_sent": "Missing Info Sent",
};

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function NotificationBell() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [open, setOpen] = useState(false);
  const [lastSeen, setLastSeen] = useState<string>(localStorage.getItem("lastNotifSeen") || "");
  const ref = useRef<HTMLDivElement>(null);

  // Poll for notifications every 15 seconds
  useEffect(() => {
    const fetchNotifs = async () => {
      try {
        const token = localStorage.getItem("token") || sessionStorage.getItem("token");
        if (!token) return;
        const res = await fetch("/api/v1/admin/notifications?limit=10", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setNotifications(data.data || []);
        }
      } catch { /* ignore */ }
    };
    fetchNotifs();
    const interval = setInterval(fetchNotifs, 15000);
    return () => clearInterval(interval);
  }, []);

  // Close on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const unreadCount = notifications.filter(n => n.created_at > lastSeen).length;

  const handleOpen = () => {
    setOpen(!open);
    if (!open && notifications.length > 0) {
      const latest = notifications[0]?.created_at || "";
      setLastSeen(latest);
      localStorage.setItem("lastNotifSeen", latest);
    }
  };

  return (
    <div className="relative" ref={ref}>
      <button onClick={handleOpen} className="relative p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 transition-colors">
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-12 w-[360px] bg-white rounded-xl shadow-2xl border border-gray-100 z-50 overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
            <h3 className="text-sm font-bold text-gray-800">Notifications</h3>
            <span className="text-[10px] text-gray-400">{notifications.length} recent</span>
          </div>
          <div className="max-h-[400px] overflow-y-auto divide-y divide-gray-50">
            {notifications.length === 0 ? (
              <p className="px-4 py-8 text-center text-sm text-gray-400">No notifications yet</p>
            ) : (
              notifications.map((n) => (
                <a key={n.id} href={`/orders/${n.order_id}`} className="block px-4 py-3 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start gap-3">
                    <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${n.created_at > lastSeen ? "bg-teal-500" : "bg-gray-200"}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-[13px] font-medium text-gray-800 truncate">
                        {n.order_number} — {EVENT_LABELS[n.event_type] || n.event_type}
                      </p>
                      <p className="text-[11px] text-gray-500 truncate">{n.customer_name || "Unknown"}</p>
                      <p className="text-[10px] text-gray-400 mt-0.5">{timeAgo(n.created_at)}</p>
                    </div>
                  </div>
                </a>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
