import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Layout from "../components/Layout";
import LoadingSpinner from "../components/LoadingSpinner";
import {
  createScenario,
  getFacultyScenario,
  listScenarioTemplates,
  updateScenario,
} from "../api/client";
import { ApiError } from "../api/client";
import type {
  ClientBehaviorRule,
  CounselorSkillRule,
  DisclosureItem,
  Difficulty,
  EmotionalCueRule,
  EngagementLevelDescription,
  EvaluationFocusSection,
  LearningObjective,
  ProgressionBeat,
  RubricItem,
  ScenarioAuthoringInput,
  ScenarioTemplate,
  SessionSuccessIndicator,
  SilenceResponseRule,
} from "../types";
import { detailToInput, emptyScenario, linesToArray } from "../lib/scenarioForm";

// --- Small presentational inputs ------------------------------------------

function Section({
  title,
  hint,
  children,
}: {
  title: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <h2 className="text-lg font-semibold text-navy-700">{title}</h2>
      {hint && <p className="mt-1 text-sm text-slate-500">{hint}</p>}
      <div className="mt-4 space-y-4">{children}</div>
    </section>
  );
}

const inputClass =
  "mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-navy-600 focus:outline-none focus:ring-1 focus:ring-navy-600";

const BEHAVIOR_KEY_OPTIONS = [
  "accurate_empathy",
  "reflection_of_feeling",
  "reflection_of_meaning",
  "open_ended_question",
  "validation",
  "emotional_exploration",
  "appropriate_processing_space",
  "cue_acknowledgment",
  "cue_deepening",
  "therapeutic_presence",
  "rapport_building",
  "pacing",
  "premature_advice",
  "rapid_fire_questions",
  "excessive_questioning",
  "frequent_topic_shift",
  "early_problem_solving",
  "ignored_emotional_cue",
];

function BehaviorKeyField({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      Behavior key
      <select className={inputClass} value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">Select a runtime signal</option>
        {BEHAVIOR_KEY_OPTIONS.map((key) => (
          <option key={key} value={key}>{key.replaceAll("_", " ")}</option>
        ))}
      </select>
    </label>
  );
}

function TextField({
  label,
  value,
  onChange,
  placeholder,
  required,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  required?: boolean;
}) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      {required && <span className="text-red-500"> *</span>}
      <input
        className={inputClass}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

function TextArea({
  label,
  value,
  onChange,
  rows = 3,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  rows?: number;
  placeholder?: string;
}) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <textarea
        className={inputClass}
        rows={rows}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}

function ListField({
  label,
  value,
  onChange,
  hint,
  rows = 3,
}: {
  label: string;
  value: string[];
  onChange: (v: string[]) => void;
  hint?: string;
  rows?: number;
}) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      {hint && <span className="ml-1 font-normal text-slate-400">({hint})</span>}
      <textarea
        className={inputClass}
        rows={rows}
        value={value.join("\n")}
        placeholder="One item per line"
        onChange={(e) => onChange(linesToArray(e.target.value))}
      />
    </label>
  );
}

function anchorsToLines(value: Record<string, string>): string {
  return Object.entries(value)
    .sort(([a], [b]) => Number(b) - Number(a))
    .map(([score, description]) => `${score}: ${description}`)
    .join("\n");
}

function linesToAnchors(value: string): Record<string, string> {
  return Object.fromEntries(
    value
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [score, ...rest] = line.split(":");
        return [score.trim(), rest.join(":").trim()];
      })
      .filter(([score, description]) => score && description),
  );
}

function NumberField({
  label,
  value,
  onChange,
  min,
  max,
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  min: number;
  max: number;
}) {
  return (
    <label className="block text-sm font-medium text-slate-700">
      {label}
      <input
        className={inputClass}
        type="number"
        min={min}
        max={max}
        value={value}
        onChange={(e) => onChange(Number(e.target.value) || min)}
      />
    </label>
  );
}

