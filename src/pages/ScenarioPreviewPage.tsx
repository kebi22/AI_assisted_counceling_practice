import { useEffect, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Layout from "../components/Layout";
import LoadingSpinner from "../components/LoadingSpinner";
import { ApiError } from "../api/client";
import {
  generateScenarioPreview,
  getFacultyScenario,
  publishScenario,
  testScenarioMessage,
} from "../api/client";
import type {
  DisclosureItem,
  FacultyScenarioDetail,
  ScenarioPreviewResponse,
  ScenarioTestMessageResponse,
  TestTurn,
} from "../types";
import { SCENARIO_STATUS_LABELS } from "../types";

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 py-1 text-sm">
      <dt className="text-slate-500">{label}</dt>
      <dd className="text-right font-medium text-slate-800">{value}</dd>
    </div>
  );
}

export default function ScenarioPreviewPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const navigate = useNavigate();

  const [detail, setDetail] = useState<FacultyScenarioDetail | null>(null);
  const [preview, setPreview] = useState<ScenarioPreviewResponse | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [showPrompt, setShowPrompt] = useState(false);
  const [showEvaluatorPrompt, setShowEvaluatorPrompt] = useState(false);

  const [turns, setTurns] = useState<TestTurn[]>([]);
  const [debugState, setDebugState] =
    useState<NonNullable<ScenarioTestMessageResponse["debug_state"]> | null>(null);
  const [promptTrace, setPromptTrace] =
    useState<NonNullable<ScenarioTestMessageResponse["trace"]> | null>(null);
  const [input, setInput] = useState("");
  const [testBusy, setTestBusy] = useState(false);
  const [testError, setTestError] = useState<string | null>(null);

  const [publishing, setPublishing] = useState(false);
  const [publishError, setPublishError] = useState<string | null>(null);
  const [publishedVersion, setPublishedVersion] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);

  const runPreview = async (id: string) => {
    setGenerating(true);
    try {
      setPreview(await generateScenarioPreview(id));
    } catch {
      setLoadError("Could not generate the client behavior preview.");
    } finally {
      setGenerating(false);
    }
  };

  useEffect(() => {
    if (!scenarioId) return;
    getFacultyScenario(scenarioId)
      .then((d) => {
        setDetail(d);
        return runPreview(scenarioId);
      })
      .catch(() => setLoadError("Could not load this scenario."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenarioId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [turns]);

  const sendTest = async () => {
    if (!scenarioId || !input.trim() || testBusy) return;
    const content = input.trim();
    setInput("");
    setTestError(null);
    const history = [...turns];
    setTurns((prev) => [...prev, { speaker: "student", content }]);
    setTestBusy(true);
    try {
      const { reply, debug_state, trace } = await testScenarioMessage(
        scenarioId,
        content,
        history,
      );
      setTurns((prev) => [...prev, { speaker: "client", content: reply }]);
      setDebugState(debug_state ?? null);
      setPromptTrace(trace ?? null);
    } catch {
      setTestError("The client could not respond. Try again.");
      setTurns((prev) => prev.slice(0, -1));
    } finally {
      setTestBusy(false);
    }
  };

  const handlePublish = async () => {
    if (!scenarioId) return;
    setPublishing(true);
    setPublishError(null);
    try {
      const result = await publishScenario(scenarioId);
      setPublishedVersion(result.scenario_version_id);
      setTimeout(() => navigate("/faculty/scenarios"), 1200);
    } catch (e) {
      setPublishError(
        e instanceof ApiError ? e.message : "Could not publish the scenario.",
      );
    } finally {
      setPublishing(false);
    }
  };

  if (loadError) {
    return (
      <Layout>
        <p className="py-20 text-center text-red-600">{loadError}</p>
      </Layout>
    );
  }

  if (!detail) {
    return (
      <Layout>
        <div className="flex justify-center py-20">
          <LoadingSpinner label="Loading scenario..." />
        </div>
      </Layout>
    );
  }

  const clientName = detail.client_identity?.name || "the client";
  const objectives = detail.learning_objectives ?? [];
  const rubric = detail.rubric_items ?? [];
  const disclosure = detail.disclosure_rules;
  const isPublished = detail.status === "published" || Boolean(publishedVersion);

  return (
    <Layout>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link to="/faculty/scenarios" className="text-sm text-navy-600 hover:underline">
            &larr; Back to scenarios
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-navy-700">{detail.title}</h1>
          <p className="text-sm text-slate-500">
            Status: {SCENARIO_STATUS_LABELS[detail.status]}
            {preview?.prompt_version ? ` \u00b7 ${preview.prompt_version}` : ""}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            Template: {detail.template_key} v{detail.template_version}
            {detail.current_version_id ? ` · Version ${detail.current_version_id.slice(0, 8)}` : ""}
            {publishedVersion ? ` · New version ${publishedVersion.slice(0, 8)}` : ""}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to={`/faculty/scenarios/${detail.id}`}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Full details
          </Link>
          {!isPublished && (
            <Link
              to={`/faculty/scenarios/${detail.id}/edit`}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Edit
            </Link>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        {/* Left: summary + generated behavior */}
        <div className="space-y-6">
          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <h2 className="text-lg font-semibold text-navy-700">Scenario summary</h2>
            <dl className="mt-3 divide-y divide-slate-100">
              <SummaryRow label="Client" value={clientName} />
              <SummaryRow label="Template" value={detail.template_key} />
              <SummaryRow label="Template version" value={detail.template_version} />
              <SummaryRow label="Difficulty" value={detail.difficulty} />
              <SummaryRow
                label="Resistance level"
                value={`${detail.resistance_configuration?.level ?? "\u2014"} / 5`}
              />
              <SummaryRow
                label="Primary concern"
                value={detail.presenting_concern?.primary_concern ?? "\u2014"}
              />
            </dl>

            <h3 className="mt-5 text-sm font-semibold text-slate-700">Learning objectives</h3>
            {objectives.length ? (
              <ul className="mt-2 space-y-2 text-sm text-slate-600">
                {objectives.map((o, i) => (
                  <li key={i}>
                    <p className="font-medium text-slate-800">{o.name}</p>
                    {o.description && <p>{o.description}</p>}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-1 text-sm text-amber-600">None defined yet.</p>
            )}

            <h3 className="mt-5 text-sm font-semibold text-slate-700">Story progression</h3>
            <ol className="mt-2 space-y-2 text-sm text-slate-600">
              {(detail.progression_beats ?? []).map((beat, index) => (
                <li key={beat.key} className="border-l-2 border-navy-200 pl-3">
                  <p className="font-medium text-slate-800">
                    {index + 1}. {beat.title} · {beat.session_stage}
                  </p>
                  <p>{beat.disclosure_content || "Cue-only beat"}</p>
                  <p className="text-xs text-slate-500">
                    Cues: {beat.emotional_cues.join(", ") || "none"} · trust {beat.minimum_trust_level}+ · engagement {beat.minimum_engagement_level}+ · response milestone {beat.required_counselor_response}
                  </p>
                </li>
              ))}
            </ol>
            {(detail.progression_beats ?? []).length === 0 && (
              <p className="mt-1 text-sm text-slate-500">
                Legacy disclosure adapter: {formatDisclosureItems(disclosure?.immediate)}, {formatDisclosureItems(disclosure?.after_rapport)}, {formatDisclosureItems(disclosure?.on_direct_question)}.
              </p>
            )}

            <h3 className="mt-5 text-sm font-semibold text-slate-700">Behavior engine</h3>
            <div className="mt-2 grid gap-3 text-sm text-slate-600 sm:grid-cols-2">
              <PreviewList
                label="Engagement levels"
                items={(detail.engagement_levels ?? []).map(
                  (item) => `${item.level} - ${item.label}: ${item.description}`,
                )}
              />
              <PreviewList
                label="Emotional cues"
                items={(detail.emotional_cue_progression ?? []).map(
                  (item) =>
                    `${item.session_stage}: ${item.emotional_cues.join(", ")}${
                      item.example_statements.length
                        ? ` (${item.example_statements.join("; ")})`
                        : ""
                    }`,
                )}
              />
              <PreviewList
                label="Silence rules"
                items={(detail.silence_response_rules ?? []).map(
                  (item) =>
                    `${item.counselor_use_of_silence}: ${item.client_response} (${item.engagement_change})`,
                )}
              />
              <PreviewList
                label="Success indicators"
                items={(detail.session_success_indicators ?? []).map(
                  (item) => `${item.indicator}: ${item.evidence}`,
                )}
              />
            </div>

            {rubric.length > 0 && (
              <>
                <h3 className="mt-5 text-sm font-semibold text-slate-700">Rubric</h3>
                <ul className="mt-1 text-sm text-slate-600">
                  {rubric.map((r, i) => (
                    <li key={i} className="border-b border-slate-100 py-2 last:border-0">
                      <div className="flex justify-between gap-4">
                        <span className="font-medium text-slate-800">{r.category}</span>
                        <span className="text-slate-400">
                          weight {r.weight} · max {r.max_score}
                        </span>
                      </div>
                      {r.description && <p className="mt-1">{r.description}</p>}
                      {r.observable_indicators.length > 0 && (
                        <p className="mt-1 text-xs text-slate-500">
                          Indicators: {r.observable_indicators.join("; ")}
                        </p>
                      )}
                      {Object.keys(r.rating_anchors ?? {}).length > 0 && (
                        <p className="mt-1 text-xs text-slate-500">
                          Anchors:{" "}
                          {Object.keys(r.rating_anchors)
                            .sort((a, b) => Number(b) - Number(a))
                            .join(", ")}
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
              </>
            )}

            {detail.reflection_questions && detail.reflection_questions.length > 0 && (
              <>
                <h3 className="mt-5 text-sm font-semibold text-slate-700">
                  Reflection questions
                </h3>
                <ul className="mt-1 list-inside list-disc space-y-1 text-sm text-slate-600">
                  {detail.reflection_questions.map((question, i) => (
                    <li key={i}>{question}</li>
                  ))}
                </ul>
              </>
            )}
          </section>

          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-navy-700">Generated prompts</h2>
              <button
                type="button"
                onClick={() => scenarioId && runPreview(scenarioId)}
                disabled={generating}
                className="text-sm font-medium text-navy-700 hover:underline disabled:opacity-50"
              >
                {generating ? "Generating..." : "Regenerate"}
              </button>
            </div>

            {preview?.warnings && preview.warnings.length > 0 && (
              <ul className="mt-3 space-y-1 rounded-lg bg-amber-50 p-3 text-sm text-amber-800 ring-1 ring-amber-200">
                {preview.warnings.map((w, i) => (
                  <li key={i}>{"\u26a0 "}{w}</li>
                ))}
              </ul>
            )}

            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => setShowPrompt((s) => !s)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                {showPrompt ? "Hide" : "View"} scenario builder prompt
              </button>
              <button
                type="button"
                onClick={() => setShowEvaluatorPrompt((s) => !s)}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                {showEvaluatorPrompt ? "Hide" : "View"} evaluator builder prompt
              </button>
            </div>
            {showPrompt && (
              <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-xs text-slate-700 ring-1 ring-slate-200">
                {preview?.prompt_text ?? detail.generated_prompt ?? "Not generated yet."}
              </pre>
            )}
            {showEvaluatorPrompt && (
              <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-950 p-3 text-xs text-slate-100 ring-1 ring-slate-800">
                {preview?.evaluator_prompt_text ?? "Not generated yet."}
              </pre>
            )}
          </section>
        </div>

        {/* Right: test chat + publish */}
        <div className="space-y-6">
          <section className="flex h-[60vh] flex-col rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
            <div className="border-b border-slate-200 px-4 py-3">
              <h2 className="font-semibold text-navy-700">Test conversation</h2>
              <p className="text-xs text-slate-500">
                Practice with {clientName}. This does not affect student attempts.
              </p>
            </div>
            <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-4">
              {turns.length === 0 && (
                <p className="text-sm italic text-slate-400">
                  Send a message to see how {clientName} responds.
                </p>
              )}
              {turns.map((t, i) => (
                <div
                  key={i}
                  className={`flex ${t.speaker === "student" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={
                      t.speaker === "student"
                        ? "max-w-[80%] rounded-2xl rounded-tr-sm bg-emerald-50 px-4 py-2 text-sm text-slate-800 ring-1 ring-emerald-100"
                        : "max-w-[80%] rounded-2xl rounded-tl-sm bg-slate-100 px-4 py-2 text-sm text-slate-800"
                    }
                  >
                    {t.content}
                  </div>
                </div>
              ))}
              {testBusy && (
                <p className="text-sm italic text-slate-500">{clientName} is responding...</p>
              )}
              {testError && <p className="text-sm text-red-600">{testError}</p>}
            </div>
            <div className="border-t border-slate-200 p-3">
              <div className="flex gap-2">
                <textarea
                  rows={2}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      sendTest();
                    }
                  }}
                  placeholder={`Respond to ${clientName}...`}
                  className="flex-1 resize-none rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-navy-600 focus:outline-none focus:ring-1 focus:ring-navy-600"
                />
                <button
                  type="button"
                  onClick={sendTest}
                  disabled={testBusy || !input.trim()}
                  className="rounded-lg bg-navy-700 px-4 text-sm font-medium text-white hover:bg-navy-800 disabled:opacity-50"
                >
                  Send
                </button>
              </div>
              {turns.length > 0 && (
                <button
                  type="button"
                  onClick={() => {
                    setTurns([]);
                    setDebugState(null);
                    setPromptTrace(null);
                  }}
                  className="mt-2 text-xs text-slate-500 hover:underline"
                >
                  Reset conversation
                </button>
              )}
            </div>
          </section>

          {debugState && (
            <section className="rounded-xl bg-slate-900 p-5 text-sm text-slate-100 shadow-sm">
              <h2 className="font-semibold">Debug state</h2>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <DebugItem label="Engagement" value={`${debugState.engagement_level} / 5`} />
                <DebugItem label="Trust" value={`${debugState.trust_level} / 5`} />
                <DebugItem label="Disclosure stage" value={String(debugState.disclosure_stage)} />
                <DebugItem label="Session stage" value={debugState.session_stage} />
              </div>
              <DebugList label="Detected behaviors" items={debugState.detected_behaviors} />
              <DebugList label="Expected client reactions" items={debugState.expected_client_reactions ?? []} />
              <DebugList label="Allowed disclosures" items={debugState.allowed_disclosures} />
            </section>
          )}

          {promptTrace && <PromptTracePanel trace={promptTrace} />}

          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <h2 className="text-lg font-semibold text-navy-700">Publish</h2>
            <p className="mt-1 text-sm text-slate-500">
              Once published, students can start sessions with this client.
            </p>
            {publishError && (
              <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200">
                {publishError}
              </p>
            )}
            {publishedVersion ? (
              <p className="mt-3 text-sm font-medium text-emerald-700">
                Published version {publishedVersion.slice(0, 8)}. Redirecting...
              </p>
            ) : (
              <button
                type="button"
                onClick={handlePublish}
                disabled={publishing || isPublished}
                className="mt-3 rounded-lg bg-emerald-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
              >
                {isPublished ? "Published" : publishing ? "Publishing..." : "Publish scenario"}
              </button>
            )}
          </section>
        </div>
      </div>
    </Layout>
  );
}

function DebugItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-0.5 font-medium">{value}</p>
    </div>
  );
}

function PreviewList({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
        {label}
      </p>
      {items.length ? (
        <ul className="mt-1 list-inside list-disc space-y-1">
          {items.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-slate-400">None defined</p>
      )}
    </div>
  );
}

function PromptTracePanel({
  trace,
}: {
  trace: NonNullable<ScenarioTestMessageResponse["trace"]>;
}) {
  return (
    <section className="rounded-xl bg-white p-5 text-sm shadow-sm ring-1 ring-slate-200">
      <h2 className="font-semibold text-navy-700">Stateful prompt trace</h2>
      <p className="mt-1 text-xs text-slate-500">
        Faculty-only trace from the test conversation. Student sessions use the same
        stateful client prompt pattern.
      </p>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <TracePrompt
          title="Latest runtime state block"
          text={trace.latest_runtime_context_text}
        />
        <TracePrompt
          title="Latest client conversation prompt"
          text={trace.latest_client_conversation_prompt_text}
        />
        <TracePrompt
          title="Latest full stateful client system prompt"
          text={trace.latest_client_stateful_system_prompt_text}
        />
        <TracePrompt
          title="Final evaluation prompt"
          text={trace.final_evaluation_prompt_text ?? "Not available yet."}
        />
      </div>

      <details className="mt-4">
        <summary className="cursor-pointer font-medium text-slate-700">
          View per-turn state replay
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
                  {turn.stage_gate.progression_basis === "clinical_milestones"
                    ? ` · milestone ${turn.stage_gate.milestone_ready ? "ready" : "building"}`
                    : ""}
                  {turn.stage_gate.missing_beat_keys.length
                    ? ` · missing ${turn.stage_gate.missing_beat_keys.join(", ")}`
                    : ""}
                  {turn.stage_gate.unresolved_beat_keys?.length
                    ? ` · unresolved beats ${turn.stage_gate.unresolved_beat_keys.join(", ")}`
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
                <div className="my-2 rounded bg-white p-2 text-xs text-slate-600 ring-1 ring-slate-200">
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
              <div className="mb-2">
                <TracePrompt
                  title="Response plan, semantic evidence, and generation attempts"
                  text={JSON.stringify(
                    {
                      response_plan: turn.response_plan,
                      counselor_analysis: turn.counselor_analysis,
                      cue_response_analysis: turn.cue_response_analysis,
                      beat_states: turn.beat_states,
                      validation: turn.validation,
                      generation_attempts: turn.generation_attempts,
                    },
                    null,
                    2,
                  )}
                />
              </div>
              <TracePrompt
                title="Turn stateful client system prompt"
                text={turn.client_stateful_system_prompt_text}
              />
            </div>
          ))}
        </div>
      </details>

      <details className="mt-4">
        <summary className="cursor-pointer font-medium text-slate-700">
          View state history and transcript
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
            text={trace.evaluation_transcript_text ?? "Not available yet."}
          />
          <TracePrompt
            title="Evaluator system prompt only"
            text={trace.evaluator_system_prompt_text ?? "Not available yet."}
          />
          <TracePrompt
            title="Evaluator user prompt only"
            text={trace.evaluator_user_prompt_text ?? "Not available yet."}
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
      <pre className="mt-2 max-h-80 overflow-auto whitespace-pre-wrap rounded bg-slate-950 p-3 text-xs text-slate-100">
        {text}
      </pre>
    </details>
  );
}

function DebugList({ label, items }: { label: string; items: string[] }) {
  return (
    <div className="mt-4">
      <p className="text-xs uppercase tracking-wide text-slate-400">{label}</p>
      {items.length ? (
        <ul className="mt-1 list-inside list-disc space-y-1">
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="mt-1 text-slate-400">None</p>
      )}
    </div>
  );
}

function formatDisclosureItems(items: DisclosureItem[] | undefined): string {
  if (!Array.isArray(items) || items.length === 0) return "\u2014";
  return items
    .map((item) => `${item.label} (${item.minimum_engagement_level}+/${item.session_stage})`)
    .join("; ");
}
