import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Layout from "../components/Layout";
import TranscriptViewer from "../components/TranscriptViewer";
import FeedbackScoreCard from "../components/FeedbackScoreCard";
import RubricScoreTable from "../components/RubricScoreTable";
import LoadingSpinner from "../components/LoadingSpinner";
import { getFacultySession, saveFacultyReview } from "../api/client";
import type { FacultySessionDetail, PromptTrace } from "../types";

export default function FacultySessionReviewPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [session, setSession] = useState<FacultySessionDetail | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveNote, setSaveNote] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    getFacultySession(sessionId)
      .then((s) => {
        setSession(s);
        setComment(s.faculty_comment);
      })
      .catch(() => setNotFound(true));
  }, [sessionId]);

  const handleSave = async (markReviewed: boolean) => {
    if (!sessionId) return;
    setSaving(true);
    setSaveNote(null);
    try {
      await saveFacultyReview(sessionId, {
        comments: comment,
        adjusted_score: null,
        review_status: markReviewed ? "reviewed" : "pending",
      });
      const refreshed = await getFacultySession(sessionId);
      setSession(refreshed);
      setComment(refreshed.faculty_comment);
      setSaveNote(markReviewed ? "Session marked as reviewed." : "Comment saved.");
    } catch {
      setSaveNote("Could not save. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  if (notFound) {
    return (
      <Layout>
        <p className="py-20 text-center text-slate-600">
          Session not found.{" "}
          <Link to="/faculty" className="font-medium text-navy-600 hover:underline">
            Back to Faculty Dashboard
          </Link>
        </p>
      </Layout>
    );
  }

  if (!session) {
    return (
      <Layout>
        <div className="flex justify-center py-20">
          <LoadingSpinner label="Loading session..." />
        </div>
      </Layout>
    );
  }

  const fb = session.evaluation;
  const isReviewed = session.status === "reviewed" || session.review_status === "reviewed";

  return (
    <Layout>
      <div className="mx-auto max-w-4xl space-y-8">
        <header className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-navy-700">Session Review</h1>
            <p className="mt-1 text-slate-600">{session.scenario_title}</p>
          </div>
          <Link to="/faculty" className="text-sm font-medium text-navy-600 hover:underline">
            Back to Faculty Dashboard
          </Link>
        </header>

        <section className="grid gap-4 rounded-xl bg-white p-6 text-sm shadow-sm ring-1 ring-slate-200 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-slate-500">Student</p>
            <p className="font-medium text-slate-800">{session.student_name}</p>
          </div>
          <div>
            <p className="text-slate-500">Date completed</p>
            <p className="font-medium text-slate-800">
              {session.ended_at
                ? new Date(session.ended_at).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })
                : "—"}
            </p>
          </div>
          <div>
            <p className="text-slate-500">Overall score</p>
            <p className="font-medium text-slate-800">
              {fb ? `${fb.overall_score.toFixed(1)} / 5` : "—"}
            </p>
          </div>
          <div>
            <p className="text-slate-500">Status</p>
            <p className="font-medium text-slate-800">{isReviewed ? "Reviewed" : "Awaiting review"}</p>
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold text-slate-800">Transcript</h2>
          <TranscriptViewer messages={session.messages} clientName={session.client_name} />
        </section>

        {fb && (
          <section className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-800">AI Feedback</h2>
            <FeedbackScoreCard score={fb.overall_score} />
            <RubricScoreTable scores={fb.rubric_scores} />
            {fb.faculty_review_recommended && (
              <div className="rounded-xl bg-amber-50 p-5 text-sm text-amber-900 ring-1 ring-amber-200">
                Faculty review is recommended for this session.
              </div>
            )}
            <div className="grid gap-6 md:grid-cols-2">
              <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
                <h3 className="font-semibold text-emerald-700">Strengths</h3>
                <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-700">
                  {fb.strengths.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              </div>
              <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
                <h3 className="font-semibold text-navy-700">Areas for Growth</h3>
                <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-700">
                  {fb.areas_for_growth.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="rounded-xl bg-teal-50 p-6 ring-1 ring-teal-200">
              <h3 className="font-semibold text-teal-800">Suggested Improved Response</h3>
              <p className="mt-2 text-slate-800">“{fb.suggested_improved_response}”</p>
            </div>
          </section>
        )}

        {session.prompt_trace && <PromptTracePanel trace={session.prompt_trace} />}

        <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <label htmlFor="faculty-comment" className="text-lg font-semibold text-slate-800">
            Faculty comments
          </label>
          <textarea
            id="faculty-comment"
            rows={4}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Add notes for this student session..."
            className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-navy-600 focus:outline-none focus:ring-1 focus:ring-navy-600"
          />
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => handleSave(false)}
              disabled={saving}
              className="rounded-lg bg-navy-700 px-5 py-2.5 text-sm font-medium text-white hover:bg-navy-600 disabled:opacity-50"
            >
              Save Comment
            </button>
            <button
              type="button"
              onClick={() => handleSave(true)}
              disabled={saving || isReviewed}
              className="rounded-lg border border-navy-700 px-5 py-2.5 text-sm font-medium text-navy-700 hover:bg-navy-50 disabled:opacity-50"
            >
              {isReviewed ? "Reviewed" : "Mark Reviewed"}
            </button>
            {saveNote && (
              <span className="text-sm text-emerald-700" role="status">
                {saveNote}
              </span>
            )}
          </div>
        </section>
      </div>
    </Layout>
  );
}

