import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Layout from "../components/Layout";
import ChatWindow from "../components/ChatWindow";
import LoadingSpinner from "../components/LoadingSpinner";
import { evaluateSession, sendMessage, startSession } from "../api/client";
import type { SessionRecord } from "../types";
import { SCENARIO } from "../types";

const MIN_STUDENT_MESSAGES = 4;

// Mock auth for Version 1; replace with real authentication later.
const currentUser = { id: "student_001", name: "Demo Student", role: "student" as const };

export default function SimulationChatPage() {
  const navigate = useNavigate();
  const [session, setSession] = useState<SessionRecord | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [endWarning, setEndWarning] = useState<string | null>(null);
  const startedRef = useRef(false);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    startSession(currentUser.name)
      .then(setSession)
      .catch(() => setError("The simulator service is currently unavailable."));
  }, []);

  const studentCount = session?.messages.filter((m) => m.sender === "student").length ?? 0;

  const handleSend = async (text: string) => {
    if (!session || isLoading) return;
    setIsLoading(true);
    setError(null);
    setEndWarning(null);
    try {
      setSession(await sendMessage(session, text));
    } catch {
      setError(`${SCENARIO.clientName} could not respond right now. Please try again.`);
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
      await evaluateSession(session);
      navigate(`/student/feedback/${session.session_id}`);
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

  return (
    <Layout>
      <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
        <aside className="space-y-4">
          <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
            <h2 className="font-semibold text-navy-700">{SCENARIO.title}</h2>
            <dl className="mt-3 space-y-1 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">Client</dt>
                <dd className="font-medium text-slate-800">{SCENARIO.clientName}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Difficulty</dt>
                <dd className="font-medium text-slate-800">{SCENARIO.difficulty}</dd>
              </div>
            </dl>
            <p className="mt-4 text-sm font-medium text-slate-600">Skills being practiced</p>
            <ul className="mt-2 flex flex-wrap gap-2">
              {SCENARIO.skills.map((skill) => (
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

          <div className="rounded-xl bg-navy-50 p-5 text-sm text-navy-800 ring-1 ring-navy-100">
            {SCENARIO.reminder}
          </div>
        </aside>

        <section>
          {endWarning && (
            <p className="mb-3 rounded-lg bg-amber-50 px-4 py-3 text-sm text-amber-800 ring-1 ring-amber-200" role="alert">
              {endWarning}
            </p>
          )}
          <ChatWindow
            messages={session.messages}
            isLoading={isLoading}
            error={error}
            onSend={handleSend}
            onEndSession={handleEndSession}
          />
        </section>
      </div>
    </Layout>
  );
}
