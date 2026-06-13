import type { RubricScores } from "../types";
import { RUBRIC_LABELS } from "../types";

export default function RubricScoreTable({ scores }: { scores: RubricScores }) {
  return (
    <div className="overflow-x-auto rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-600">
          <tr>
            <th scope="col" className="px-4 py-3">Skill</th>
            <th scope="col" className="px-4 py-3 text-right">Score (1–5)</th>
            <th scope="col" className="px-4 py-3">Meaning</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {(Object.keys(RUBRIC_LABELS) as (keyof RubricScores)[]).map((key) => (
            <tr key={key}>
              <td className="px-4 py-3 font-medium text-slate-800">{RUBRIC_LABELS[key].label}</td>
              <td className="px-4 py-3 text-right font-semibold text-navy-700">
                {scores[key]} / 5
              </td>
              <td className="px-4 py-3 text-slate-600">{RUBRIC_LABELS[key].meaning}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
