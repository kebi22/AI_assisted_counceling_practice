import type { ChatMessage } from "../types";
import MessageBubble from "./MessageBubble";

interface Props {
  messages: ChatMessage[];
  clientName?: string;
}

export default function TranscriptViewer({ messages, clientName = "Jordan" }: Props) {
  return (
    <div className="max-h-[60vh] space-y-4 overflow-y-auto rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      {messages.map((m) => (
        <MessageBubble key={m.id} message={m} clientName={clientName} studentLabel="Student" />
      ))}
    </div>
  );
}
