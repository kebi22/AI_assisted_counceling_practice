import { useEffect, useRef } from "react";
import type { ChatMessage } from "../types";
import MessageBubble from "./MessageBubble";

interface Props {
  messages: ChatMessage[];
  clientName: string;
  isLoading: boolean;
  /** When true, auto-scroll to the latest message. */
  autoScroll?: boolean;
  className?: string;
}

/** Scrollable transcript panel shared by voice and video session layouts. */
export default function SessionTranscript({
  messages,
  clientName,
  isLoading,
  autoScroll = true,
  className = "",
}: Props) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!autoScroll) return;
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isLoading, autoScroll]);

  return (
    <div className={`flex flex-col ${className}`}>
      <div className="border-b border-slate-200 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-700">Live transcript</h2>
        <p className="text-xs text-slate-500">Spoken turns appear here after transcription</p>
      </div>
      <div
        ref={scrollRef}
        className="flex-1 space-y-3 overflow-y-auto p-4"
        aria-label="Conversation transcript"
      >
        {messages.length === 0 && (
          <p className="text-sm italic text-slate-400">The conversation will appear here...</p>
        )}
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} clientName={clientName} />
        ))}
        {isLoading && (
          <p className="text-sm italic text-slate-500" role="status" aria-live="polite">
            {clientName} is responding...
          </p>
        )}
      </div>
    </div>
  );
}
