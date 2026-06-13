import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import Layout from "../components/Layout";
import TranscriptViewer from "../components/TranscriptViewer";
import FeedbackScoreCard from "../components/FeedbackScoreCard";
import RubricScoreTable from "../components/RubricScoreTable";
import LoadingSpinner from "../components/LoadingSpinner";
import { getSession, saveFacultyReview } from "../api/client";
import type { SessionRecord } from "../types";

export default function FacultySessionReviewPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [session, setSession] = useState<SessionRecord | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [comment, setComment] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveNote, setSaveNote] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    getSession(sessionId).then((s) => {
      if (s) {
        setSession(s);
        setComment(s.faculty_comment);
      } else {
        setNotFound(true);
      }
    });
  }, [sessionId]);

  const handleSave = async (markReviewed: boolean) => {
    if (!sessionId) return;
    setSaving(true);
    setSaveNote(null);
    const updated = await saveFacultyReview(sessionId, comment, markReviewed);
    if (updated) {
      setSession(updated);
      setSaveNote(markReviewed ? "Session marked as reviewed." : "Comment saved.");
    }
    setSaving(false);
  };

  if (notFound) {
    return (
      <Layout>
        <p className="py-20 text-center text-slate-600">
          Session not found.{" "}
          <Link to="/faculty" className="font-medium text-navy-600 hover:underline">
            Back to Faculty Dashboard
          </Link>
        </p>
      </Layout>
    );
  }

  if (!session) {
    return (
      <Layout>
        <div className="flex justify-center py-20">
          <LoadingSpinner label="Loading session..." />
        </div>
      </Layout>
    );
  }

  const fb = session.evaluation;

  return (
    <Layout>
      <div className="mx-auto max-w-4xl space-y-8">
        <header className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold text-navy-700">Session Review</h1>
            <p className="mt-1 text-slate-600">{session.scenario_title}</p>
          </div>
          <Link to="/faculty" className="text-sm font-medium text-navy-600 hover:underline">
            Back to Faculty Dashboard
          </Link>
        </header>

        <section className="grid gap-4 rounded-xl bg-white p-6 text-sm shadow-sm ring-1 ring-slate-200 sm:grid-cols-2 lg:grid-cols-4">
          <div>
            <p className="text-slate-500">Student</p>
            <p className="font-medium text-slate-800">{session.student_name}</p>
          </div>
          <div>
            <p className="text-slate-500">Date completed</p>
            <p className="font-medium text-slate-800">
              {session.completed_at
                ? new Date(session.completed_at).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })
                : "—"}
            </p>
          </div>
          <div>
            <p className="text-slate-500">Overall score</p>
            <p className="font-medium text-slate-800">
              {fb ? `${fb.overall_score.toFixed(1)} / 5` : "—"}
            </p>
          </div>
          <div>
            <p className="text-slate-500">Status</p>
            <p className="font-medium text-slate-800">{session.status}</p>
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold text-slate-800">Transcript</h2>
          <TranscriptViewer messages={session.messages} />
        </section>

        {fb && (
          <section className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-800">AI Feedback</h2>
            <FeedbackScoreCard score={fb.overall_score} />
            <RubricScoreTable scores={fb.rubric_scores} />
            <div className="grid gap-6 md:grid-cols-2">
              <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
                <h3 className="font-semibold text-emerald-700">Strengths</h3>
                <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-700">
                  {fb.strengths.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              </div>
              <div className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
                <h3 className="font-semibold text-navy-700">Areas for Growth</h3>
                <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-700">
                  {fb.areas_for_growth.map((s) => (
                    <li key={s}>{s}</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="rounded-xl bg-teal-50 p-6 ring-1 ring-teal-200">
              <h3 className="font-semibold text-teal-800">Suggested Improved Response</h3>
              <p className="mt-2 text-slate-800">“{fb.suggested_improved_response}”</p>
            </div>
          </section>
        )}

        <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <label htmlFor="faculty-comment" className="text-lg font-semibold text-slate-800">
            Faculty comments
          </label>
          <textarea
            id="faculty-comment"
            rows={4}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="Add notes for this student session..."
            className="mt-3 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-navy-600 focus:outline-none focus:ring-1 focus:ring-navy-600"
          />
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => handleSave(false)}
              disabled={saving}
              className="rounded-lg bg-navy-700 px-5 py-2.5 text-sm font-medium text-white hover:bg-navy-600 disabled:opacity-50"
            >
              Save Comment
            </button>
            <button
              type="button"
              onClick={() => handleSave(true)}
              disabled={saving || session.status === "Reviewed"}
              className="rounded-lg border border-navy-700 px-5 py-2.5 text-sm font-medium text-navy-700 hover:bg-navy-50 disabled:opacity-50"
            >
              {session.status === "Reviewed" ? "Reviewed" : "Mark Reviewed"}
            </button>
            {saveNote && (
              <span className="text-sm text-emerald-700" role="status">
                {saveNote}
              </span>
            )}
          </div>
        </section>
      </div>
    </Layout>
  );
}
