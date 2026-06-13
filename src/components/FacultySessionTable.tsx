import { Link } from "react-router-dom";
import type { SessionRecord } from "../types";

function formatDate(iso: string) {
  if (!iso) return "\u2014";
  return new Date(iso).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
}

export default function FacultySessionTable({ sessions }: { sessions: SessionRecord[] }) {
  if (sessions.length === 0) {
    return (
      <div className="rounded-xl bg-white p-8 text-center text-sm text-slate-500 shadow-sm ring-1 ring-slate-200">
        No completed student sessions yet.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-600">
          <tr>
            <th scope="col" className="px-4 py-3">Student</th>
            <th scope="col" className="px-4 py-3">Scenario</th>
            <th scope="col" className="px-4 py-3">Date</th>
            <th scope="col" className="px-4 py-3 text-right">Overall Score</th>
            <th scope="col" className="px-4 py-3">Status</th>
            <th scope="col" className="px-4 py-3">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {sessions.map((s) => (
            <tr key={s.session_id}>
              <td className="px-4 py-3 font-medium text-slate-800">{s.student_name}</td>
              <td className="px-4 py-3 text-slate-600">{s.scenario_title}</td>
              <td className="px-4 py-3 text-slate-600">{formatDate(s.completed_at)}</td>
              <td className="px-4 py-3 text-right font-semibold text-navy-700">
                {s.evaluation ? `${s.evaluation.overall_score.toFixed(1)} / 5` : "\u2014"}
              </td>
              <td className="px-4 py-3">
                <span
                  className={
                    s.status === "Reviewed"
                      ? "rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700 ring-1 ring-emerald-200"
                      : "rounded-full bg-amber-50 px-2.5 py-1 text-xs font-medium text-amber-700 ring-1 ring-amber-200"
                  }
                >
                  {s.status}
                </span>
              </td>
              <td className="px-4 py-3">
                <Link
                  to={`/faculty/sessions/${s.session_id}`}
                  className="font-medium text-navy-600 hover:underline"
                >
                  Review
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
