import type { RubricCriterionScore, RubricScores } from "../types";
import { RUBRIC_LABELS } from "../types";

export default function RubricScoreTable({ scores }: { scores: RubricScores }) {
  const rows = Object.entries(scores).map(([key, value]) => {
    const score = normalizeScore(value);
    const fallback = RUBRIC_LABELS[key];
    return {
      key,
      score: score.score,
      maxScore: score.max_score,
      label: score.label || fallback?.label || humanizeKey(key),
      meaning: score.description || fallback?.meaning || "Scenario-specific criterion",
      feedback: score.feedback,
    };
  });

  return (
    <div className="overflow-x-auto rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-600">
          <tr>
            <th scope="col" className="px-4 py-3">Skill</th>
            <th scope="col" className="px-4 py-3 text-right">Score</th>
            <th scope="col" className="px-4 py-3">Meaning</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row) => (
            <tr key={row.key}>
              <td className="px-4 py-3 font-medium text-slate-800">{row.label}</td>
              <td className="px-4 py-3 text-right font-semibold text-navy-700">
                {row.score === null ? "N/A" : `${row.score} / ${row.maxScore}`}
              </td>
              <td className="px-4 py-3 text-slate-600">
                <p>{row.meaning}</p>
                {row.feedback && <p className="mt-1 text-xs text-slate-500">{row.feedback}</p>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function normalizeScore(value: RubricScores[string]): RubricCriterionScore {
  if (typeof value === "number") {
    return { score: value, max_score: 5 };
  }
  return {
    max_score: value.max_score ?? 5,
    ...value,
  };
}

function humanizeKey(key: string): string {
  return key
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
