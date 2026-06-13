import { useEffect, useState } from "react";
import Layout from "../components/Layout";
import FacultySessionTable from "../components/FacultySessionTable";
import LoadingSpinner from "../components/LoadingSpinner";
import { getCompletedSessions } from "../api/client";
import type { SessionRecord } from "../types";

export default function FacultyDashboard() {
  const [sessions, setSessions] = useState<SessionRecord[] | null>(null);

  useEffect(() => {
    getCompletedSessions().then(setSessions);
  }, []);

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-navy-700">Faculty Dashboard</h1>
      <p className="mt-2 max-w-2xl text-slate-600">
        Review student simulation attempts, AI-generated feedback, and rubric scores.
      </p>

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
