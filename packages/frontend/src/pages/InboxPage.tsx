import { useQuery } from "@tanstack/react-query";
import { getEmails, getEmail } from "../lib/api";
import { useState } from "react";
import { FileText, Mail } from "lucide-react";

const CLASS_STYLES: Record<string, { bg: string; icon: string }> = {
  new_order: { bg: "bg-blue-100 text-blue-700", icon: "📦" },
  order_update: { bg: "bg-indigo-100 text-indigo-700", icon: "🔄" },
  customer_response: { bg: "bg-green-100 text-green-700", icon: "💬" },
  cancellation: { bg: "bg-red-100 text-red-700", icon: "❌" },
  other: { bg: "bg-gray-100 text-gray-600", icon: "📄" },
};

function SenderAvatar({ name }: { name: string }) {
  const initial = name?.charAt(0)?.toUpperCase() || "?";
  return (
    <div className="w-9 h-9 rounded-full bg-gradient-to-br from-slate-600 to-slate-700 flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
      {initial}
    </div>
  );
}

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
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Email Inbox</h1>
      <div className="flex gap-4 h-[calc(100vh-12rem)]">
        {/* Email List - Left Panel */}
        <div className="w-[35%] flex-shrink-0 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
          <div className="px-4 py-3 border-b border-gray-100 bg-gray-50/50">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">
              Messages ({data?.total_count ?? 0})
            </p>
          </div>
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <div className="animate-pulse p-3 space-y-2">
                {Array.from({ length: 8 }).map((_, i) => (
                  <div key={i} className="h-16 bg-gray-100 rounded-lg" />
                ))}
              </div>
            ) : data?.data.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-gray-400 px-6 text-center">
                <Mail className="w-10 h-10 mb-3 text-gray-300" />
                <p className="text-sm">No emails processed yet.</p>
                <p className="text-xs mt-1">Drop a .eml file in test-emails/inbox/ to get started.</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-50">
                {data?.data.map((email: Record<string, unknown>) => {
                  const isSelected = selectedEmailId === (email.id as string);
                  const isUnread = !(email.read as boolean);
                  return (
                    <div
                      key={email.id as string}
                      onClick={() => setSelectedEmailId(email.id as string)}
                      className={`px-4 py-3 cursor-pointer transition-all relative ${
                        isSelected
                          ? "bg-blue-50 border-l-2 border-l-blue-500"
                          : "hover:bg-gray-50 border-l-2 border-l-transparent"
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <SenderAvatar name={email.from_address as string} />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between mb-0.5">
                            <span className={`text-sm truncate max-w-[160px] ${isUnread ? "font-semibold text-gray-900" : "text-gray-700"}`}>
                              {(email.from_address as string)?.split("@")[0] || "Unknown"}
                            </span>
                            <span className="text-[11px] text-gray-400 flex-shrink-0 ml-2">
                              {email.received_at
                                ? new Date(email.received_at as string).toLocaleDateString(undefined, { month: "short", day: "numeric" })
                                : ""}
                            </span>
                          </div>
                          <p className={`text-sm truncate ${isUnread ? "font-medium text-gray-800" : "text-gray-600"}`}>
                            {(email.subject as string) || "(no subject)"}
                          </p>
                          <div className="flex items-center justify-between mt-1">
                            <p className="text-xs text-gray-400 truncate max-w-[180px]">
                              {(email.body_preview as string) || ""}
                            </p>
                            {isUnread && (
                              <span className="w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Email Detail - Right Panel */}
        <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden flex flex-col">
          {!selectedEmailId ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-400">
              <Mail className="w-12 h-12 mb-3 text-gray-300" />
              <p className="text-sm">Select an email to view its contents</p>
            </div>
          ) : !emailDetail ? (
            <div className="animate-pulse p-6 space-y-3">
              <div className="h-6 bg-gray-200 rounded w-3/4" />
              <div className="h-4 bg-gray-200 rounded w-1/2" />
              <div className="h-32 bg-gray-200 rounded" />
            </div>
          ) : (
            <div className="flex flex-col h-full overflow-hidden">
              {/* Email Header */}
              <div className="p-6 border-b border-gray-100 bg-gray-50/50 flex-shrink-0">
                <h2 className="text-lg font-semibold text-gray-900 mb-3">
                  {emailDetail.subject || "(no subject)"}
                </h2>
                <div className="bg-white rounded-lg border border-gray-200 p-4 space-y-1.5 text-sm">
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 w-14">From:</span>
                    <span className="font-medium text-gray-800">{emailDetail.from_address}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 w-14">To:</span>
                    <span className="text-gray-700">{emailDetail.to_address}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 w-14">Date:</span>
                    <span className="text-gray-700">
                      {emailDetail.received_at ? new Date(emailDetail.received_at).toLocaleString() : "—"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500 w-14">Type:</span>
                    {emailDetail.classification && (
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${
                          CLASS_STYLES[emailDetail.classification]?.bg || "bg-gray-100 text-gray-600"
                        }`}
                      >
                        <span>{CLASS_STYLES[emailDetail.classification]?.icon || "📄"}</span>
                        {emailDetail.classification.replace(/_/g, " ")}
                      </span>
                    )}
                    <span className="text-xs text-gray-400">
                      {emailDetail.classification_confidence != null
                        ? `${Number(emailDetail.classification_confidence).toFixed(1)}% confidence`
                        : ""}
                    </span>
                  </div>
                  {emailDetail.linked_order_id && (
                    <div className="flex items-center gap-2">
                      <span className="text-gray-500 w-14">Order:</span>
                      <a href={`/orders/${emailDetail.linked_order_id}`} className="text-blue-600 hover:text-blue-800 font-medium text-sm">
                        View Linked Order
                      </a>
                    </div>
                  )}
                </div>
              </div>

              {/* Attachments */}
              {emailDetail.attachments && emailDetail.attachments.length > 0 && (
                <div className="px-6 py-3 border-b border-gray-100 flex-shrink-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    {emailDetail.attachments.map((att: Record<string, unknown>) => (
                      <div
                        key={att.id as string}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-gray-100 rounded-lg text-sm text-gray-700 border border-gray-200"
                      >
                        <FileText className="w-3.5 h-3.5 text-gray-500" />
                        <span className="max-w-[150px] truncate">{att.file_name as string}</span>
                        <span className="text-[10px] text-gray-400 uppercase">{att.file_type as string}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Email Body */}
              <div className="flex-1 overflow-y-auto p-6">
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
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
