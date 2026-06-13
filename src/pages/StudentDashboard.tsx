import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import ScenarioCard from "../components/ScenarioCard";
import { getCompletedSessions } from "../api/client";
import type { SessionRecord } from "../types";

export default function StudentDashboard() {
  const [attempts, setAttempts] = useState<SessionRecord[]>([]);

  useEffect(() => {
    getCompletedSessions().then(setAttempts);
  }, []);

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-navy-700">Student Practice Dashboard</h1>
      <p className="mt-2 max-w-2xl text-slate-600">
        Complete a simulated counseling session and receive practice feedback based on Module 1
        microskills.
      </p>

      <section className="mt-8">
        <h2 className="text-lg font-semibold text-slate-800">Available Scenario</h2>
        <div className="mt-3 max-w-xl">
          <ScenarioCard />
        </div>
      </section>

      <section className="mt-10">
        <h2 className="text-lg font-semibold text-slate-800">Previous Attempts</h2>
        {attempts.length === 0 ? (
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
                    {a.completed_at
                      ? new Date(a.completed_at).toLocaleString("en-US", {
                          dateStyle: "medium",
                          timeStyle: "short",
                        })
                      : ""}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  {a.evaluation && (
                    <span className="font-semibold text-navy-700">
                      {a.evaluation.overall_score.toFixed(1)} / 5
                    </span>
                  )}
                  <Link
                    to={`/student/feedback/${a.session_id}`}
                    className="font-medium text-navy-600 hover:underline"
                  >
                    View Feedback
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </Layout>
  );
}