function PromptTracePanel({ trace }: { trace: PromptTrace }) {
  return (
    <section className="rounded-xl bg-white p-6 text-sm shadow-sm ring-1 ring-slate-200">
      <h2 className="text-lg font-semibold text-slate-800">Stateful Prompt Trace</h2>
      <p className="mt-1 text-xs text-slate-500">
        Faculty-only reconstruction of the client system prompts and final evaluator prompt
        used for this student session.
      </p>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <TracePrompt title="Base client prompt" text={trace.base_client_prompt_text} />
        <TracePrompt title="Latest runtime state block" text={trace.latest_runtime_context_text} />
        <TracePrompt
          title="Latest full stateful client system prompt"
          text={trace.latest_client_stateful_system_prompt_text}
        />
        <TracePrompt
          title="Final evaluation prompt"
          text={trace.final_evaluation_prompt_text ?? "Not available."}
        />
      </div>

      <details className="mt-4">
        <summary className="cursor-pointer font-medium text-slate-700">
          Per-turn stateful prompt replay
        </summary>
        <div className="mt-3 space-y-3">
          {trace.turn_traces.map((turn) => (
            <div key={turn.student_turn_count} className="rounded-lg bg-slate-50 p-3 ring-1 ring-slate-200">
              <p className="font-medium text-slate-800">
                Student turn {turn.student_turn_count}: {turn.student_message}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Engagement {turn.engagement_level}/5 · Trust {turn.trust_level}/5 ·
                Depth {turn.response_plan?.emotional_depth ?? 1}/5 ·
                Stage {turn.session_stage} · Engagement delta {turn.engagement_delta} ·
                Trust delta {turn.trust_delta ?? 0}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Detected: {turn.detected_behaviors.join(", ") || "none"}
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Cue response: {turn.cue_response_analysis?.status ?? "no active cue"}
                {turn.cue_response_analysis?.cue
                  ? ` · ${turn.cue_response_analysis.cue}`
                  : ""}
              </p>
              {turn.stage_gate && (
                <p className="mt-1 text-xs text-slate-500">
                  Next-stage gate ({turn.stage_gate.target_stage}): {turn.stage_gate.satisfied ? "story ready" : "blocked"}
                  {turn.stage_gate.missing_beat_keys.length
                    ? ` · missing ${turn.stage_gate.missing_beat_keys.join(", ")}`
                    : ""}
                  {turn.stage_gate.blocking_cues.length
                    ? ` · ${turn.stage_gate.blocking_cues.length} unresolved cue(s)`
                    : ""}
                </p>
              )}
              <p className="mt-1 text-xs text-slate-500">
                Allowed disclosures: {turn.allowed_disclosures.join("; ") || "none"}
              </p>
              {turn.response_plan && (
                <div className="mt-2 rounded bg-white p-2 text-xs text-slate-600 ring-1 ring-slate-200">
                  <p>Active cue: {turn.response_plan.active_emotional_cues.join(", ") || "none"}</p>
                  <p>
                    Selected disclosure: {turn.response_plan.selected_disclosure_label || "none"}
                  </p>
                  <p>
                    Validation: {turn.validation?.accepted ? "accepted" : "not confirmed"} ·
                    Revealed: {turn.revealed_information?.join(", ") || "none"}
                  </p>
                </div>
              )}
              <div className="mt-3">
                <TracePrompt
                  title="Response plan, semantic evidence, and generation attempts"
                  text={JSON.stringify(
                    {
                      response_plan: turn.response_plan,
                      counselor_analysis: turn.counselor_analysis,
                      cue_response_analysis: turn.cue_response_analysis,
                      validation: turn.validation,
                      generation_attempts: turn.generation_attempts,
                    },
                    null,
                    2,
                  )}
                />
              </div>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                <TracePrompt
                  title="Runtime state block"
                  text={turn.runtime_context_text}
                />
                <TracePrompt
                  title="Conversation prompt"
                  text={turn.client_conversation_prompt_text}
                />
                <TracePrompt
                  title="Full stateful client system prompt"
                  text={turn.client_stateful_system_prompt_text}
                />
              </div>
            </div>
          ))}
        </div>
      </details>

      <details className="mt-4">
        <summary className="cursor-pointer font-medium text-slate-700">
          Evaluation inputs and state history
        </summary>
        <div className="mt-3 grid gap-3">
          <TracePrompt
            title="State history JSON"
            text={JSON.stringify(trace.state_history, null, 2)}
          />
          <TracePrompt
            title="Simulation fidelity audit"
            text={JSON.stringify(trace.simulation_fidelity ?? {}, null, 2)}
          />
          <TracePrompt
            title="Evaluation transcript"
            text={trace.evaluation_transcript_text ?? "Not available."}
          />
          <TracePrompt
            title="Evaluator system prompt"
            text={trace.evaluator_system_prompt_text ?? "Not available."}
          />
          <TracePrompt
            title="Evaluator user prompt"
            text={trace.evaluator_user_prompt_text ?? "Not available."}
          />
        </div>
      </details>
    </section>
  );
}

function TracePrompt({ title, text }: { title: string; text: string }) {
  return (
    <details className="rounded-lg bg-slate-50 p-3 ring-1 ring-slate-200">
      <summary className="cursor-pointer text-sm font-medium text-slate-700">
        {title}
      </summary>
      <pre className="mt-2 max-h-96 overflow-auto whitespace-pre-wrap rounded bg-slate-950 p-3 text-xs text-slate-100">
        {text}
      </pre>
    </details>
  );
}
