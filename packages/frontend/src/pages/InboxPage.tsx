import { useQuery } from "@tanstack/react-query";
import { getEmails, getEmail } from "../lib/api";
import { useState } from "react";

const CLASS_COLORS: Record<string, string> = {
  new_order: "bg-blue-100 text-blue-800",
  order_update: "bg-indigo-100 text-indigo-800",
  customer_response: "bg-green-100 text-green-800",
  cancellation: "bg-red-100 text-red-800",
  other: "bg-gray-100 text-gray-600",
};

export function InboxPage() {
  const [selectedEmailId, setSelectedEmailId] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["emails"],
    queryFn: () => getEmails({ limit: 50 }),
  });

  const { data: emailDetail } = useQuery({
    queryKey: ["email", selectedEmailId],
    queryFn: () => getEmail(selectedEmailId!),
    enabled: !!selectedEmailId,
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Email Inbox</h1>
      <div className="flex gap-4 h-[calc(100vh-12rem)]">
        {/* Email List */}
        <div className="w-1/3 overflow-y-auto">
          {isLoading ? (
            <div className="animate-pulse space-y-2">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="h-16 bg-gray-200 rounded" />
              ))}
            </div>
          ) : data?.data.length === 0 ? (
            <div className="text-center text-gray-400 py-12">
              No emails processed yet. Drop a .eml file in test-emails/inbox/ to get started.
            </div>
          ) : (
            <div className="space-y-1">
              {data?.data.map((email: any) => (
                <div
                  key={email.id}
                  onClick={() => setSelectedEmailId(email.id)}
                  className={`p-3 rounded-lg cursor-pointer border transition-colors ${
                    selectedEmailId === email.id
                      ? "bg-brand-50 border-brand-300"
                      : "bg-white border-gray-200 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900 truncate max-w-[180px]">
                      {email.from_address}
                    </span>
                    {email.classification && (
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${CLASS_COLORS[email.classification] || "bg-gray-100"}`}>
                        {email.classification.replace("_", " ")}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 truncate">{email.subject || "(no subject)"}</p>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-xs text-gray-400">
                      {email.received_at ? new Date(email.received_at).toLocaleString() : ""}
                    </span>
                    <span className="text-xs text-gray-400">
                      {email.classification_confidence != null ? `${Number(email.classification_confidence).toFixed(0)}%` : ""}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Email Detail */}
        <div className="flex-1 bg-white rounded-lg shadow-sm border overflow-y-auto">
          {!selectedEmailId ? (
            <div className="flex items-center justify-center h-full text-gray-400">
              Select an email to view its contents
            </div>
          ) : !emailDetail ? (
            <div className="animate-pulse p-6 space-y-3">
              <div className="h-6 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-1/2" />
              <div className="h-32 bg-gray-200 rounded" />
            </div>
          ) : (
            <div className="p-6">
              {/* Header */}
              <div className="border-b pb-4 mb-4">
                <h2 className="text-lg font-semibold text-gray-900">{emailDetail.subject || "(no subject)"}</h2>
                <div className="mt-2 space-y-1 text-sm text-gray-600">
                  <div><span className="font-medium">From:</span> {emailDetail.from_address}</div>
                  <div><span className="font-medium">To:</span> {emailDetail.to_address}</div>
                  <div><span className="font-medium">Date:</span> {emailDetail.received_at ? new Date(emailDetail.received_at).toLocaleString() : "—"}</div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">Classification:</span>
                    {emailDetail.classification && (
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${CLASS_COLORS[emailDetail.classification] || "bg-gray-100"}`}>
                        {emailDetail.classification.replace("_", " ")}
                      </span>
                    )}
                    <span className="text-gray-400">
                      ({emailDetail.classification_confidence != null ? `${Number(emailDetail.classification_confidence).toFixed(1)}% confidence` : "—"})
                    </span>
                  </div>
                  {emailDetail.linked_order_id && (
                    <div><span className="font-medium">Linked Order:</span> <a href={`/orders/${emailDetail.linked_order_id}`} className="text-brand-600 hover:underline">View Order</a></div>
                  )}
                </div>
              </div>

              {/* Attachments */}
              {emailDetail.attachments && emailDetail.attachments.length > 0 && (
                <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Attachments ({emailDetail.attachments.length})</h3>
                  <div className="space-y-1">
                    {emailDetail.attachments.map((att: any) => (
                      <div key={att.id} className="flex items-center gap-2 text-sm text-gray-600">
                        <span>📎</span>
                        <span>{att.file_name}</span>
                        <span className="text-xs text-gray-400">({att.file_type})</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Email Body */}
              <div className="prose prose-sm max-w-none">
                {emailDetail.body_html ? (
                  <div dangerouslySetInnerHTML={{ __html: emailDetail.body_html }} />
                ) : (
                  <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800 leading-relaxed">
                    {emailDetail.body_text || "No email body content"}
                  </pre>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