function ProgressionBeatEditor({
  items,
  onChange,
}: {
  items: ProgressionBeat[];
  onChange: (items: ProgressionBeat[]) => void;
}) {
  const update = (idx: number, patch: Partial<ProgressionBeat>) =>
    onChange(items.map((item, i) => (i === idx ? { ...item, ...patch } : item)));
  const add = () =>
    onChange([
      ...items,
      {
        key: `beat_${items.length + 1}`,
        title: "New progression beat",
        session_stage: "early",
        emotional_cues: [],
        emotional_intensity: 2,
        private_meaning: "",
        disclosure_label: "",
        disclosure_content: "",
        semantic_claims: [],
        example_expressions: [],
        prerequisite_beat_keys: items.length ? [items[items.length - 1].key] : [],
        minimum_trust_level: 1,
        minimum_engagement_level: 1,
        required_counselor_response: "any",
        trigger: "volunteer",
        repeatable: false,
        required_for_completion: false,
        faculty_only_notes: "",
      },
    ]);
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-800">Story progression</h3>
          <p className="mt-1 text-xs text-slate-500">
            Each beat connects what the client feels, what may be revealed, and what must happen first.
          </p>
        </div>
        <button type="button" onClick={add} className="text-sm font-medium text-navy-700 hover:underline">
          + Add beat
        </button>
      </div>
      {items.map((item, idx) => (
        <details key={`${item.key}-${idx}`} open={idx === 0} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
          <summary className="cursor-pointer text-sm font-semibold text-slate-800">
            {idx + 1}. {item.title || "Untitled beat"} · {item.session_stage}
          </summary>
          <div className="mt-4 space-y-4">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <TextField label="Beat title" value={item.title} onChange={(v) => update(idx, { title: v })} />
              <TextField label="Stable key" value={item.key} onChange={(v) => update(idx, { key: v.trim().toLowerCase().replace(/[^a-z0-9]+/g, "_") })} />
              <label className="block text-sm font-medium text-slate-700">
                Session stage
                <select className={inputClass} value={item.session_stage} onChange={(e) => update(idx, { session_stage: e.target.value as ProgressionBeat["session_stage"] })}>
                  <option value="early">Early</option><option value="mid">Mid</option><option value="later">Later</option>
                </select>
              </label>
              <NumberField label="Emotional intensity" value={item.emotional_intensity} min={1} max={5} onChange={(v) => update(idx, { emotional_intensity: v })} />
            </div>
            <TextArea label="Private meaning" value={item.private_meaning ?? ""} rows={2} onChange={(v) => update(idx, { private_meaning: v })} />
            <div className="grid gap-4 lg:grid-cols-2">
              <ListField label="Emotional cues" value={item.emotional_cues} onChange={(v) => update(idx, { emotional_cues: v })} />
              <ListField label="Example client expressions" value={item.example_expressions} onChange={(v) => update(idx, { example_expressions: v })} />
            </div>
            <div className="grid gap-4 lg:grid-cols-2">
              <TextField label="Disclosure label" value={item.disclosure_label ?? ""} onChange={(v) => update(idx, { disclosure_label: v })} />
              <TextArea label="Permitted disclosure" value={item.disclosure_content ?? ""} rows={2} onChange={(v) => update(idx, { disclosure_content: v })} />
            </div>
            <ListField label="Semantic claims conveyed by this disclosure" value={item.semantic_claims} onChange={(v) => update(idx, { semantic_claims: v })} />
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              <ListField label="Prerequisite beat keys" value={item.prerequisite_beat_keys} rows={2} onChange={(v) => update(idx, { prerequisite_beat_keys: v })} />
              <NumberField label="Minimum trust" value={item.minimum_trust_level} min={1} max={5} onChange={(v) => update(idx, { minimum_trust_level: v })} />
              <NumberField label="Minimum engagement" value={item.minimum_engagement_level} min={1} max={5} onChange={(v) => update(idx, { minimum_engagement_level: v })} />
              <label className="block text-sm font-medium text-slate-700">
                Trigger
                <select className={inputClass} value={item.trigger} onChange={(e) => update(idx, { trigger: e.target.value as ProgressionBeat["trigger"] })}>
                  <option value="opening">Opening</option><option value="volunteer">Volunteer</option><option value="after_rapport">After rapport</option><option value="after_reflection">After reflection</option><option value="after_pause">After pause</option><option value="direct_question">Direct question</option>
                </select>
              </label>
              <label className="block text-sm font-medium text-slate-700">
                Counselor condition
                <select className={inputClass} value={item.required_counselor_response} onChange={(e) => update(idx, { required_counselor_response: e.target.value as ProgressionBeat["required_counselor_response"] })}>
                  <option value="any">Any response</option><option value="acknowledge_cue">Acknowledge cue</option><option value="deepen_cue">Deepen cue</option><option value="direct_question">Direct question</option><option value="therapeutic_pause">Therapeutic pause</option>
                </select>
              </label>
            </div>
            <div className="flex flex-wrap items-center gap-5 text-sm text-slate-700">
              <label className="flex items-center gap-2"><input type="checkbox" checked={item.required_for_completion} onChange={(e) => update(idx, { required_for_completion: e.target.checked })} />Required story beat</label>
              <label className="flex items-center gap-2"><input type="checkbox" checked={item.repeatable} onChange={(e) => update(idx, { repeatable: e.target.checked })} />May repeat</label>
              <button type="button" onClick={() => onChange(items.filter((_, i) => i !== idx))} className="ml-auto font-medium text-red-600 hover:underline">Remove beat</button>
            </div>
          </div>
        </details>
      ))}
    </div>
  );
}

