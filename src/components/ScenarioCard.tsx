import { Link } from "react-router-dom";
import type { ScenarioSummary } from "../types";

interface Props {
  scenario: ScenarioSummary;
}

export default function ScenarioCard({ scenario }: Props) {
  return (
    <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-start justify-between gap-4">
        <h3 className="text-lg font-semibold text-navy-700">{scenario.title}</h3>
        <span className="shrink-0 rounded-full bg-teal-50 px-3 py-1 text-xs font-medium capitalize text-teal-700 ring-1 ring-teal-200">
          {scenario.difficulty}
        </span>
      </div>
      <dl className="mt-3 space-y-1 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Client</dt>
          <dd className="font-medium text-slate-800">{scenario.client_name}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Module</dt>
          <dd className="font-medium text-slate-800">{scenario.module_number}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-slate-500">Template</dt>
          <dd className="text-right font-medium text-slate-800">
            {scenario.template_version}
            {scenario.current_version_id ? ` · ${scenario.current_version_id.slice(0, 8)}` : ""}
          </dd>
        </div>
      </dl>
      <Link
        to={`/student/scenario/${scenario.id}`}
        className="mt-5 inline-block rounded-lg bg-navy-700 px-5 py-2.5 text-sm font-medium text-white hover:bg-navy-600"
      >
        View Scenario
      </Link>
    </div>
  );
}
