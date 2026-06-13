import { Link } from "react-router-dom";
import { SCENARIO } from "../types";

export default function ScenarioCard() {
  return (
    <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-start justify-between gap-4">
        <h3 className="text-lg font-semibold text-navy-700">{SCENARIO.title}</h3>
        <span className="rounded-full bg-teal-50 px-3 py-1 text-xs font-medium text-teal-700 ring-1 ring-teal-200">
          Difficulty: {SCENARIO.difficulty}
        </span>
      </div>
      <p className="mt-2 text-sm font-medium text-slate-600">Focus skills</p>
      <ul className="mt-2 flex flex-wrap gap-2">
        {SCENARIO.skills.map((skill) => (
          <li
            key={skill}
            className="rounded-full bg-navy-50 px-3 py-1 text-xs font-medium text-navy-700"
          >
            {skill}
          </li>
        ))}
      </ul>
      <Link
        to="/student/scenario"
        className="mt-5 inline-block rounded-lg bg-navy-700 px-5 py-2.5 text-sm font-medium text-white hover:bg-navy-600"
      >
        Start Scenario
      </Link>
    </div>
  );
}
