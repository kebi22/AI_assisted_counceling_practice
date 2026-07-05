import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import LoadingSpinner from "../components/LoadingSpinner";
import { listScenarioTemplates } from "../api/client";
import type { ScenarioTemplate } from "../types";

export default function ScenarioTemplatesPage() {
  const [templates, setTemplates] = useState<ScenarioTemplate[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listScenarioTemplates()
      .then(setTemplates)
      .catch(() => {
        setError("Could not load scenario templates.");
        setTemplates([]);
      });
  }, []);

  return (
    <Layout>
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <Link to="/faculty/scenarios" className="text-sm text-navy-600 hover:underline">
            &larr; Back to scenarios
          </Link>
          <h1 className="mt-1 text-2xl font-bold text-navy-700">Scenario Templates</h1>
          <p className="mt-1 max-w-3xl text-slate-600">
            Developer-owned template families define the prompt scaffold, state rules,
            disclosure policy, evaluator instructions, default rubric, and safety policy.
          </p>
        </div>
      </div>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      {templates === null ? (
        <div className="flex justify-center py-20">
          <LoadingSpinner label="Loading templates..." />
        </div>
      ) : (
        <div className="space-y-6">
          {templates.map((template) => (
            <TemplateCard key={template.key} template={template} />
          ))}
        </div>
      )}
    </Layout>
  );
}

function TemplateCard({ template }: { template: ScenarioTemplate }) {
  const content = template.content;
  return (
    <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold text-navy-700">{template.display_name}</h2>
          <p className="mt-1 text-sm text-slate-500">
            {template.key} · template v{template.version} · output schema v
            {template.output_schema_version}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {template.supported_modalities.map((modality) => (
            <span
              key={modality}
              className="rounded-full bg-teal-50 px-3 py-1 text-xs font-medium text-teal-700 ring-1 ring-teal-200"
            >
              {modality}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <TemplateSection
          title="Client Prompt Scaffold"
          value={content.client_prompt_scaffold}
        />
        <TemplateSection title="State Policy" value={content.state_policy} />
        <TemplateSection
          title="Module 1 Client Blueprint"
          value={content.module1_client_blueprint}
        />
        <TemplateSection title="Disclosure Policy" value={content.disclosure_policy} />
        <TemplateSection title="Competency Scale" value={content.competency_scale} />
        <TemplateSection
          title="Evaluation Focus Sections"
          value={content.evaluation_focus_sections}
        />
        <TemplateSection title="Reflection Questions" value={content.reflection_questions} />
        <TemplateSection title="Default Safety Policy" value={template.default_safety_policy} />
        <TemplateSection title="Default Rubric" value={template.default_rubric} />
      </div>

      <details className="mt-6">
        <summary className="cursor-pointer text-sm font-medium text-navy-700 hover:underline">
          View evaluator prompt
        </summary>
        <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-4 text-xs text-slate-700 ring-1 ring-slate-200">
          {String(content.evaluator_prompt ?? "")}
        </pre>
      </details>

      <details className="mt-4">
        <summary className="cursor-pointer text-sm font-medium text-slate-600 hover:underline">
          View raw template JSON
        </summary>
        <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap rounded-lg bg-slate-950 p-4 text-xs text-slate-100">
          {JSON.stringify(template, null, 2)}
        </pre>
      </details>
    </section>
  );
}

function TemplateSection({ title, value }: { title: string; value: unknown }) {
  return (
    <section className="rounded-lg bg-slate-50 p-4 ring-1 ring-slate-200">
      <h3 className="font-semibold text-slate-800">{title}</h3>
      <div className="mt-3 text-sm text-slate-700">{renderValue(value)}</div>
    </section>
  );
}

function renderValue(value: unknown): JSX.Element {
  if (value === null || value === undefined) {
    return <p className="text-slate-500">None</p>;
  }
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return <p>{String(value)}</p>;
  }
  if (Array.isArray(value)) {
    return (
      <ul className="list-inside list-disc space-y-1">
        {value.map((item, index) => (
          <li key={index}>{typeof item === "object" ? JSON.stringify(item) : String(item)}</li>
        ))}
      </ul>
    );
  }
  if (typeof value === "object") {
    return (
      <dl className="space-y-2">
        {Object.entries(value as Record<string, unknown>).map(([key, item]) => (
          <div key={key}>
            <dt className="text-xs font-medium uppercase tracking-wide text-slate-500">
              {humanizeKey(key)}
            </dt>
            <dd className="mt-0.5">{renderValue(item)}</dd>
          </div>
        ))}
      </dl>
    );
  }
  return <p>{String(value)}</p>;
}

function humanizeKey(key: string): string {
  return key
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
