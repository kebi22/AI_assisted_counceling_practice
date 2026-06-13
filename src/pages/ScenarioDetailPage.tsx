import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import { SCENARIO } from "../types";

export default function ScenarioDetailPage() {
  return (
    <Layout>
      <div className="mx-auto max-w-3xl">
        <h1 className="text-2xl font-bold text-navy-700">{SCENARIO.title}</h1>

        <div className="mt-6 space-y-5 rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <section>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Scenario
            </h2>
            <p className="mt-1 text-slate-700">{SCENARIO.description}</p>
          </section>

          <section>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              Your Goal
            </h2>
            <p className="mt-1 text-slate-700">{SCENARIO.goal}</p>
          </section>

          <section className="rounded-lg bg-amber-50 p-4 ring-1 ring-amber-200">
            <h2 className="text-sm font-semibold text-amber-800">Important Note</h2>
            <p className="mt-1 text-sm text-amber-900">{SCENARIO.disclaimer}</p>
          </section>
        </div>

        <div className="mt-6 flex flex-col gap-3 sm:flex-row">
          <Link
            to="/student/simulation"
            className="rounded-lg bg-navy-700 px-6 py-3 text-center text-sm font-medium text-white hover:bg-navy-600"
          >
            Begin Simulation
          </Link>
          <Link
            to="/student"
            className="rounded-lg border border-slate-300 px-6 py-3 text-center text-sm font-medium text-slate-700 hover:bg-white"
          >
            Back to Dashboard
          </Link>
        </div>
      </div>
    </Layout>
  );
}
