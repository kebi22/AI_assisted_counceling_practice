import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "../types";
import MessageBubble from "./MessageBubble";

interface Props {
  messages: ChatMessage[];
  clientName: string;
  isLoading: boolean;
  error: string | null;
  onSend: (text: string) => void;
  onEndSession: () => void;
}

/** Text-mode chat window (sidebar + transcript layout lives in SimulationChatPage). */
export default function ChatWindow({
  messages,
  clientName,
  isLoading,
  error,
  onSend,
  onEndSession,
}: Props) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, isLoading]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || isLoading) return;
    setInput("");
    onSend(text);
  };

  return (
    <div className="flex h-[70vh] flex-col rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
      <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4" aria-label="Conversation history">
        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} clientName={clientName} />
        ))}
        {isLoading && (
          <p className="text-sm italic text-slate-500" role="status" aria-live="polite">
            {clientName} is responding...
          </p>
        )}
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>

      <div className="border-t border-slate-200 p-3">
        <label htmlFor="chat-input" className="mb-1 block text-xs font-medium text-slate-600">
          Your response
        </label>
        <div className="flex gap-2">
          <textarea
            id="chat-input"
            rows={2}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={`Respond to ${clientName}...`}
            className="flex-1 resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-navy-600 focus:outline-none focus:ring-1 focus:ring-navy-600"
          />
          <div className="flex flex-col gap-2">
            <button
              type="button"
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="rounded-lg bg-navy-700 px-4 py-2 text-sm font-medium text-white hover:bg-navy-600 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              Send
            </button>
            <button
              type="button"
              onClick={onEndSession}
              disabled={isLoading}
              className="rounded-lg border border-navy-700 px-4 py-2 text-sm font-medium text-navy-700 hover:bg-navy-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              End Session &amp; Get Feedback
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
