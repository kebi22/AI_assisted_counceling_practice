import { useState } from "react";
import type { ChatMessage } from "../types";
import { MIN_STUDENT_MESSAGES } from "../types";
import ClientAvatar from "./ClientAvatar";
import JoinCallOverlay from "./JoinCallOverlay";
import SessionTranscript from "./SessionTranscript";
import VoiceRecorder from "./VoiceRecorder";
import { useClientAudioPlayback } from "../hooks/useClientAudioPlayback";

interface Props {
  messages: ChatMessage[];
  clientName: string;
  scenarioTitle: string;
  studentCount: number;
  studentGoal?: string;
  isLoading: boolean;
  error: string | null;
  endWarning: string | null;
  clientAudioUrl: string | null;
  onSend: (text: string) => void;
  onSendAudio: (audio: Blob) => void;
  onEndSession: () => void;
}

/**
 * Voice-call layout: client avatar on a dark stage, transcript sidebar,
 * push-to-talk dock with optional text fallback.
 */
export default function VoiceSessionView({
  messages,
  clientName,
  scenarioTitle,
  studentCount,
  studentGoal,
  isLoading,
  error,
  endWarning,
  clientAudioUrl,
  onSend,
  onSendAudio,
  onEndSession,
}: Props) {
  const [showTextInput, setShowTextInput] = useState(false);
  const [input, setInput] = useState("");
  const { audioRef, callJoined, joinCall } = useClientAudioPlayback(clientAudioUrl);

  const openingReady = Boolean(clientAudioUrl) || messages.some((m) => m.speaker === "client");
  const progressPct = Math.min(100, (studentCount / MIN_STUDENT_MESSAGES) * 100);
  const canEnd = studentCount >= MIN_STUDENT_MESSAGES;

  const handleSend = () => {
    const text = input.trim();
    if (!text || isLoading) return;
    setInput("");
    onSend(text);
  };

  return (
    <div className="flex min-h-[78vh] flex-col overflow-hidden rounded-2xl bg-white shadow-lg ring-1 ring-slate-200">
      {/* Header */}
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-teal-600">Voice call</p>
          <h1 className="truncate text-lg font-semibold text-navy-800">{scenarioTitle}</h1>
          <p className="text-sm text-slate-500">Speaking with {clientName}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="hidden text-right sm:block">
            <p className="text-xs text-slate-500">Progress</p>
            <p className="text-sm font-medium text-slate-700">
              {studentCount}/{MIN_STUDENT_MESSAGES} responses
            </p>
          </div>
          <div className="h-2 w-24 overflow-hidden rounded-full bg-slate-200" aria-hidden="true">
            <div className="h-full rounded-full bg-teal-500 transition-all" style={{ width: `${progressPct}%` }} />
          </div>
        </div>
      </header>

      {endWarning && (
        <p className="mx-5 mt-3 rounded-lg bg-amber-50 px-4 py-2 text-sm text-amber-800 ring-1 ring-amber-200" role="alert">
          {endWarning}
        </p>
      )}
      {error && (
        <p className="mx-5 mt-3 rounded-lg bg-red-50 px-4 py-2 text-sm text-red-700 ring-1 ring-red-200">{error}</p>
      )}

      {/* Main: stage + transcript */}
      <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
        <section className="relative flex flex-1 flex-col items-center justify-center bg-gradient-to-b from-navy-900 via-navy-950 to-slate-950 px-6 py-10">
          {openingReady && !callJoined && (
            <JoinCallOverlay clientName={clientName} onJoin={joinCall} />
          )}
          <ClientAvatar
            clientName={clientName}
            audioRef={audioRef}
            audioUrl={clientAudioUrl}
            variant="hero"
          />
          <audio
            ref={audioRef}
            src={clientAudioUrl ?? undefined}
            preload="auto"
            className="sr-only"
            aria-hidden="true"
          />
          {studentGoal && (
            <p className="mt-8 max-w-md text-center text-sm leading-relaxed text-slate-400">{studentGoal}</p>
          )}
        </section>

        <aside className="flex w-full flex-col border-t border-slate-200 bg-slate-50 lg:w-[340px] lg:border-l lg:border-t-0 xl:w-[380px]">
          <SessionTranscript
            messages={messages}
            clientName={clientName}
            isLoading={isLoading}
            className="min-h-[240px] flex-1 lg:min-h-0"
          />
        </aside>
      </div>

      {/* Control dock */}
      <footer className="border-t border-slate-200 bg-white px-5 py-4">
        <div className="flex flex-col items-center gap-4">
          <VoiceRecorder onRecorded={onSendAudio} disabled={isLoading} />
          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => setShowTextInput((v) => !v)}
              className="rounded-full border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
            >
              {showTextInput ? "Hide keyboard" : "Type instead"}
            </button>
            <button
              type="button"
              onClick={onEndSession}
              disabled={isLoading}
              className={`rounded-full px-5 py-2 text-sm font-medium transition ${
                canEnd
                  ? "bg-navy-700 text-white hover:bg-navy-600"
                  : "border border-slate-300 text-slate-500 hover:bg-slate-50"
              } disabled:opacity-50`}
            >
              End &amp; get feedback
            </button>
          </div>
        </div>

        {showTextInput && (
          <div className="mx-auto mt-4 flex max-w-xl gap-2">
            <textarea
              rows={2}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder={`Type a response to ${clientName}...`}
              className="flex-1 resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-navy-600 focus:outline-none focus:ring-1 focus:ring-navy-600"
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="self-end rounded-lg bg-navy-700 px-4 py-2 text-sm font-medium text-white hover:bg-navy-600 disabled:bg-slate-300"
            >
              Send
            </button>
          </div>
        )}
      </footer>
    </div>
  );
}
