import type { ChatMessage } from "../types";

interface Props {
  message: ChatMessage;
  clientName?: string;
  studentLabel?: string;
}

export default function MessageBubble({
  message,
  clientName = "Jordan",
  studentLabel = "You",
}: Props) {
  const isClient = message.speaker === "client";
  return (
    <div className={`flex ${isClient ? "justify-start" : "justify-end"}`}>
      <div className="max-w-[80%]">
        <p className={`mb-1 text-xs font-medium text-slate-500 ${isClient ? "" : "text-right"}`}>
          {isClient ? clientName : studentLabel}
        </p>
        <div
          className={
            isClient
              ? "rounded-2xl rounded-tl-sm bg-navy-50 px-4 py-2.5 text-sm text-slate-800 ring-1 ring-navy-100"
              : "rounded-2xl rounded-tr-sm bg-emerald-50 px-4 py-2.5 text-sm text-slate-800 ring-1 ring-emerald-100"
          }
        >
          {message.content}
        </div>
      </div>
    </div>
  );
}
