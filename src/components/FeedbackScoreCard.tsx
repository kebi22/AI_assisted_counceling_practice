export default function FeedbackScoreCard({ score }: { score: number }) {
  return (
    <div className="rounded-xl bg-navy-700 p-6 text-center text-white shadow-sm">
      <p className="text-sm font-medium uppercase tracking-wide text-navy-100">Overall Score</p>
      <p className="mt-1 text-5xl font-bold">
        {score.toFixed(1)} <span className="text-2xl font-normal text-navy-100">/ 5</span>
      </p>
    </div>
  );
}
