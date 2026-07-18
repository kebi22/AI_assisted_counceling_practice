interface Props {
  clientName: string;
  onJoin: () => void;
}

/** One-click gate so the browser allows Sara's opening TTS to play. */
export default function JoinCallOverlay({ clientName, onJoin }: Props) {
  return (
    <div className="absolute inset-0 z-20 flex items-center justify-center bg-navy-950/80 backdrop-blur-sm">
      <div className="mx-4 max-w-sm rounded-2xl bg-white p-6 text-center shadow-xl">
        <p className="text-sm font-medium text-teal-600">Session ready</p>
        <h2 className="mt-1 text-lg font-semibold text-navy-800">Join your call with {clientName}</h2>
        <p className="mt-2 text-sm text-slate-600">
          {clientName} will introduce the session. Click below to start and hear their opening.
        </p>
        <button
          type="button"
          onClick={onJoin}
          className="mt-5 w-full rounded-full bg-navy-700 px-6 py-3 text-sm font-semibold text-white hover:bg-navy-600"
        >
          Join call
        </button>
      </div>
    </div>
  );
}
