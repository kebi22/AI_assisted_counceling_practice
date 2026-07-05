import { useEffect, useState, type ReactNode } from "react";
import { Link, useParams } from "react-router-dom";
import Layout from "../components/Layout";
import LoadingSpinner from "../components/LoadingSpinner";
import { getFacultyScenario } from "../api/client";
import type { FacultyScenarioDetail } from "../types";
import { SCENARIO_STATUS_LABELS } from "../types";

const RESISTANCE_LABELS: Record<number, string> = {
  1: "Cooperative",
  2: "Mildly hesitant",
  3: "Guarded",
  4: "Resistant",
  5: "Highly resistant",
};

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <h2 className="text-lg font-semibold text-navy-700">{title}</h2>
      <div className="mt-4 space-y-3">{children}</div>
    </section>
  );
}

function Field({ label, value }: { label: string; value: string | null | undefined }) {
  const text = value?.trim();
  return (
    <div>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-0.5 text-sm text-slate-800">{text || "\u2014"}</p>
    </div>
  );
}

function BulletList({
  items,
  empty = "None defined",
}: {
  items: string[] | undefined | null;
  empty?: string;
}) {
  if (!items?.length) {
    return <p className="text-sm text-slate-500">{empty}</p>;
  }
  return (
    <ul className="list-inside list-disc space-y-1 text-sm text-slate-700">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}

function DisclosureList({ items }: { items: NonNullable<FacultyScenarioDetail["disclosure_rules"]>["immediate"] | undefined }) {
  if (!items?.length) return <p className="text-sm text-slate-500">None defined</p>;
  return (
    <ul className="space-y-2 text-sm text-slate-700">
      {items.map((item, i) => (
        <li key={i} className="rounded-lg bg-slate-50 p-3">
          <p className="font-medium text-slate-800">{item.label}</p>
          <p className="mt-1">{item.content_summary}</p>
          <p className="mt-1 text-xs text-slate-500">
            Engagement {item.minimum_engagement_level}+ · {item.session_stage} stage
            {item.requires_direct_question ? " · direct question required" : ""}
          </p>
          {item.faculty_only_notes && (
            <p className="mt-1 text-xs text-slate-500">Notes: {item.faculty_only_notes}</p>
          )}
        </li>
      ))}
    </ul>
  );
}

function KeyValueList({
  items,
  empty = "None defined",
}: {
  items: Record<string, unknown>[] | undefined | null;
  empty?: string;
}) {
  if (!items?.length) return <p className="text-sm text-slate-500">{empty}</p>;
  return (
    <ul className="space-y-2 text-sm text-slate-700">
      {items.map((item, i) => (
        <li key={i} className="rounded-lg bg-slate-50 p-3">
          <dl className="grid gap-2 sm:grid-cols-2">
            {Object.entries(item).map(([key, value]) => (
              <div key={key}>
                <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
                  {humanizeKey(key)}
                </dt>
                <dd className="mt-0.5 text-slate-800">{formatValue(value)}</dd>
              </div>
            ))}
          </dl>
        </li>
      ))}
    </ul>
  );
}

function humanizeKey(key: string): string {
  return key
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "\u2014";
  if (Array.isArray(value)) return value.map(formatValue).join("; ");
  if (typeof value === "object") {
    return Object.entries(value as Record<string, unknown>)
      .map(([key, item]) => `${key}: ${formatValue(item)}`)
      .join("; ");
  }
  return String(value);
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "\u2014";
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function ScenarioDetailContent({ scenario }: { scenario: FacultyScenarioDetail }) {
  const identity = scenario.client_identity;
  const concern = scenario.presenting_concern;
  const culture = scenario.cultural_considerations;
  const resistance = scenario.resistance_configuration;
  const disclosure = scenario.disclosure_rules;
  const tone = scenario.emotional_tone;
  const safety = scenario.safety_rules;
  const rubricTotal = (scenario.rubric_items ?? []).reduce((sum, r) => sum + r.weight, 0);

  return (
    <div className="space-y-6">
      <Section title="Basic information">
        <Field label="Description" value={scenario.description} />
        <div className="grid gap-4 sm:grid-cols-3">
          <Field label="Module" value={String(scenario.module_number)} />
          <Field label="Difficulty" value={scenario.difficulty} />
          <Field label="Estimated exchanges" value={scenario.estimated_turns?.toString()} />
        </div>
        <Field label="Opening client message" value={scenario.opening_message} />
      </Section>

      <Section title="Architecture">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Template key" value={scenario.template_key} />
          <Field label="Template version" value={scenario.template_version} />
          <Field
            label="Current published version"
            value={scenario.current_version_id ?? undefined}
          />
          <Field label="Prompt version" value={scenario.prompt_version ?? undefined} />
        </div>
      </Section>

      <Section title="Client identity">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Name" value={identity?.name} />
          <Field label="Age / age range" value={identity?.age} />
          <Field label="Pronouns" value={identity?.pronouns} />
          <Field label="Occupation or role" value={identity?.occupation} />
        </div>
        <Field label="General background" value={identity?.background} />
        <Field label="Relevant identity context" value={identity?.identity_information} />
      </Section>

      <Section title="Presenting concern">
        <Field label="Primary concern" value={concern?.primary_concern} />
        <Field label="Secondary concern" value={concern?.secondary_concern} />
        <Field label="Reason for attending" value={concern?.reason_for_attending} />
        <Field label="Client's own explanation" value={concern?.client_explanation} />
        <Field label="What the client hopes will change" value={concern?.hoped_change} />
      </Section>

      <Section title="Cultural and contextual considerations">
        <Field label="Cultural or contextual factors" value={culture?.cultural_factors} />
        <Field label="Language preferences" value={culture?.language_preferences} />
        <Field label="Relevant values" value={culture?.relevant_values} />
        <Field label="Possible concerns about the counselor" value={culture?.concerns_about_counselor} />
        <Field label="Communication preferences" value={culture?.communication_preferences} />
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Topics requiring sensitivity
          </p>
          <div className="mt-1">
            <BulletList items={culture?.sensitive_topics} empty="None listed" />
          </div>
        </div>
      </Section>

      <Section title="Story progression">
        <p className="text-sm text-slate-600">
          Ordered emotional beats used by the runtime planner. Private meanings and disclosures remain hidden from students.
        </p>
        <KeyValueList
          items={scenario.progression_beats as Record<string, unknown>[] | null}
          empty="No progression beats defined. This scenario uses the legacy disclosure adapter."
        />
      </Section>

      <Section title="Runtime behavior and legacy rules">
        <Field
          label="Resistance level"
          value={
            resistance?.level
              ? `${RESISTANCE_LABELS[resistance.level] ?? "Unknown"} (${resistance.level} / 5)`
              : undefined
          }
        />
        <div className="grid gap-4 sm:grid-cols-3">
          <Field
            label="Starting engagement"
            value={resistance?.starting_engagement_level?.toString()}
          />
          <Field
            label="Minimum engagement"
            value={resistance?.minimum_engagement_level?.toString()}
          />
          <Field
            label="Maximum engagement"
            value={resistance?.maximum_engagement_level?.toString()}
          />
        </div>
        <Field label="Trust development speed" value={resistance?.trust_development_speed} />
        <Field label="Increases when" value={resistance?.increases_when} />
        <Field label="Decreases when" value={resistance?.decreases_when} />
        <Field label="Trust development" value={resistance?.trust_development} />
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Behaviors to resist
          </p>
          <div className="mt-1">
            <BulletList items={resistance?.behaviors_to_resist} empty="None listed" />
          </div>
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Engagement levels
          </p>
          <div className="mt-1">
            <KeyValueList items={scenario.engagement_levels as Record<string, unknown>[] | null} />
          </div>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Engagement increase rules
            </p>
            <div className="mt-1">
              <KeyValueList items={scenario.engagement_increase_rules as Record<string, unknown>[] | null} />
            </div>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Engagement decrease rules
            </p>
            <div className="mt-1">
              <KeyValueList items={scenario.engagement_decrease_rules as Record<string, unknown>[] | null} />
            </div>
          </div>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Emotional cue progression
            </p>
            <div className="mt-1">
              <KeyValueList items={scenario.emotional_cue_progression as Record<string, unknown>[] | null} />
            </div>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Silence response rules
            </p>
            <div className="mt-1">
              <KeyValueList items={scenario.silence_response_rules as Record<string, unknown>[] | null} />
            </div>
          </div>
        </div>
        <div className="grid gap-4 lg:grid-cols-2">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Counselor skill reactions
            </p>
            <div className="mt-1">
              <KeyValueList items={scenario.counselor_skill_detection as Record<string, unknown>[] | null} />
            </div>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Session success indicators
            </p>
            <div className="mt-1">
              <KeyValueList items={scenario.session_success_indicators as Record<string, unknown>[] | null} />
            </div>
          </div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Disclose immediately
            </p>
            <div className="mt-1">
              <DisclosureList items={disclosure?.immediate} />
            </div>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              After rapport develops
            </p>
            <div className="mt-1">
              <DisclosureList items={disclosure?.after_rapport} />
            </div>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Only if asked directly
            </p>
            <div className="mt-1">
              <DisclosureList items={disclosure?.on_direct_question} />
            </div>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Never disclose
            </p>
            <div className="mt-1">
              <BulletList items={disclosure?.never} />
            </div>
          </div>
        </div>
      </Section>

      <Section title="Emotional tone and hidden information">
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Starting tone" value={tone?.starting_tone} />
          <Field label="Communication style" value={tone?.communication_style} />
          <Field label="Emotional intensity" value={tone?.intensity} />
          <Field label="Typical response length" value={tone?.typical_response_length} />
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Possible emotional shifts
          </p>
          <div className="mt-1">
            <BulletList items={tone?.possible_shifts} empty="None listed" />
          </div>
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Hidden information
          </p>
          <p className="mt-0.5 text-xs text-slate-400">
            Known to the AI client only; not shown to students.
          </p>
          <div className="mt-1">
            <BulletList items={scenario.hidden_information} empty="None defined" />
          </div>
        </div>
      </Section>

      <Section title="Learning objectives">
        {(scenario.learning_objectives ?? []).length === 0 ? (
          <p className="text-sm text-slate-500">None defined</p>
        ) : (
          <ul className="space-y-3 text-sm">
            {scenario.learning_objectives!.map((objective, i) => (
              <li key={i}>
                <p className="font-medium text-slate-800">{objective.name}</p>
                {objective.description && (
                  <p className="mt-1 text-slate-600">{objective.description}</p>
                )}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Feedback rubric">
        {(scenario.rubric_items ?? []).length === 0 ? (
          <p className="text-sm text-slate-500">No rubric categories defined.</p>
        ) : (
          <>
            <ul className="space-y-2 text-sm">
              {scenario.rubric_items!.map((item, i) => (
                <li key={i} className="rounded-lg bg-slate-50 px-3 py-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-800">{item.category}</span>
                    <span className="text-slate-500">
                      weight {item.weight} · max {item.max_score}
                    </span>
                  </div>
                  {item.description && (
                    <p className="mt-1 text-slate-600">{item.description}</p>
                  )}
                  {item.observable_indicators.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                        Observable indicators
                      </p>
                      <BulletList items={item.observable_indicators} />
                    </div>
                  )}
                  {item.common_mistakes.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                        Common mistakes
                      </p>
                      <BulletList items={item.common_mistakes} />
                    </div>
                  )}
                  {item.feedback_guidance && (
                    <Field label="Feedback guidance" value={item.feedback_guidance} />
                  )}
                  {item.optional_when_not_observable && (
                    <p className="mt-2 text-xs text-slate-500">
                      Optional when not observable in the session modality.
                    </p>
                  )}
                  {Object.keys(item.rating_anchors ?? {}).length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
                        Rating anchors
                      </p>
                      <dl className="mt-1 space-y-1">
                        {Object.entries(item.rating_anchors)
                          .sort(([a], [b]) => Number(b) - Number(a))
                          .map(([score, text]) => (
                            <div key={score} className="text-xs text-slate-600">
                              <dt className="inline font-semibold text-slate-700">
                                {score}:
                              </dt>{" "}
                              <dd className="inline">{text}</dd>
                            </div>
                          ))}
                      </dl>
                    </div>
                  )}
                </li>
              ))}
            </ul>
            <p
              className={`text-sm font-medium ${
                rubricTotal === 100 ? "text-emerald-600" : "text-amber-600"
              }`}
            >
              Total weight: {rubricTotal} / 100
            </p>
          </>
        )}
      </Section>

      <Section title="Evaluation guidance">
        <div className="grid gap-4 lg:grid-cols-2">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Competency scale
            </p>
            <div className="mt-1">
              <KeyValueList items={scenario.competency_scale as Record<string, unknown>[] | null} />
            </div>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Reflection questions
            </p>
            <div className="mt-1">
              <BulletList items={scenario.reflection_questions} />
            </div>
          </div>
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Evaluation focus sections
          </p>
          <div className="mt-1">
            <KeyValueList items={scenario.evaluation_focus_sections as Record<string, unknown>[] | null} />
          </div>
        </div>
      </Section>

      <Section title="Safety boundaries">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Additional disallowed topics
          </p>
          <div className="mt-1">
            <BulletList items={safety?.disallowed_topics} empty="None beyond defaults" />
          </div>
        </div>
        <Field label="Required redirection" value={safety?.required_redirection} />
        <Field label="Maximum emotional intensity" value={safety?.max_emotional_intensity} />
        <Field
          label="Required safety clarification"
          value={safety?.required_safety_clarification}
        />
        <div className="grid gap-4 lg:grid-cols-2">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Ambiguous safety phrases
            </p>
            <div className="mt-1">
              <BulletList items={safety?.ambiguous_safety_phrases} empty="None listed" />
            </div>
          </div>
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
              Faculty review triggers
            </p>
            <div className="mt-1">
              <BulletList items={safety?.safety_review_triggers} empty="None listed" />
            </div>
          </div>
        </div>
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-slate-500">
            Ending topics
          </p>
          <div className="mt-1">
            <BulletList items={safety?.ending_topics} empty="None listed" />
          </div>
        </div>
        <Field
          label="Crisis content allowed"
          value={safety?.crisis_content_allowed ? "Yes" : "No"}
        />
        <Field
          label="Faculty review required"
          value={safety?.faculty_review_required ? "Yes" : "No"}
        />
        <p className="rounded-lg bg-slate-50 p-3 text-xs text-slate-600">
          Default safety rules always apply: no crisis/self-harm/abuse content, no clinical advice,
          stay in character.
        </p>
      </Section>

      {scenario.generated_prompt && (
        <Section title="Generated client behavior">
          <div className="grid gap-3 text-sm sm:grid-cols-2">
            <Field label="Prompt version" value={scenario.prompt_version} />
            <Field label="Generated at" value={formatDate(scenario.prompt_generated_at)} />
          </div>
          <details className="group">
            <summary className="cursor-pointer text-sm font-medium text-navy-700 hover:underline">
              View generated prompt
            </summary>
            <pre className="mt-2 max-h-96 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-xs text-slate-700 ring-1 ring-slate-200">
              {scenario.generated_prompt}
            </pre>
          </details>
        </Section>
      )}
    </div>
  );
}

export default function FacultyScenarioDetailPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const [scenario, setScenario] = useState<FacultyScenarioDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!scenarioId) return;
    getFacultyScenario(scenarioId)
      .then(setScenario)
      .catch(() => setError("Could not load this scenario."));
  }, [scenarioId]);

  if (!scenarioId) {
    return (
      <Layout>
        <p className="py-20 text-center text-red-600">Scenario not found.</p>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <p className="py-20 text-center text-red-600">
          {error}{" "}
          <Link to="/faculty/scenarios" className="font-medium text-navy-600 hover:underline">
            Back to scenarios
          </Link>
        </p>
      </Layout>
    );
  }

  if (!scenario) {
    return (
      <Layout>
        <div className="flex justify-center py-20">
          <LoadingSpinner label="Loading scenario details..." />
        </div>
      </Layout>
    );
  }

  const isPublished = scenario.status === "published";
  const clientName = scenario.client_identity?.name ?? "\u2014";

  return (
    <Layout>
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link to="/faculty/scenarios" className="text-sm text-navy-600 hover:underline">
            &larr; Back to scenarios
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-navy-700">{scenario.title}</h1>
          <p className="mt-1 text-sm text-slate-500">
            Client: {clientName} &middot; {SCENARIO_STATUS_LABELS[scenario.status]}
            {scenario.published_at && (
              <> &middot; Published {formatDate(scenario.published_at)}</>
            )}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to={`/faculty/scenarios/${scenario.id}/preview`}
            className="rounded-lg border border-navy-700 px-4 py-2 text-sm font-medium text-navy-700 hover:bg-navy-50"
          >
            Preview &amp; Test
          </Link>
          {!isPublished && (
            <Link
              to={`/faculty/scenarios/${scenario.id}/edit`}
              className="rounded-lg bg-navy-700 px-4 py-2 text-sm font-medium text-white hover:bg-navy-800"
            >
              Edit
            </Link>
          )}
        </div>
      </div>

      <ScenarioDetailContent scenario={scenario} />
    </Layout>
  );
}
