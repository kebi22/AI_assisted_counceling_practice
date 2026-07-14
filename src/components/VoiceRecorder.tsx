import { useCallback, useEffect, useRef, useState } from "react";

interface Props {
  /** Called with the recorded audio once the student finishes a turn. */
  onRecorded: (audio: Blob) => void;
  /** Disable recording (e.g. while the client is responding). */
  disabled?: boolean;
}

type RecorderState = "idle" | "requesting" | "recording";

function pickMimeType(): string {
  const candidates = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
  for (const type of candidates) {
    if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(type)) {
      return type;
    }
  }
  return "";
}

/**
 * Push-to-talk recorder: hold the button (or press and hold) to record a turn,
 * release to send. Uses MediaRecorder; the resulting blob is uploaded as one
 * spoken student turn.
 */
export default function VoiceRecorder({ onRecorded, disabled = false }: Props) {
  const [state, setState] = useState<RecorderState>("idle");
  const [error, setError] = useState<string | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const stopStream = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
  }, []);

  useEffect(() => () => stopStream(), [stopStream]);

  const startRecording = useCallback(async () => {
    if (disabled || state !== "idle") return;
    setError(null);
    setState("requesting");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      const mimeType = pickMimeType();
      const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };
      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, {
          type: mimeType || "audio/webm",
        });
        stopStream();
        setState("idle");
        if (blob.size > 0) onRecorded(blob);
      };
      recorder.start();
      recorderRef.current = recorder;
      setState("recording");
    } catch {
      stopStream();
      setState("idle");
      setError("Microphone access was denied. Check your browser permissions.");
    }
  }, [disabled, state, onRecorded, stopStream]);

  const stopRecording = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      recorderRef.current.stop();
    }
  }, []);

  const isRecording = state === "recording";
  const label =
    state === "requesting"
      ? "Starting mic..."
      : isRecording
        ? "Recording... release to send"
        : "Hold to speak";

  return (
    <div className="flex flex-col items-center gap-1">
      <button
        type="button"
        disabled={disabled || state === "requesting"}
        onPointerDown={startRecording}
        onPointerUp={stopRecording}
        onPointerLeave={() => isRecording && stopRecording()}
        aria-pressed={isRecording}
        aria-label="Push to talk"
        className={
          isRecording
            ? "flex h-16 w-16 items-center justify-center rounded-full bg-red-600 text-white shadow-lg ring-4 ring-red-200 transition"
            : "flex h-16 w-16 items-center justify-center rounded-full bg-navy-700 text-white shadow-sm transition hover:bg-navy-600 disabled:opacity-50"
        }
      >
        <span aria-hidden="true" className="text-2xl">
          {isRecording ? "\u25A0" : "\uD83C\uDFA4"}
        </span>
      </button>
      <p className="text-xs text-slate-500" role="status" aria-live="polite">
        {label}
      </p>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
