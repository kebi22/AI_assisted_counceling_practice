import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import Layout from "../components/Layout";
import LoadingSpinner from "../components/LoadingSpinner";
import {
  deactivateScenario,
  duplicateScenario,
  listFacultyScenarios,
} from "../api/client";
import type { FacultyScenarioSummary, ScenarioStatus } from "../types";
import { SCENARIO_STATUS_LABELS } from "../types";

const STATUS_STYLES: Record<ScenarioStatus, string> = {
  draft: "bg-slate-100 text-slate-600 ring-slate-200",
  ready_for_testing: "bg-amber-50 text-amber-700 ring-amber-200",
  published: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  inactive: "bg-slate-100 text-slate-400 ring-slate-200",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function FacultyScenariosPage() {
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState<FacultyScenarioSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const load = () => {
    listFacultyScenarios()
      .then(setScenarios)
      .catch(() => {
        setError("Could not load scenarios.");
        setScenarios([]);
      });
  };

  useEffect(load, []);

  const handleDuplicate = async (id: string) => {
    setBusyId(id);
    try {
      const copy = await duplicateScenario(id);
      navigate(`/faculty/scenarios/${copy.id}/edit`);
    } catch {
      setError("Could not duplicate the scenario.");
    } finally {
      setBusyId(null);
    }
  };

  const handleDeactivate = async (id: string) => {
    setBusyId(id);
    try {
      await deactivateScenario(id);
      load();
    } catch {
      setError("Could not deactivate the scenario.");
    } finally {
      setBusyId(null);
    }
  };

  return (
    <Layout>
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy-700">Scenarios</h1>
          <p className="mt-1 text-slate-600">
            Build, test, and publish practice clients for students.
          </p>
        </div>
        <Link
          to="/faculty/scenarios/new"
          className="rounded-lg bg-navy-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-navy-800"
        >
          + New Scenario
        </Link>
        <Link
          to="/faculty/scenario-templates"
          className="rounded-lg border border-slate-300 px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-white"
        >
          View Templates
        </Link>
      </div>

      {error && <p className="mt-4 text-sm text-red-600">{error}</p>}

      <div className="mt-6">
        {scenarios === null ? (
          <div className="flex justify-center py-16">
            <LoadingSpinner label="Loading scenarios..." />
          </div>
        ) : scenarios.length === 0 ? (
          <div className="rounded-xl bg-white p-8 text-center text-sm text-slate-500 shadow-sm ring-1 ring-slate-200">
            No scenarios yet. Create your first one to get started.
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Title</th>
                  <th className="px-4 py-3">Client</th>
                  <th className="px-4 py-3">Module</th>
                  <th className="px-4 py-3">Template</th>
                  <th className="px-4 py-3">Difficulty</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Updated</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {scenarios.map((s) => {
                  const isPublished = s.status === "published";
                  const busy = busyId === s.id;
                  return (
                    <tr key={s.id}>
                      <td className="px-4 py-3 font-medium text-slate-800">{s.title}</td>
                      <td className="px-4 py-3 text-slate-600">{s.client_name || "\u2014"}</td>
                      <td className="px-4 py-3 text-slate-600">{s.module_number}</td>
                      <td className="px-4 py-3 text-slate-600">
                        <div>{humanizeTemplate(s.template_key)}</div>
                        <div className="text-xs text-slate-400">
                          v{s.template_version}
                          {s.current_version_id ? ` · ${s.current_version_id.slice(0, 8)}` : ""}
                        </div>
                      </td>
                      <td className="px-4 py-3 capitalize text-slate-600">{s.difficulty}</td>
                      <td className="px-4 py-3">
                        <span
                          className={`rounded-full px-2.5 py-1 text-xs font-medium ring-1 ${STATUS_STYLES[s.status]}`}
                        >
                          {SCENARIO_STATUS_LABELS[s.status]}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-500">{formatDate(s.updated_at)}</td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap justify-end gap-3 text-sm font-medium">
                          <Link
                            to={`/faculty/scenarios/${s.id}`}
                            className="text-navy-700 hover:underline"
                          >
                            {isPublished ? "View details" : "Details"}
                          </Link>
                          {!isPublished && (
                            <Link
                              to={`/faculty/scenarios/${s.id}/edit`}
                              className="text-navy-700 hover:underline"
                            >
                              Edit
                            </Link>
                          )}
                          <Link
                            to={`/faculty/scenarios/${s.id}/preview`}
                            className="text-navy-700 hover:underline"
                          >
                            Preview &amp; Test
                          </Link>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => handleDuplicate(s.id)}
                            className="text-slate-600 hover:underline disabled:opacity-50"
                          >
                            Duplicate
                          </button>
                          {isPublished && (
                            <button
                              type="button"
                              disabled={busy}
                              onClick={() => handleDeactivate(s.id)}
                              className="text-red-600 hover:underline disabled:opacity-50"
                            >
                              Deactivate
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}

function humanizeTemplate(key: string): string {
  return key
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
