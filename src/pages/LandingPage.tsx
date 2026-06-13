import { Link } from "react-router-dom";

export default function LandingPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 px-4">
      <div className="w-full max-w-lg rounded-2xl bg-white p-10 text-center shadow-md ring-1 ring-slate-200">
        <p className="text-xs font-semibold uppercase tracking-widest text-teal-600">
          Counseling Education
        </p>
        <h1 className="mt-3 text-3xl font-bold text-navy-700">
          AI-Assisted Counseling Simulator
        </h1>
        <p className="mt-3 text-slate-600">
          Practice counseling microskills through simulated client interactions
        </p>
        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Link
            to="/student"
            className="rounded-lg bg-navy-700 px-6 py-3 text-sm font-medium text-white hover:bg-navy-600"
          >
            Continue as Student
          </Link>
          <Link
            to="/faculty"
            className="rounded-lg border border-navy-700 px-6 py-3 text-sm font-medium text-navy-700 hover:bg-navy-50"
          >
            Continue as Faculty
          </Link>
        </div>
        <p className="mt-8 text-xs text-slate-400">
          Version 1 · Module 1: Advanced Microskills · Practice environment only
        </p>
      </div>
    </div>
  );
}
