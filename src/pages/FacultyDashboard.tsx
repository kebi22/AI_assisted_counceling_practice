import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import FacultySessionTable from "../components/FacultySessionTable";
import LoadingSpinner from "../components/LoadingSpinner";
import { listFacultySessions } from "../api/client";
import type { FacultySessionSummary } from "../types";

export default function FacultyDashboard() {
  const [sessions, setSessions] = useState<FacultySessionSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listFacultySessions()
      .then(setSessions)
      .catch(() => {
        setError("Could not load sessions.");
        setSessions([]);
      });
  }, []);

  return (
    <Layout>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-navy-700">Faculty Dashboard</h1>
          <p className="mt-2 max-w-2xl text-slate-600">
            Review student simulation attempts, AI-generated feedback, and rubric scores.
          </p>
        </div>
        <Link
          to="/faculty/scenarios"
          className="shrink-0 rounded-lg bg-navy-700 px-4 py-2.5 text-sm font-medium text-white hover:bg-navy-800"
        >
          Manage Scenarios
        </Link>
      </div>

      {/* Filter placeholders; non-functional in Version 1 */}
      <div className="mt-6 flex flex-wrap gap-3">
        <select
          aria-label="Filter by scenario"
          disabled
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-500"
        >
          <option>All scenarios</option>
        </select>
        <select
          aria-label="Filter by score range"
          disabled
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-500"
        >
          <option>All score ranges</option>
        </select>
        <select
          aria-label="Filter by review status"
          disabled
          className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-500"
        >
          <option>All statuses</option>
        </select>
      </div>

      <div className="mt-6">
        {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
        {sessions === null ? (
          <div className="flex justify-center py-16">
            <LoadingSpinner label="Loading sessions..." />
          </div>
        ) : (
          <FacultySessionTable sessions={sessions} />
        )}
      </div>
    </Layout>
  );
}
