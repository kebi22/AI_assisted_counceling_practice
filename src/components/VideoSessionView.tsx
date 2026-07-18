import { useState } from "react";
import type { ChatMessage, NonverbalSummary } from "../types";
import { MIN_STUDENT_MESSAGES } from "../types";
import ClientAvatar from "./ClientAvatar";
import JoinCallOverlay from "./JoinCallOverlay";
import SessionTranscript from "./SessionTranscript";
import VoiceRecorder from "./VoiceRecorder";
import WebcamMonitor from "./WebcamMonitor";
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
  onNonverbalSummary: (summary: NonverbalSummary) => void;
}

/**
 * Video-call layout: full-screen dark stage with the client avatar as the
 * main participant, student webcam as a PiP tile, and a slide-over transcript.
 */
export default function VideoSessionView({
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
  onNonverbalSummary,
}: Props) {
  const [showTranscript, setShowTranscript] = useState(true);
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
    <div className="flex min-h-[82vh] flex-col overflow-hidden rounded-2xl bg-slate-950 shadow-lg ring-1 ring-slate-800">
      {/* Top bar — floats over the stage */}
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 bg-slate-900/90 px-5 py-3 backdrop-blur-sm">
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wide text-teal-400">Video session</p>
          <h1 className="truncate text-base font-semibold text-white sm:text-lg">{scenarioTitle}</h1>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          <span className="hidden rounded-full bg-white/10 px-3 py-1 text-xs text-slate-300 sm:inline">
            {clientName}
          </span>
          <div className="flex items-center gap-2">
            <div className="h-1.5 w-16 overflow-hidden rounded-full bg-white/10 sm:w-24" aria-hidden="true">
              <div className="h-full rounded-full bg-teal-500 transition-all" style={{ width: `${progressPct}%` }} />
            </div>
            <span className="text-xs text-slate-400">{studentCount}/{MIN_STUDENT_MESSAGES}</span>
          </div>
        </div>
      </header>

      {(endWarning || error) && (
        <div className="space-y-2 px-5 py-2">
          {endWarning && (
            <p className="rounded-lg bg-amber-500/20 px-3 py-2 text-sm text-amber-200" role="alert">
              {endWarning}
            </p>
          )}
          {error && (
            <p className="rounded-lg bg-red-500/20 px-3 py-2 text-sm text-red-200">{error}</p>
          )}
        </div>
      )}

      {/* Stage + optional transcript overlay */}
      <div className="relative flex min-h-0 flex-1">
        {/* Main stage */}
        <section className="relative flex flex-1 flex-col items-center justify-center px-4 py-8 sm:px-8">
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
            <p className="mt-6 max-w-lg text-center text-sm leading-relaxed text-slate-400">{studentGoal}</p>
          )}

          {/* Student PiP — bottom-right of stage, not in sidebar */}
          <div className="absolute bottom-4 right-4 w-36 sm:bottom-6 sm:right-6 sm:w-48 lg:w-56">
            <WebcamMonitor variant="pip" onSummaryChange={onNonverbalSummary} />
          </div>
        </section>

        {/* Transcript slide-over (desktop: side panel; mobile: full overlay) */}
        {showTranscript && (
          <aside className="absolute inset-y-0 right-0 z-10 flex w-full flex-col border-l border-white/10 bg-white shadow-2xl sm:w-80 lg:relative lg:w-[340px] xl:w-[380px]">
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-2 lg:hidden">
              <span className="text-sm font-medium text-slate-700">Transcript</span>
              <button
                type="button"
                onClick={() => setShowTranscript(false)}
                className="rounded p-1 text-slate-500 hover:bg-slate-100"
                aria-label="Close transcript"
              >
                ✕
              </button>
            </div>
            <SessionTranscript
              messages={messages}
              clientName={clientName}
              isLoading={isLoading}
              className="min-h-0 flex-1 bg-slate-50"
            />
          </aside>
        )}
      </div>

      {/* Bottom control bar — video-call style */}
      <footer className="border-t border-white/10 bg-slate-900/95 px-4 py-4 backdrop-blur-sm sm:px-6">
        <div className="mx-auto flex max-w-3xl flex-col items-center gap-4">
          <VoiceRecorder onRecorded={onSendAudio} disabled={isLoading} />

          <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3">
            <button
              type="button"
              onClick={() => setShowTranscript((v) => !v)}
              className={`rounded-full px-4 py-2 text-sm font-medium transition ${
                showTranscript
                  ? "bg-white/15 text-white"
                  : "border border-white/20 text-slate-300 hover:bg-white/5"
              }`}
            >
              Transcript
            </button>
            <button
              type="button"
              onClick={() => setShowTextInput((v) => !v)}
              className="rounded-full border border-white/20 px-4 py-2 text-sm font-medium text-slate-300 hover:bg-white/5"
            >
              {showTextInput ? "Hide keyboard" : "Type"}
            </button>
            <button
              type="button"
              onClick={onEndSession}
              disabled={isLoading}
              className={`rounded-full px-5 py-2 text-sm font-medium transition ${
                canEnd
                  ? "bg-red-600 text-white hover:bg-red-500"
                  : "border border-white/20 text-slate-400 hover:bg-white/5"
              } disabled:opacity-50`}
            >
              End session
            </button>
          </div>

          <p className="text-center text-[11px] text-slate-500">
            Your camera is analyzed on-device only. Aggregate attending metrics are saved at session end.
          </p>
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
              className="flex-1 resize-none rounded-lg border border-white/20 bg-slate-800 px-3 py-2 text-sm text-white placeholder:text-slate-500 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className="self-end rounded-lg bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-500 disabled:bg-slate-600"
            >
              Send
            </button>
          </div>
        )}
      </footer>
    </div>
  );
}
