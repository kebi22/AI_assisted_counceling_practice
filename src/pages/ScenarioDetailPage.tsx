import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Layout from "../components/Layout";
import LoadingSpinner from "../components/LoadingSpinner";
import { getScenario } from "../api/client";
import type { Modality, ScenarioDetail } from "../types";
import { MODALITY_LABELS } from "../types";

const MODALITY_OPTIONS: { value: Modality; hint: string }[] = [
  { value: "text", hint: "Type your responses in a chat window." },
  { value: "audio", hint: "Speak your responses; the client replies out loud." },
  { value: "video", hint: "Speak with your webcam on for nonverbal feedback." },
];

const PRACTICE_DISCLAIMER =
  "This is a practice simulation. AI-generated feedback is for learning support and should not be treated as a final clinical evaluation.";

export default function ScenarioDetailPage() {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [modality, setModality] = useState<Modality>("text");

  useEffect(() => {
    if (!scenarioId) return;
    getScenario(scenarioId)
      .then(setScenario)
      .catch(() => setError("Could not load this scenario."));
  }, [scenarioId]);

  if (error) {
    return (
      <Layout>
        <p className="py-20 text-center text-red-600">
          {error}{" "}
          <Link to="/student" className="font-medium text-navy-600 hover:underline">
            Back to dashboard
          </Link>
        </p>
      </Layout>
    );
  }

  if (!scenario) {
    return (
      <Layout>
        <div className="flex justify-center py-20">
          <LoadingSpinner label="Loading scenario..." />
        </div>
      </Layout>
    );
  }

  const skills = (scenario.client_profile as { skills?: unknown }).skills;
  const focusSkills = Array.isArray(skills)
    ? skills.filter((s): s is string => typeof s === "string")
    : Object.entries(scenario.rubric_json).map(([key, value]) => rubricLabel(key, value));

  return (
    <Layout>
      <div className="mx-auto max-w-3xl">
        <Link to="/student" className="text-sm text-navy-600 hover:underline">
          &larr; All scenarios
        </Link>
        <h1 className="mt-2 text-2xl font-bold text-navy-700">{scenario.title}</h1>
        <p className="mt-1 text-sm text-slate-500">
          Client: {scenario.client_name} &middot; Module {scenario.module_number} &middot;{" "}
          <span className="capitalize">{scenario.difficulty}</span>
        </p>
        <p className="mt-1 text-xs text-slate-500">
          Template: {scenario.template_key} v{scenario.template_version}
          {scenario.current_version_id ? ` · Version ${scenario.current_version_id.slice(0, 8)}` : ""}
        </p>

        <div className="mt-6 space-y-5 rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <section>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Scenario
            </h2>
            <p className="mt-1 text-slate-700">{scenario.description}</p>
          </section>

          <section>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Your Goal
            </h2>
            <p className="mt-1 text-slate-700">{scenario.student_goal}</p>
          </section>

          {focusSkills.length > 0 && (
            <section>
              <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Focus Skills
              </h2>
              <ul className="mt-2 flex flex-wrap gap-2">
                {focusSkills.map((skill) => (
                  <li
                    key={skill}
                    className="rounded-full bg-navy-50 px-3 py-1 text-xs font-medium text-navy-700"
                  >
                    {skill}
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Practice Mode
            </h2>
            <div className="mt-2 grid gap-2 sm:grid-cols-3">
              {MODALITY_OPTIONS.map((option) => {
                const selected = modality === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setModality(option.value)}
                    aria-pressed={selected}
                    className={
                      selected
                        ? "rounded-lg border-2 border-navy-600 bg-navy-50 p-3 text-left"
                        : "rounded-lg border border-slate-300 p-3 text-left hover:border-navy-400"
                    }
                  >
                    <span className="block text-sm font-medium text-navy-700">
                      {MODALITY_LABELS[option.value]}
                    </span>
                    <span className="mt-1 block text-xs text-slate-500">{option.hint}</span>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="rounded-lg bg-amber-50 p-4 ring-1 ring-amber-200">
            <h2 className="text-sm font-semibold text-amber-800">Important Note</h2>
            <p className="mt-1 text-sm text-amber-900">{PRACTICE_DISCLAIMER}</p>
          </section>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <Link
            to={`/student/simulation/${scenario.id}?mode=${modality}`}
            className="rounded-lg bg-navy-700 px-6 py-3 text-center text-sm font-medium text-white hover:bg-navy-600"
          >
            Begin Simulation
          </Link>
          <Link
            to="/student"
            className="rounded-lg border border-slate-300 px-6 py-3 text-center text-sm font-medium text-slate-700 hover:bg-white"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>
    </Layout>
  );
}

function rubricLabel(key: string, value: unknown): string {
  if (typeof value === "string") return value;
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    if (typeof record.label === "string" && record.label.trim()) return record.label;
    if (typeof record.description === "string" && record.description.trim()) {
      return record.description;
    }
  }
  return key
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
