import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import ScenarioCard from "../components/ScenarioCard";
import LoadingSpinner from "../components/LoadingSpinner";
import { listMySessions, listScenarios } from "../api/client";
import type { ScenarioSummary, StudentSessionSummary } from "../types";
import { STATUS_LABELS } from "../types";

export default function StudentDashboard() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[] | null>(null);
  const [attempts, setAttempts] = useState<StudentSessionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listScenarios()
      .then(setScenarios)
      .catch(() => setError("Could not load practice scenarios."));
    listMySessions()
      .then(setAttempts)
      .catch(() => setAttempts([]));
  }, []);

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-navy-700">Student Practice Dashboard</h1>
      <p className="mt-2 max-w-2xl text-slate-600">
        Choose a published scenario, complete a simulated counseling session, and receive
        practice feedback based on Module 1 microskills.
      </p>

      <section className="mt-8">
        <h2 className="text-lg font-semibold text-slate-800">Available Scenarios</h2>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
        {scenarios === null && !error && (
          <div className="mt-3">
            <LoadingSpinner label="Loading scenarios..." />
          </div>
        )}
        {scenarios && scenarios.length === 0 && (
          <p className="mt-3 rounded-xl bg-white p-6 text-sm text-slate-500 shadow-sm ring-1 ring-slate-200">
            No scenarios are available yet. Your instructor may still be preparing them.
          </p>
        )}
        {scenarios && scenarios.length > 0 && (
          <div className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {scenarios.map((scenario) => (
              <ScenarioCard key={scenario.id} scenario={scenario} />
            ))}
          </div>
        )}
      </section>

      <section className="mt-10">
        <h2 className="text-lg font-semibold text-slate-800">Previous Attempts</h2>
        {attempts === null ? (
          <div className="mt-3">
            <LoadingSpinner label="Loading attempts..." />
          </div>
        ) : attempts.length === 0 ? (
          <p className="mt-3 rounded-xl bg-white p-6 text-sm text-slate-500 shadow-sm ring-1 ring-slate-200">
            No previous attempts yet.
          </p>
        ) : (
          <ul className="mt-3 space-y-2">
            {attempts.map((a) => (
              <li
                key={a.session_id}
                className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-white px-5 py-4 text-sm shadow-sm ring-1 ring-slate-200"
              >
                <div>
                  <p className="font-medium text-slate-800">{a.scenario_title}</p>
                  <p className="text-xs text-slate-500">
                    {STATUS_LABELS[a.status]}
                    {" \u00b7 "}
                    {new Date(a.created_at).toLocaleString("en-US", {
                      dateStyle: "medium",
                      timeStyle: "short",
                    })}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  {a.overall_score != null && (
                    <span className="font-semibold text-navy-700">
                      {a.overall_score.toFixed(1)} / 5
                    </span>
                  )}
                  {a.overall_score != null && (
                    <Link
                      to={`/student/feedback/${a.session_id}`}
                      className="font-medium text-navy-600 hover:underline"
                    >
                      View Feedback
                    </Link>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </Layout>
  );
}