function DisclosureEditor({
  title,
  items,
  onAdd,
  onChange,
  onRemove,
}: {
  title: string;
  items: DisclosureItem[];
  onAdd: () => void;
  onChange: (idx: number, patch: Partial<DisclosureItem>) => void;
  onRemove: (idx: number) => void;
}) {
  return (
    <div className="rounded-lg border border-slate-200 p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
        <button
          type="button"
          onClick={onAdd}
          className="text-sm font-medium text-navy-700 hover:underline"
        >
          + Add
        </button>
      </div>
      {items.length === 0 ? (
        <p className="mt-3 text-sm text-slate-500">No disclosures defined.</p>
      ) : (
        <div className="mt-3 space-y-4">
          {items.map((item, idx) => (
            <div key={idx} className="space-y-3 border-t border-slate-100 pt-4 first:border-0 first:pt-0">
              <div className="flex items-start gap-3">
                <input
                  className={`${inputClass} mt-0 flex-1`}
                  placeholder="Short label"
                  value={item.label}
                  onChange={(e) => onChange(idx, { label: e.target.value })}
                />
                <button
                  type="button"
                  onClick={() => onRemove(idx)}
                  className="pt-2 text-sm font-medium text-red-600 hover:underline"
                >
                  Remove
                </button>
              </div>
              <textarea
                className={inputClass}
                rows={2}
                placeholder="Content summary the client may reveal"
                value={item.content_summary}
                onChange={(e) => onChange(idx, { content_summary: e.target.value })}
              />
              <div className="grid gap-4 sm:grid-cols-3">
                <NumberField
                  label="Minimum engagement"
                  value={item.minimum_engagement_level}
                  min={1}
                  max={5}
                  onChange={(v) => onChange(idx, { minimum_engagement_level: v })}
                />
                <label className="block text-sm font-medium text-slate-700">
                  Session stage
                  <select
                    className={inputClass}
                    value={item.session_stage}
                    onChange={(e) =>
                      onChange(idx, {
                        session_stage: e.target.value as DisclosureItem["session_stage"],
                      })
                    }
                  >
                    <option value="early">Early</option>
                    <option value="mid">Mid</option>
                    <option value="later">Later</option>
                  </select>
                </label>
                <label className="mt-7 flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={item.requires_direct_question}
                    onChange={(e) =>
                      onChange(idx, { requires_direct_question: e.target.checked })
                    }
                  />
                  Requires direct question
                </label>
              </div>
              <textarea
                className={inputClass}
                rows={2}
                placeholder="Faculty-only notes"
                value={item.faculty_only_notes ?? ""}
                onChange={(e) => onChange(idx, { faculty_only_notes: e.target.value })}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function EngagementLevelsEditor({
  items,
  onChange,
}: {
  items: EngagementLevelDescription[];
  onChange: (items: EngagementLevelDescription[]) => void;
}) {
  const update = (idx: number, patch: Partial<EngagementLevelDescription>) =>
    onChange(items.map((item, i) => (i === idx ? { ...item, ...patch } : item)));
  return (
    <div className="space-y-3">
      {items.map((item, idx) => (
        <div key={idx} className="grid gap-3 rounded-lg border border-slate-200 p-3 lg:grid-cols-[80px_1fr_2fr_2fr]">
          <NumberField
            label="Level"
            value={item.level}
            min={1}
            max={5}
            onChange={(v) => update(idx, { level: v })}
          />
          <TextField label="Label" value={item.label} onChange={(v) => update(idx, { label: v })} />
          <TextArea label="Description" value={item.description} rows={2} onChange={(v) => update(idx, { description: v })} />
          <TextArea label="Typical response" value={item.typical_response ?? ""} rows={2} onChange={(v) => update(idx, { typical_response: v })} />
        </div>
      ))}
    </div>
  );
}

function BehaviorRulesEditor({
  title,
  items,
  onChange,
}: {
  title: string;
  items: ClientBehaviorRule[];
  onChange: (items: ClientBehaviorRule[]) => void;
}) {
  const update = (idx: number, patch: Partial<ClientBehaviorRule>) =>
    onChange(items.map((item, i) => (i === idx ? { ...item, ...patch } : item)));
  const add = () =>
    onChange([
      ...items,
      { counselor_behavior: "", behavior_key: "", client_response: "", engagement_change: 0 },
    ]);
  return (
    <div className="rounded-lg border border-slate-200 p-4">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
        <button type="button" onClick={add} className="text-sm font-medium text-navy-700 hover:underline">
          + Add
        </button>
      </div>
      <div className="mt-3 space-y-3">
        {items.map((item, idx) => (
          <div key={idx} className="grid gap-3 border-t border-slate-100 pt-3 first:border-0 first:pt-0 lg:grid-cols-[1fr_1fr_1.5fr_100px_auto]">
            <TextField label="Counselor behavior" value={item.counselor_behavior} onChange={(v) => update(idx, { counselor_behavior: v })} />
            <BehaviorKeyField value={item.behavior_key ?? ""} onChange={(v) => update(idx, { behavior_key: v })} />
            <TextField label="Client response" value={item.client_response} onChange={(v) => update(idx, { client_response: v })} />
            <NumberField label="Delta" value={item.engagement_change} min={-5} max={5} onChange={(v) => update(idx, { engagement_change: v })} />
            <button type="button" onClick={() => onChange(items.filter((_, i) => i !== idx))} className="pt-7 text-sm font-medium text-red-600 hover:underline">
              Remove
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

function EmotionalCueEditor({
  items,
  onChange,
}: {
  items: EmotionalCueRule[];
  onChange: (items: EmotionalCueRule[]) => void;
}) {
  const update = (idx: number, patch: Partial<EmotionalCueRule>) =>
    onChange(items.map((item, i) => (i === idx ? { ...item, ...patch } : item)));
  return (
    <div className="space-y-3">
      {items.map((item, idx) => (
        <div key={idx} className="grid gap-3 rounded-lg border border-slate-200 p-3 md:grid-cols-[160px_1fr_1fr]">
          <label className="block text-sm font-medium text-slate-700">
            Stage
            <select
              className={inputClass}
              value={item.session_stage}
              onChange={(e) => update(idx, { session_stage: e.target.value as EmotionalCueRule["session_stage"] })}
            >
              <option value="early">Early</option>
              <option value="mid">Mid</option>
              <option value="later">Later</option>
            </select>
          </label>
          <ListField label="Emotional cues" value={item.emotional_cues} onChange={(v) => update(idx, { emotional_cues: v })} rows={2} />
          <ListField label="Example statements" value={item.example_statements} onChange={(v) => update(idx, { example_statements: v })} rows={2} />
        </div>
      ))}
    </div>
  );
}

function SilenceRulesEditor({
  items,
  onChange,
}: {
  items: SilenceResponseRule[];
  onChange: (items: SilenceResponseRule[]) => void;
}) {
  const update = (idx: number, patch: Partial<SilenceResponseRule>) =>
    onChange(items.map((item, i) => (i === idx ? { ...item, ...patch } : item)));
  return (
    <div className="space-y-3">
      {items.map((item, idx) => (
        <div key={idx} className="grid gap-3 rounded-lg border border-slate-200 p-3 md:grid-cols-[1fr_1fr_100px]">
          <TextField label="Use of silence" value={item.counselor_use_of_silence} onChange={(v) => update(idx, { counselor_use_of_silence: v })} />
          <TextField label="Client response" value={item.client_response} onChange={(v) => update(idx, { client_response: v })} />
          <NumberField label="Delta" value={item.engagement_change} min={-5} max={5} onChange={(v) => update(idx, { engagement_change: v })} />
        </div>
      ))}
    </div>
  );
}

function SkillRulesEditor({
  items,
  onChange,
}: {
  items: CounselorSkillRule[];
  onChange: (items: CounselorSkillRule[]) => void;
}) {
  const update = (idx: number, patch: Partial<CounselorSkillRule>) =>
    onChange(items.map((item, i) => (i === idx ? { ...item, ...patch } : item)));
  return (
    <div className="space-y-3">
      {items.map((item, idx) => (
        <div key={idx} className="grid gap-3 rounded-lg border border-slate-200 p-3 lg:grid-cols-[1fr_1fr_1.5fr_1.5fr]">
          <TextField label="Skill" value={item.skill} onChange={(v) => update(idx, { skill: v })} />
          <BehaviorKeyField value={item.behavior_key ?? ""} onChange={(v) => update(idx, { behavior_key: v })} />
          <TextField label="Behavioral indicator" value={item.behavioral_indicator} onChange={(v) => update(idx, { behavioral_indicator: v })} />
          <TextField label="Expected client reaction" value={item.expected_client_reaction} onChange={(v) => update(idx, { expected_client_reaction: v })} />
        </div>
      ))}
    </div>
  );
}

function SuccessIndicatorsEditor({
  items,
  onChange,
}: {
  items: SessionSuccessIndicator[];
  onChange: (items: SessionSuccessIndicator[]) => void;
}) {
  const update = (idx: number, patch: Partial<SessionSuccessIndicator>) =>
    onChange(items.map((item, i) => (i === idx ? { ...item, ...patch } : item)));
  return (
    <div className="space-y-3">
      {items.map((item, idx) => (
        <div key={idx} className="grid gap-3 rounded-lg border border-slate-200 p-3 md:grid-cols-2">
          <TextField label="Indicator" value={item.indicator} onChange={(v) => update(idx, { indicator: v })} />
          <TextField label="Evidence" value={item.evidence} onChange={(v) => update(idx, { evidence: v })} />
        </div>
      ))}
    </div>
  );
}

function EvaluationFocusEditor({
  items,
  onChange,
}: {
  items: EvaluationFocusSection[];
  onChange: (items: EvaluationFocusSection[]) => void;
}) {
  const update = (idx: number, patch: Partial<EvaluationFocusSection>) =>
    onChange(items.map((item, i) => (i === idx ? { ...item, ...patch } : item)));
  return (
    <div className="space-y-3">
      {items.map((item, idx) => (
        <div key={idx} className="space-y-3 rounded-lg border border-slate-200 p-3">
          <div className="grid gap-3 md:grid-cols-2">
            <TextField label="Key" value={item.key} onChange={(v) => update(idx, { key: v })} />
            <TextField label="Title" value={item.title} onChange={(v) => update(idx, { title: v })} />
          </div>
          <ListField label="Instructions" value={item.instructions} onChange={(v) => update(idx, { instructions: v })} rows={3} />
        </div>
      ))}
    </div>
  );
}

// --- Page -----------------------------------------------------------------

export default function ScenarioBuilderPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const isEdit = Boolean(scenarioId);
  const navigate = useNavigate();

  const [form, setForm] = useState<ScenarioAuthoringInput>(emptyScenario());
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [templates, setTemplates] = useState<ScenarioTemplate[]>([]);
  const [scenarioMeta, setScenarioMeta] = useState<{
    template_key: string;
    template_version: string;
    current_version_id: string | null;
  } | null>(null);

  useEffect(() => {
    listScenarioTemplates().then(setTemplates).catch(() => setTemplates([]));
  }, []);

  useEffect(() => {
    if (!scenarioId) return;
    getFacultyScenario(scenarioId)
      .then((detail) => {
        setForm(detailToInput(detail));
        setScenarioMeta({
          template_key: detail.template_key,
          template_version: detail.template_version,
          current_version_id: detail.current_version_id,
        });
      })
      .catch(() => setError("Could not load this scenario."))
      .finally(() => setLoading(false));
  }, [scenarioId]);

  const rubricTotal = useMemo(
    () => form.rubric.reduce((sum, item) => sum + (Number(item.weight) || 0), 0),
    [form.rubric],
  );

  const canSave =
    form.title.trim().length > 0 &&
    form.client_identity.name.trim().length > 0 &&
    form.presenting_concern.primary_concern.trim().length > 0;

  const set = (patch: Partial<ScenarioAuthoringInput>) =>
    setForm((prev) => ({ ...prev, ...patch }));
  const activeTemplate =
    templates.find((template) => template.key === scenarioMeta?.template_key) ??
    templates[0];

  const save = async (thenPreview: boolean) => {
    setSaving(true);
    setError(null);
    setNote(null);
    try {
      const saved = isEdit
        ? await updateScenario(scenarioId as string, form)
        : await createScenario(form);
      if (thenPreview) {
        navigate(`/faculty/scenarios/${saved.id}/preview`);
        return;
      }
      setNote("Draft saved.");
      if (!isEdit) navigate(`/faculty/scenarios/${saved.id}/edit`, { replace: true });
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not save the scenario.");
    } finally {
      setSaving(false);
    }
  };

  const addRubricRow = () =>
    set({
      rubric: [
        ...form.rubric,
        {
          category: "",
          description: null,
          max_score: 5,
          weight: 0,
          observable_indicators: [],
          common_mistakes: [],
          feedback_guidance: null,
          rating_anchors: {},
          optional_when_not_observable: false,
        },
      ],
    });

  const updateRubricRow = (idx: number, patch: Partial<RubricItem>) =>
    set({
      rubric: form.rubric.map((row, i) => (i === idx ? { ...row, ...patch } : row)),
    });

  const removeRubricRow = (idx: number) =>
    set({ rubric: form.rubric.filter((_, i) => i !== idx) });

  const addObjective = () =>
    set({
      learning_objectives: [
        ...form.learning_objectives,
        { name: "", description: "" },
      ],
    });

  const updateObjective = (idx: number, patch: Partial<LearningObjective>) =>
    set({
      learning_objectives: form.learning_objectives.map((row, i) =>
        i === idx ? { ...row, ...patch } : row,
      ),
    });

  const removeObjective = (idx: number) =>
    set({ learning_objectives: form.learning_objectives.filter((_, i) => i !== idx) });

  const newDisclosureItem = (
    stage: DisclosureItem["session_stage"],
    minimumEngagement: number,
    requiresDirectQuestion = false,
  ): DisclosureItem => ({
    key: null,
    label: "",
    content_summary: "",
    minimum_engagement_level: minimumEngagement,
    session_stage: stage,
    requires_direct_question: requiresDirectQuestion,
    faculty_only_notes: "",
  });

  const addDisclosureItem = (group: keyof Pick<ScenarioAuthoringInput["disclosure_rules"], "immediate" | "after_rapport" | "on_direct_question">) => {
    const defaults =
      group === "after_rapport"
        ? newDisclosureItem("mid", 3)
        : group === "on_direct_question"
          ? newDisclosureItem("early", 2, true)
          : newDisclosureItem("early", 1);
    set({
      disclosure_rules: {
        ...form.disclosure_rules,
        [group]: [...form.disclosure_rules[group], defaults],
      },
    });
  };

  const updateDisclosureItem = (
    group: keyof Pick<ScenarioAuthoringInput["disclosure_rules"], "immediate" | "after_rapport" | "on_direct_question">,
    idx: number,
    patch: Partial<DisclosureItem>,
  ) =>
    set({
      disclosure_rules: {
        ...form.disclosure_rules,
        [group]: form.disclosure_rules[group].map((item, i) =>
          i === idx ? { ...item, ...patch } : item,
        ),
      },
    });

  const removeDisclosureItem = (
    group: keyof Pick<ScenarioAuthoringInput["disclosure_rules"], "immediate" | "after_rapport" | "on_direct_question">,
    idx: number,
  ) =>
    set({
      disclosure_rules: {
        ...form.disclosure_rules,
        [group]: form.disclosure_rules[group].filter((_, i) => i !== idx),
      },
    });

  if (loading) {
    return (
      <Layout>
        <div className="flex justify-center py-20">
          <LoadingSpinner label="Loading scenario..." />
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link to="/faculty/scenarios" className="text-sm text-navy-600 hover:underline">
            &larr; Back to scenarios
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-navy-700">
            {isEdit ? "Edit Scenario" : "New Scenario"}
          </h1>
        </div>
      </div>

      {error && (
        <p className="mb-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-red-200">
          {error}
        </p>
      )}

      <div className="space-y-6">
        <Section title="Basic information">
          <div className="rounded-lg bg-slate-50 p-3 text-sm text-slate-700 ring-1 ring-slate-200">
            <p className="font-medium text-slate-800">
              {activeTemplate?.display_name ?? "Advanced Microskills and Emotional Exploration"}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              Template: {scenarioMeta?.template_key ?? activeTemplate?.key ?? "microskills_progressive_disclosure"} · Version:{" "}
              {scenarioMeta?.template_version ?? activeTemplate?.version ?? "1.0.0"}
              {scenarioMeta?.current_version_id
                ? ` · Published version: ${scenarioMeta.current_version_id.slice(0, 8)}`
                : ""}
            </p>
            <Link
              to="/faculty/scenario-templates"
              className="mt-2 inline-block text-xs font-medium text-navy-700 hover:underline"
            >
              View full template content
            </Link>
          </div>
          <TextField
            label="Scenario title"
            required
            value={form.title}
            onChange={(v) => set({ title: v })}
            placeholder="e.g., Overwhelmed New Teacher"
          />
          <TextArea
            label="Scenario description (shown to students)"
            value={form.description ?? ""}
            onChange={(v) => set({ description: v })}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block text-sm font-medium text-slate-700">
              Difficulty
              <select
                className={inputClass}
                value={form.difficulty}
                onChange={(e) => set({ difficulty: e.target.value as Difficulty })}
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </label>
            <TextField
              label="Estimated number of exchanges"
              value={form.estimated_turns?.toString() ?? ""}
              onChange={(v) =>
                set({ estimated_turns: v.trim() === "" ? null : Number(v) || null })
              }
              placeholder="e.g., 8"
            />
          </div>
          <TextArea
            label="Opening message (the client's first line; optional)"
            value={form.opening_message ?? ""}
            onChange={(v) => set({ opening_message: v })}
            placeholder="If left blank, one is generated from the presenting concern."
          />
        </Section>

        <Section
          title="Client identity"
          hint="Describe lived context and role. Avoid stereotyping or tokenizing the client."
        >
          <TextField
            label="Client name"
            required
            value={form.client_identity.name}
            onChange={(v) =>
              set({ client_identity: { ...form.client_identity, name: v } })
            }
          />
          <div className="grid gap-4 sm:grid-cols-3">
            <TextField
              label="Age / age range"
              value={form.client_identity.age ?? ""}
              onChange={(v) => set({ client_identity: { ...form.client_identity, age: v } })}
            />
            <TextField
              label="Pronouns"
              value={form.client_identity.pronouns ?? ""}
              onChange={(v) =>
                set({ client_identity: { ...form.client_identity, pronouns: v } })
              }
            />
            <TextField
              label="Occupation or role"
              value={form.client_identity.occupation ?? ""}
              onChange={(v) =>
                set({ client_identity: { ...form.client_identity, occupation: v } })
              }
            />
          </div>
          <TextArea
            label="General background"
            value={form.client_identity.background ?? ""}
            onChange={(v) =>
              set({ client_identity: { ...form.client_identity, background: v } })
            }
          />
          <TextArea
            label="Relevant identity context"
            value={form.client_identity.identity_information ?? ""}
            onChange={(v) =>
              set({
                client_identity: { ...form.client_identity, identity_information: v },
              })
            }
          />
        </Section>

        <Section title="Presenting concern">
          <TextArea
            label="Primary presenting concern"
            value={form.presenting_concern.primary_concern}
            onChange={(v) =>
              set({ presenting_concern: { ...form.presenting_concern, primary_concern: v } })
            }
            rows={2}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <TextArea
              label="Secondary concern"
              value={form.presenting_concern.secondary_concern ?? ""}
              onChange={(v) =>
                set({
                  presenting_concern: { ...form.presenting_concern, secondary_concern: v },
                })
              }
              rows={2}
            />
            <TextArea
              label="Reason for attending"
              value={form.presenting_concern.reason_for_attending ?? ""}
              onChange={(v) =>
                set({
                  presenting_concern: {
                    ...form.presenting_concern,
                    reason_for_attending: v,
                  },
                })
              }
              rows={2}
            />
          </div>
          <TextArea
            label="Client's own explanation of the problem"
            value={form.presenting_concern.client_explanation ?? ""}
            onChange={(v) =>
              set({
                presenting_concern: { ...form.presenting_concern, client_explanation: v },
              })
            }
            rows={2}
          />
          <TextArea
            label="What the client hopes will change"
            value={form.presenting_concern.hoped_change ?? ""}
            onChange={(v) =>
              set({ presenting_concern: { ...form.presenting_concern, hoped_change: v } })
            }
            rows={2}
          />
        </Section>

        <Section
          title="Cultural and contextual considerations"
          hint="Focus on lived context, values, and communication preferences relevant to the learning objective."
        >
          <TextArea
            label="Cultural or contextual factors"
            value={form.cultural_considerations.cultural_factors ?? ""}
            onChange={(v) =>
              set({
                cultural_considerations: {
                  ...form.cultural_considerations,
                  cultural_factors: v,
                },
              })
            }
            rows={2}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField
              label="Language preferences"
              value={form.cultural_considerations.language_preferences ?? ""}
              onChange={(v) =>
                set({
                  cultural_considerations: {
                    ...form.cultural_considerations,
                    language_preferences: v,
                  },
                })
              }
            />
            <TextField
              label="Communication preferences"
              value={form.cultural_considerations.communication_preferences ?? ""}
              onChange={(v) =>
                set({
                  cultural_considerations: {
                    ...form.cultural_considerations,
                    communication_preferences: v,
                  },
                })
              }
            />
          </div>
          <TextArea
            label="Values relevant to the session"
            value={form.cultural_considerations.relevant_values ?? ""}
            onChange={(v) =>
              set({
                cultural_considerations: {
                  ...form.cultural_considerations,
                  relevant_values: v,
                },
              })
            }
            rows={2}
          />
          <TextArea
            label="Possible concerns about the counselor"
            value={form.cultural_considerations.concerns_about_counselor ?? ""}
            onChange={(v) =>
              set({
                cultural_considerations: {
                  ...form.cultural_considerations,
                  concerns_about_counselor: v,
                },
              })
            }
            rows={2}
          />
          <ListField
            label="Topics requiring sensitivity"
            value={form.cultural_considerations.sensitive_topics}
            onChange={(v) =>
              set({
                cultural_considerations: {
                  ...form.cultural_considerations,
                  sensitive_topics: v,
                },
              })
            }
          />
        </Section>

        <Section
          title="Client progression and interaction style"
          hint="Define the client's starting stance and the ordered emotional story the simulation may reveal."
        >
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <label className="block text-sm font-medium text-slate-700">
              Resistance level
              <select
                className={inputClass}
                value={form.resistance_configuration.level}
                onChange={(e) =>
                  set({
                    resistance_configuration: {
                      ...form.resistance_configuration,
                      level: Number(e.target.value),
                    },
                  })
                }
              >
                <option value={1}>1 — Cooperative</option>
                <option value={2}>2 — Mildly hesitant</option>
                <option value={3}>3 — Guarded</option>
                <option value={4}>4 — Resistant</option>
                <option value={5}>5 — Highly resistant</option>
              </select>
            </label>
            <NumberField
              label="Starting engagement"
              value={form.resistance_configuration.starting_engagement_level}
              min={1}
              max={5}
              onChange={(v) =>
                set({
                  resistance_configuration: {
                    ...form.resistance_configuration,
                    starting_engagement_level: v,
                  },
                })
              }
            />
            <NumberField
              label="Minimum engagement"
              value={form.resistance_configuration.minimum_engagement_level}
              min={1}
              max={5}
              onChange={(v) =>
                set({
                  resistance_configuration: {
                    ...form.resistance_configuration,
                    minimum_engagement_level: v,
                  },
                })
              }
            />
            <NumberField
              label="Maximum engagement"
              value={form.resistance_configuration.maximum_engagement_level}
              min={1}
              max={5}
              onChange={(v) =>
                set({
                  resistance_configuration: {
                    ...form.resistance_configuration,
                    maximum_engagement_level: v,
                  },
                })
              }
            />
          </div>
          <label className="block text-sm font-medium text-slate-700">
            Trust development speed
            <select
              className={inputClass}
              value={form.resistance_configuration.trust_development_speed}
              onChange={(e) =>
                set({
                  resistance_configuration: {
                    ...form.resistance_configuration,
                    trust_development_speed: e.target.value as "slow" | "moderate" | "fast",
                  },
                })
              }
            >
              <option value="slow">Slow</option>
              <option value="moderate">Moderate</option>
              <option value="fast">Fast</option>
            </select>
          </label>
          <div className="grid gap-4 sm:grid-cols-2">
            <TextArea
              label="What increases resistance"
              value={form.resistance_configuration.increases_when ?? ""}
              onChange={(v) =>
                set({
                  resistance_configuration: {
                    ...form.resistance_configuration,
                    increases_when: v,
                  },
                })
              }
              rows={2}
            />
            <TextArea
              label="What decreases resistance"
              value={form.resistance_configuration.decreases_when ?? ""}
              onChange={(v) =>
                set({
                  resistance_configuration: {
                    ...form.resistance_configuration,
                    decreases_when: v,
                  },
                })
              }
              rows={2}
            />
          </div>
          <TextArea
            label="How trust should develop"
            value={form.resistance_configuration.trust_development ?? ""}
            onChange={(v) =>
              set({
                resistance_configuration: {
                  ...form.resistance_configuration,
                  trust_development: v,
                },
              })
            }
            rows={2}
          />
          <ListField
            label="Student behaviors the client should resist"
            hint="for example: premature advice, rapid-fire questions"
            value={form.resistance_configuration.behaviors_to_resist}
            onChange={(v) =>
              set({
                resistance_configuration: {
                  ...form.resistance_configuration,
                  behaviors_to_resist: v,
                },
              })
            }
          />
          <ProgressionBeatEditor
            items={form.progression_beats}
            onChange={(v) => set({ progression_beats: v })}
          />
          <details className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <summary className="cursor-pointer text-sm font-semibold text-slate-800">
              Advanced behavior engine defaults
            </summary>
            <div className="mt-4 space-y-4">
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-slate-800">Engagement scale</h3>
                <EngagementLevelsEditor
                  items={form.engagement_levels}
                  onChange={(v) => set({ engagement_levels: v })}
                />
              </div>
              <BehaviorRulesEditor
                title="Engagement increase rules"
                items={form.engagement_increase_rules}
                onChange={(v) => set({ engagement_increase_rules: v })}
              />
              <BehaviorRulesEditor
                title="Engagement decrease rules"
                items={form.engagement_decrease_rules}
                onChange={(v) => set({ engagement_decrease_rules: v })}
              />
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-slate-800">Emotional cue progression</h3>
                <EmotionalCueEditor
                  items={form.emotional_cue_progression}
                  onChange={(v) => set({ emotional_cue_progression: v })}
                />
              </div>
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-slate-800">Silence response rules</h3>
                <SilenceRulesEditor
                  items={form.silence_response_rules}
                  onChange={(v) => set({ silence_response_rules: v })}
                />
              </div>
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-slate-800">Counselor skill reactions</h3>
                <SkillRulesEditor
                  items={form.counselor_skill_detection}
                  onChange={(v) => set({ counselor_skill_detection: v })}
                />
              </div>
              <div className="space-y-3">
                <h3 className="text-sm font-semibold text-slate-800">Session success indicators</h3>
                <SuccessIndicatorsEditor
                  items={form.session_success_indicators}
                  onChange={(v) => set({ session_success_indicators: v })}
                />
              </div>
            </div>
          </details>
          <details className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <summary className="cursor-pointer text-sm font-semibold text-slate-800">
              Legacy disclosure buckets
            </summary>
            <div className="mt-4 space-y-4">
          <DisclosureEditor
            title="Immediate disclosures"
            items={form.disclosure_rules.immediate}
            onAdd={() => addDisclosureItem("immediate")}
            onChange={(idx, patch) => updateDisclosureItem("immediate", idx, patch)}
            onRemove={(idx) => removeDisclosureItem("immediate", idx)}
          />
          <DisclosureEditor
            title="Progressive disclosures after rapport"
            items={form.disclosure_rules.after_rapport}
            onAdd={() => addDisclosureItem("after_rapport")}
            onChange={(idx, patch) => updateDisclosureItem("after_rapport", idx, patch)}
            onRemove={(idx) => removeDisclosureItem("after_rapport", idx)}
          />
          <DisclosureEditor
            title="Direct-question disclosures"
            items={form.disclosure_rules.on_direct_question}
            onAdd={() => addDisclosureItem("on_direct_question")}
            onChange={(idx, patch) => updateDisclosureItem("on_direct_question", idx, patch)}
            onRemove={(idx) => removeDisclosureItem("on_direct_question", idx)}
          />
          <ListField
            label="Never disclose in this scenario"
            value={form.disclosure_rules.never}
            onChange={(v) =>
              set({ disclosure_rules: { ...form.disclosure_rules, never: v } })
            }
          />
            </div>
          </details>
        </Section>

        <Section title="Emotional tone and hidden information">
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField
              label="Starting emotional tone"
              value={form.emotional_tone.starting_tone ?? ""}
              onChange={(v) =>
                set({ emotional_tone: { ...form.emotional_tone, starting_tone: v } })
              }
              placeholder="e.g., hesitant"
            />
            <TextField
              label="Communication style"
              value={form.emotional_tone.communication_style ?? ""}
              onChange={(v) =>
                set({ emotional_tone: { ...form.emotional_tone, communication_style: v } })
              }
            />
            <TextField
              label="Level of emotional intensity"
              value={form.emotional_tone.intensity ?? ""}
              onChange={(v) =>
                set({ emotional_tone: { ...form.emotional_tone, intensity: v } })
              }
            />
            <TextField
              label="Typical response length"
              value={form.emotional_tone.typical_response_length ?? ""}
              onChange={(v) =>
                set({
                  emotional_tone: { ...form.emotional_tone, typical_response_length: v },
                })
              }
              placeholder="e.g., short, 1-2 sentences"
            />
          </div>
          <ListField
            label="Possible emotional shifts"
            value={form.emotional_tone.possible_shifts}
            onChange={(v) =>
              set({ emotional_tone: { ...form.emotional_tone, possible_shifts: v } })
            }
          />
          <ListField
            label="Hidden information"
            hint="known to the AI, never volunteered to the student"
            value={form.hidden_information}
            onChange={(v) => set({ hidden_information: v })}
          />
        </Section>

        <Section
          title="Learning objectives"
          hint="At least one is required to publish. Descriptions are included in evaluation context."
        >
          <div className="space-y-4">
            {form.learning_objectives.map((objective, idx) => (
              <div key={idx} className="space-y-3 border-b border-slate-100 pb-4 last:border-0">
                <div className="flex items-start gap-3">
                  <input
                    className={`${inputClass} mt-0 flex-1`}
                    placeholder="Objective name"
                    value={objective.name}
                    onChange={(e) => updateObjective(idx, { name: e.target.value })}
                  />
                  <button
                    type="button"
                    onClick={() => removeObjective(idx)}
                    className="pt-2 text-sm font-medium text-red-600 hover:underline"
                  >
                    Remove
                  </button>
                </div>
                <textarea
                  className={inputClass}
                  rows={2}
                  placeholder="Objective description"
                  value={objective.description ?? ""}
                  onChange={(e) => updateObjective(idx, { description: e.target.value })}
                />
              </div>
            ))}
          </div>
          <button
            type="button"
            onClick={addObjective}
            className="text-sm font-medium text-navy-700 hover:underline"
          >
            + Add learning objective
          </button>
        </Section>

        <Section
          title="Feedback rubric"
          hint="Weights must total 100 to publish. These criteria are frozen into the published scenario version and used by evaluation."
        >
          <div className="space-y-3">
            {form.rubric.map((row, idx) => (
              <div key={idx} className="space-y-3 border-b border-slate-100 pb-4 last:border-0">
                <div className="flex flex-wrap items-start gap-3">
                  <input
                    className={`${inputClass} mt-0 min-w-56 flex-1`}
                    placeholder="Category (e.g., Empathy)"
                    value={row.category}
                    onChange={(e) => updateRubricRow(idx, { category: e.target.value })}
                  />
                  <label className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Max score
                    <input
                      className={`${inputClass} mt-1 w-24`}
                      type="number"
                      min={1}
                      max={10}
                      value={row.max_score}
                      onChange={(e) =>
                        updateRubricRow(idx, { max_score: Number(e.target.value) || 5 })
                      }
                    />
                  </label>
                  <label className="text-xs font-medium uppercase tracking-wide text-slate-500">
                    Weight
                    <input
                      className={`${inputClass} mt-1 w-24`}
                      type="number"
                      min={0}
                      max={100}
                      value={row.weight}
                      onChange={(e) =>
                        updateRubricRow(idx, { weight: Number(e.target.value) || 0 })
                      }
                    />
                  </label>
                  <button
                    type="button"
                    onClick={() => removeRubricRow(idx)}
                    className="pt-2 text-sm font-medium text-red-600 hover:underline"
                  >
                    Remove
                  </button>
                </div>
                <TextArea
                  label="Criterion description"
                  value={row.description ?? ""}
                  onChange={(v) => updateRubricRow(idx, { description: v })}
                  rows={2}
                />
                <div className="grid gap-4 sm:grid-cols-2">
                  <ListField
                    label="Observable indicators"
                    value={row.observable_indicators}
                    onChange={(v) => updateRubricRow(idx, { observable_indicators: v })}
                  />
                  <ListField
                    label="Common mistakes"
                    value={row.common_mistakes}
                    onChange={(v) => updateRubricRow(idx, { common_mistakes: v })}
                  />
                </div>
                <TextArea
                  label="Feedback guidance"
                  value={row.feedback_guidance ?? ""}
                  onChange={(v) => updateRubricRow(idx, { feedback_guidance: v })}
                  rows={2}
                />
                <TextArea
                  label="1-5 rating anchors"
                  value={anchorsToLines(row.rating_anchors ?? {})}
                  onChange={(v) => updateRubricRow(idx, { rating_anchors: linesToAnchors(v) })}
                  rows={5}
                  placeholder="5: Advanced description&#10;4: Proficient description"
                />
                <label className="flex items-center gap-2 text-sm text-slate-700">
                  <input
                    type="checkbox"
                    checked={row.optional_when_not_observable}
                    onChange={(e) =>
                      updateRubricRow(idx, {
                        optional_when_not_observable: e.target.checked,
                      })
                    }
                  />
                  Optional when not observable in this modality
                </label>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-between">
            <button
              type="button"
              onClick={addRubricRow}
              className="text-sm font-medium text-navy-700 hover:underline"
            >
              + Add rubric category
            </button>
            {form.rubric.length > 0 && (
              <span
                className={`text-sm font-medium ${
                  rubricTotal === 100 ? "text-emerald-600" : "text-amber-600"
                }`}
              >
                Total weight: {rubricTotal} / 100
              </span>
            )}
          </div>
        </Section>

        <Section
          title="Evaluation guidance"
          hint="These sections guide the structured feedback report and faculty review expectations."
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <ListField
              label="Competency scale"
              hint="score range: competency level"
              value={form.competency_scale.map(
                (item) => `${item.score_range}: ${item.competency_level}`,
              )}
              onChange={(lines) =>
                set({
                  competency_scale: lines.map((line) => {
                    const [scoreRange, ...rest] = line.split(":");
                    return {
                      score_range: scoreRange.trim(),
                      competency_level: rest.join(":").trim(),
                    };
                  }),
                })
              }
              rows={5}
            />
            <ListField
              label="Reflection questions"
              value={form.reflection_questions}
              onChange={(v) => set({ reflection_questions: v })}
              rows={8}
            />
          </div>
          <EvaluationFocusEditor
            items={form.evaluation_focus_sections}
            onChange={(v) => set({ evaluation_focus_sections: v })}
          />
        </Section>

        <Section
          title="Safety boundaries"
          hint="Default safety rules always apply. Crisis, self-harm, and abuse content are not permitted in this version."
        >
          <ListField
            label="Additional disallowed topics"
            value={form.safety_rules.disallowed_topics}
            onChange={(v) =>
              set({ safety_rules: { ...form.safety_rules, disallowed_topics: v } })
            }
          />
          <TextArea
            label="Required redirection if pushed toward unsafe content"
            value={form.safety_rules.required_redirection ?? ""}
            onChange={(v) =>
              set({ safety_rules: { ...form.safety_rules, required_redirection: v } })
            }
            rows={2}
          />
          <TextField
            label="Maximum emotional intensity"
            value={form.safety_rules.max_emotional_intensity ?? ""}
            onChange={(v) =>
              set({ safety_rules: { ...form.safety_rules, max_emotional_intensity: v } })
            }
          />
          <ListField
            label="Ending topics or graceful close options"
            value={form.safety_rules.ending_topics}
            onChange={(v) =>
              set({ safety_rules: { ...form.safety_rules, ending_topics: v } })
            }
          />
          <div className="grid gap-4 lg:grid-cols-2">
            <ListField
              label="Ambiguous safety phrases"
              hint="phrases that require clarification, not automatic crisis classification"
              value={form.safety_rules.ambiguous_safety_phrases}
              onChange={(v) => set({ safety_rules: { ...form.safety_rules, ambiguous_safety_phrases: v } })}
            />
            <ListField
              label="Faculty review triggers"
              value={form.safety_rules.safety_review_triggers}
              onChange={(v) => set({ safety_rules: { ...form.safety_rules, safety_review_triggers: v } })}
            />
          </div>
          <TextArea
            label="Required clarification response"
            value={form.safety_rules.required_safety_clarification ?? ""}
            onChange={(v) => set({ safety_rules: { ...form.safety_rules, required_safety_clarification: v } })}
            rows={2}
          />
          <label className="flex items-center gap-2 text-sm text-slate-500">
            <input type="checkbox" checked={false} disabled />
            Crisis, self-harm, and abuse disclosure content allowed
          </label>
          <label className="flex items-center gap-2 text-sm text-slate-700">
            <input
              type="checkbox"
              checked={form.safety_rules.faculty_review_required}
              onChange={(e) =>
                set({
                  safety_rules: {
                    ...form.safety_rules,
                    faculty_review_required: e.target.checked,
                  },
                })
              }
            />
            Faculty review required before students see results
          </label>
        </Section>
      </div>

      <div className="sticky bottom-0 mt-6 flex flex-wrap items-center gap-3 rounded-xl bg-white/95 p-4 shadow-sm ring-1 ring-slate-200 backdrop-blur">
        <button
          type="button"
          disabled={!canSave || saving}
          onClick={() => save(false)}
          className="rounded-lg border border-navy-700 px-5 py-2.5 text-sm font-medium text-navy-700 hover:bg-navy-50 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save draft"}
        </button>
        <button
          type="button"
          disabled={!canSave || saving}
          onClick={() => save(true)}
          className="rounded-lg bg-navy-700 px-5 py-2.5 text-sm font-medium text-white hover:bg-navy-800 disabled:opacity-50"
        >
          Save &amp; Preview
        </button>
        {!canSave && (
          <span className="text-sm text-slate-500">
            Title, client name, and primary concern are required.
          </span>
        )}
        {note && (
          <span className="text-sm text-emerald-700" role="status">
            {note}
          </span>
        )}
      </div>
    </Layout>
  );
}
