import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import Layout from "../components/Layout";
import ChatWindow from "../components/ChatWindow";
import LoadingSpinner from "../components/LoadingSpinner";
import WebcamMonitor from "../components/WebcamMonitor";
import {
  completeSession,
  evaluateSession,
  getScenario,
  sendAudioMessage,
  sendMessage,
  startSession,
} from "../api/client";
import type {
  ChatMessage,
  Modality,
  NonverbalSummary,
  ScenarioDetail,
  SessionDetail,
} from "../types";
import { MIN_STUDENT_MESSAGES, MODALITY_LABELS } from "../types";

function base64ToObjectUrl(base64: string, mimeType: string): string {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
  return URL.createObjectURL(new Blob([bytes], { type: mimeType }));
}

function parseModality(raw: string | null): Modality {
  return raw === "audio" || raw === "video" ? raw : "text";
}

export default function SimulationChatPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const [searchParams] = useSearchParams();
  const modality = parseModality(searchParams.get("mode"));
  const navigate = useNavigate();
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [endWarning, setEndWarning] = useState<string | null>(null);
  const [clientAudioUrl, setClientAudioUrl] = useState<string | null>(null);
  const startedRef = useRef(false);
  // Latest aggregated webcam metrics (video mode); submitted on session end.
  const nonverbalRef = useRef<NonverbalSummary | null>(null);

  useEffect(() => {
    if (!scenarioId || startedRef.current) return;
    startedRef.current = true;
    (async () => {
      try {
        const selectedScenario = await getScenario(scenarioId);
        setScenario(selectedScenario);
        const newSession = await startSession(selectedScenario.id, modality);
        setSession(newSession);
        setMessages(newSession.messages);
      } catch {
        setError("The simulator service is currently unavailable.");
      }
    })();
  }, [scenarioId, modality]);

  useEffect(() => () => {
    if (clientAudioUrl) URL.revokeObjectURL(clientAudioUrl);
  }, [clientAudioUrl]);

  const clientName = scenario?.client_name ?? "the client";
  const studentCount = messages.filter((m) => m.speaker === "student").length;

  const handleSendAudio = async (audio: Blob) => {
    if (!session || isLoading) return;
    setIsLoading(true);
    setError(null);
    setEndWarning(null);
    try {
      const result = await sendAudioMessage(session.id, audio);
      const studentMessage: ChatMessage = {
        id: `local_${Date.now()}`,
        speaker: "student",
        content: result.transcript,
        sequence_number: (messages[messages.length - 1]?.sequence_number ?? 0) + 1,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, studentMessage, result.message]);
      setClientAudioUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return base64ToObjectUrl(result.audio_base64, result.audio_mime_type);
      });
    } catch {
      setError(`${clientName} could not respond to your recording. Please try again.`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async (text: string) => {
    if (!session || isLoading) return;
    setIsLoading(true);
    setError(null);
    setEndWarning(null);

    const optimistic: ChatMessage = {
      id: `local_${Date.now()}`,
      speaker: "student",
      content: text,
      sequence_number: (messages[messages.length - 1]?.sequence_number ?? 0) + 1,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimistic]);

    try {
      const { message } = await sendMessage(session.id, text);
      setMessages((prev) => [...prev, message]);
    } catch {
      setError(`${clientName} could not respond right now. Please try again.`);
      setMessages((prev) => prev.filter((m) => m.id !== optimistic.id));
    } finally {
      setIsLoading(false);
    }
  };

  const handleEndSession = async () => {
    if (!session) return;
    if (studentCount < MIN_STUDENT_MESSAGES) {
      setEndWarning(`Please send at least ${MIN_STUDENT_MESSAGES} responses before ending the session.`);
      return;
    }
    setIsEvaluating(true);
    setError(null);
    try {
      await completeSession(
        session.id,
        modality === "video" ? (nonverbalRef.current ?? undefined) : undefined,
      );
      await evaluateSession(session.id);
      navigate(`/student/feedback/${session.id}`);
    } catch {
      setError("Feedback could not be generated. Please try again or contact your instructor.");
      setIsEvaluating(false);
    }
  };

  if (!session) {
    return (
      <Layout>
        <div className="flex justify-center py-20">
          {error ? (
            <p className="text-red-600">{error}</p>
          ) : (
            <LoadingSpinner label="Starting your session..." />
          )}
        </div>
      </Layout>
    );
  }

  if (isEvaluating) {
    return (
      <Layout>
        <div className="flex flex-col items-center gap-4 py-20">
          <LoadingSpinner label="Generating your feedback report..." />
          <p className="text-sm text-slate-500">This usually takes a few seconds.</p>
        </div>
      </Layout>
    );
  }

  const skills = scenario
    ? ((scenario.client_profile as { skills?: unknown }).skills as string[] | undefined) ??
      Object.values(scenario.rubric_json)
    : [];

  return (
    <Layout>
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <aside className="space-y-4">
          <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <h2 className="font-semibold text-navy-700">{scenario?.title ?? session.scenario_title}</h2>
            <dl className="mt-3 space-y-1 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">Client</dt>
                <dd className="font-medium text-slate-800">{clientName}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Difficulty</dt>
                <dd className="font-medium text-slate-800">{scenario?.difficulty ?? "\u2014"}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Mode</dt>
                <dd className="font-medium text-slate-800">{MODALITY_LABELS[modality]}</dd>
              </div>
            </dl>
            <p className="mt-4 text-sm font-medium text-slate-600">Skills being practiced</p>
            <ul className="mt-2 flex flex-wrap gap-2">
              {skills.map((skill) => (
                <li
                  key={skill}
                  className="rounded-full bg-navy-50 px-3 py-1 text-xs font-medium text-navy-700"
                >
                  {skill}
                </li>
              ))}
            </ul>
          </div>

          <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <h3 className="text-sm font-semibold text-slate-700">Session progress</h3>
            <p className="mt-2 text-sm text-slate-600">
              {studentCount} of {MIN_STUDENT_MESSAGES} minimum responses sent
            </p>
            <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-200" aria-hidden="true">
              <div
                className="h-full rounded-full bg-teal-500 transition-all"
                style={{ width: `${Math.min(100, (studentCount / MIN_STUDENT_MESSAGES) * 100)}%` }}
              />
            </div>
          </div>

          {modality === "video" && (
            <WebcamMonitor
              onSummaryChange={(summary) => {
                nonverbalRef.current = summary;
              }}
            />
          )}

          {scenario && (
            <div className="rounded-xl bg-navy-50 p-5 text-sm text-navy-800 ring-1 ring-navy-100">
              {scenario.student_goal}
            </div>
          )}
        </aside>

        <section>
          {endWarning && (
            <p className="mb-3 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800 ring-1 ring-amber-200" role="alert">
              {endWarning}
            </p>
          )}
          <ChatWindow
            messages={messages}
            clientName={clientName}
            isLoading={isLoading}
            error={error}
            onSend={handleSend}
            onEndSession={handleEndSession}
            modality={modality}
            onSendAudio={modality === "text" ? undefined : handleSendAudio}
            clientAudioUrl={clientAudioUrl}
          />
        </section>
      </div>
    </Layout>
  );
}
