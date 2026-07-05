import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Layout from "../components/Layout";
import FeedbackScoreCard from "../components/FeedbackScoreCard";
import RubricScoreTable from "../components/RubricScoreTable";
import LoadingSpinner from "../components/LoadingSpinner";
import { getSession } from "../api/client";
import type { SessionDetail } from "../types";

export default function FeedbackReportPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [session, setSession] = useState<SessionDetail | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!sessionId) return;
    getSession(sessionId)
      .then((s) => {
        if (s.evaluation) setSession(s);
        else setNotFound(true);
      })
      .catch(() => setNotFound(true));
  }, [sessionId]);

  if (notFound) {
    return (
      <Layout>
        <p className="py-20 text-center text-slate-600">
          Feedback could not be found for this session.{" "}
          <Link to="/student" className="font-medium text-navy-600 hover:underline">
            Back to Student Dashboard
          </Link>
        </p>
      </Layout>
    );
  }

  if (!session || !session.evaluation) {
    return (
      <Layout>
        <div className="flex justify-center py-20">
          <LoadingSpinner label="Loading feedback report..." />
        </div>
      </Layout>
    );
  }

  const fb = session.evaluation;

  return (
    <Layout>
      <div className="mx-auto max-w-4xl space-y-8">
        <header>
          <h1 className="text-2xl font-bold text-navy-700">Session Feedback Report</h1>
          <p className="mt-1 text-slate-600">Module 1: Advanced Microskills</p>
        </header>

        <FeedbackScoreCard score={fb.overall_score} />

        <section>
          <h2 className="mb-3 text-lg font-semibold text-slate-800">Rubric Scores</h2>
          <RubricScoreTable scores={fb.rubric_scores} />
        </section>

        <div className="grid gap-6 md:grid-cols-2">
          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <h2 className="text-lg font-semibold text-emerald-700">Strengths</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-700">
              {fb.strengths.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </section>

          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <h2 className="text-lg font-semibold text-navy-700">Areas for Growth</h2>
            <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-700">
              {fb.areas_for_growth.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </section>
        </div>

        <section>
          <h2 className="mb-3 text-lg font-semibold text-slate-800">Evidence from Transcript</h2>
          <div className="space-y-3">
            {fb.evidence_from_transcript.map((e) => (
              <div key={e.quote} className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
                <blockquote className="border-l-4 border-navy-100 pl-3 text-sm italic text-slate-700">
                  Student: “{e.quote}”
                </blockquote>
                <p className="mt-2 text-sm text-slate-600">{e.feedback}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-xl bg-teal-50 p-6 ring-1 ring-teal-200">
          <h2 className="text-lg font-semibold text-teal-800">Suggested Improved Response</h2>
          <p className="mt-2 text-slate-800">“{fb.suggested_improved_response}”</p>
        </section>

        {fb.missed_opportunities && fb.missed_opportunities.length > 0 && (
          <section>
            <h2 className="mb-3 text-lg font-semibold text-slate-800">Missed Opportunities</h2>
            <div className="space-y-3">
              {fb.missed_opportunities.map((item, index) => (
                <div
                  key={index}
                  className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200"
                >
                  <dl className="space-y-2 text-sm">
                    {Object.entries(item).map(([key, value]) => (
                      <div key={key}>
                        <dt className="font-medium text-slate-700">{humanizeKey(key)}</dt>
                        <dd className="mt-1 text-slate-600">{formatAnalysisValue(value)}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              ))}
            </div>
          </section>
        )}

        {fb.specialized_analyses && Object.keys(fb.specialized_analyses).length > 0 && (
          <section>
            <h2 className="mb-3 text-lg font-semibold text-slate-800">Specialized Analyses</h2>
            <div className="grid gap-3 md:grid-cols-2">
              {Object.entries(fb.specialized_analyses).map(([key, value]) => (
                <div key={key} className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
                  <h3 className="font-semibold text-slate-800">{humanizeKey(key)}</h3>
                  <p className="mt-2 text-sm text-slate-600">{formatAnalysisValue(value)}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {fb.faculty_review_recommended && (
          <section className="rounded-xl bg-amber-50 p-5 text-sm text-amber-900 ring-1 ring-amber-200">
            Faculty review is recommended for this session.
          </section>
        )}

        <p className="text-xs text-slate-400">{fb.disclaimer}</p>

        <div className="flex flex-col gap-3 sm:flex-row">
          <Link
            to={`/student/scenario/${session.scenario_id}`}
            className="rounded-lg bg-navy-700 px-6 py-3 text-center text-sm font-medium text-white hover:bg-navy-600"
          >
            Retry Scenario
          </Link>
          <Link
            to="/student"
            className="rounded-lg border border-slate-300 px-6 py-3 text-center text-sm font-medium text-slate-700 hover:bg-white"
          >
            Back to Student Dashboard
          </Link>
        </div>
      </div>
    </Layout>
  );
}

function humanizeKey(key: string): string {
  return key
    .split("_")
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatAnalysisValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  if (Array.isArray(value)) {
    return value.map(formatAnalysisValue).join("; ");
  }
  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, item]) => `${humanizeKey(key)}: ${formatAnalysisValue(item)}`)
      .join("; ");
  }
  return String(value);
}
