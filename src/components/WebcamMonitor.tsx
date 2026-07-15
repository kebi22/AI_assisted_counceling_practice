import { useEffect, useRef, useState } from "react";
import { FaceLandmarker, FilesetResolver } from "@mediapipe/tasks-vision";
import type { NonverbalSummary } from "../types";

interface Props {
  /**
   * Called with the latest aggregated metrics (about once per second).
   * The parent keeps the most recent summary and submits it when the
   * session is completed. Raw video never leaves the browser.
   */
  onSummaryChange: (summary: NonverbalSummary) => void;
}

type TrackerState = "starting" | "tracking" | "camera-only" | "error";

// Keep the wasm runtime version in lockstep with the npm package version.
const WASM_CDN_URL =
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm";
const FACE_MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";

const SAMPLE_INTERVAL_MS = 250;
// Head-orientation thresholds (degrees) for the "facing the camera" proxy.
const FACING_MAX_YAW_DEG = 20;
const FACING_MAX_PITCH_DEG = 15;
const SMILE_THRESHOLD = 0.25;
const EXPRESSIVE_BLENDSHAPES = [
  "browInnerUp",
  "browOuterUpLeft",
  "browOuterUpRight",
  "mouthSmileLeft",
  "mouthSmileRight",
  "jawOpen",
  "eyeWideLeft",
  "eyeWideRight",
];

interface Accumulator {
  samples: number;
  faceSeen: number;
  facing: number;
  smiling: number;
  expressivenessSum: number;
  headMovementSum: number;
  startedAt: number;
}

function emptyAccumulator(): Accumulator {
  return {
    samples: 0,
    faceSeen: 0,
    facing: 0,
    smiling: 0,
    expressivenessSum: 0,
    headMovementSum: 0,
    startedAt: Date.now(),
  };
}

/** Extract approximate head yaw/pitch (degrees) from a column-major 4x4 matrix. */
function headAngles(matrixData: Float32Array | number[]): {
  yaw: number;
  pitch: number;
} {
  const d = matrixData;
  const clamp = (v: number) => Math.max(-1, Math.min(1, v));
  const yaw = (Math.asin(clamp(-d[2])) * 180) / Math.PI;
  const pitch = (Math.atan2(d[6], d[10]) * 180) / Math.PI;
  return { yaw, pitch };
}

function buildSummary(acc: Accumulator): NonverbalSummary {
  const faces = Math.max(1, acc.faceSeen);
  return {
    source: "mediapipe_face_landmarker",
    duration_seconds: Math.round((Date.now() - acc.startedAt) / 1000),
    sampled_frames: acc.samples,
    face_presence_ratio: acc.samples ? +(acc.faceSeen / acc.samples).toFixed(3) : 0,
    camera_facing_ratio: +(acc.facing / faces).toFixed(3),
    smile_ratio: +(acc.smiling / faces).toFixed(3),
    average_expressiveness: +(acc.expressivenessSum / faces).toFixed(3),
    average_head_movement_deg: +(acc.headMovementSum / faces).toFixed(1),
  };
}

/**
 * Webcam pane for video-mode sessions. Streams the student's camera locally
 * and runs MediaPipe FaceLandmarker in the browser (~4 samples/sec) to
 * aggregate nonverbal attending metrics: face presence, camera-facing head
 * orientation, smiling, and expressiveness. Only the aggregated summary is
 * reported upward; no frames or video are transmitted anywhere.
 */
export default function WebcamMonitor({ onSummaryChange }: Props) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [state, setState] = useState<TrackerState>("starting");
  const [error, setError] = useState<string | null>(null);
  const [liveSummary, setLiveSummary] = useState<NonverbalSummary | null>(null);
  const onSummaryChangeRef = useRef(onSummaryChange);
  onSummaryChangeRef.current = onSummaryChange;

  useEffect(() => {
    let cancelled = false;
    let stream: MediaStream | null = null;
    let landmarker: FaceLandmarker | null = null;
    let intervalId: number | null = null;
    const acc = emptyAccumulator();

    (async () => {
      // 1. Camera first: a preview without tracking is still useful.
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 480, height: 360, facingMode: "user" },
        });
      } catch {
        if (!cancelled) {
          setState("error");
          setError("Camera access was denied. Check your browser permissions.");
        }
        return;
      }
      if (cancelled || !videoRef.current) {
        stream.getTracks().forEach((t) => t.stop());
        return;
      }
      videoRef.current.srcObject = stream;
      await videoRef.current.play().catch(() => undefined);

      // 2. Load the face landmark model (network fetch; may fail offline).
      try {
        const fileset = await FilesetResolver.forVisionTasks(WASM_CDN_URL);
        landmarker = await FaceLandmarker.createFromOptions(fileset, {
          baseOptions: { modelAssetPath: FACE_MODEL_URL, delegate: "GPU" },
          runningMode: "VIDEO",
          numFaces: 1,
          outputFaceBlendshapes: true,
          outputFacialTransformationMatrixes: true,
        });
      } catch {
        if (!cancelled) {
          setState("camera-only");
          setError("Nonverbal tracking could not load; the camera preview still works.");
        }
        return;
      }
      if (cancelled) {
        landmarker.close();
        return;
      }
      setState("tracking");
      acc.startedAt = Date.now();

      // 3. Sample loop: detect, accumulate, and surface the running summary.
      intervalId = window.setInterval(() => {
        const video = videoRef.current;
        if (!video || video.readyState < 2 || !landmarker) return;
        let result;
        try {
          result = landmarker.detectForVideo(video, performance.now());
        } catch {
          return;
        }
        acc.samples += 1;

        const matrix = result.facialTransformationMatrixes?.[0]?.data;
        const blendshapes = result.faceBlendshapes?.[0]?.categories;
        if (matrix && blendshapes) {
          acc.faceSeen += 1;
          const { yaw, pitch } = headAngles(matrix);
          if (
            Math.abs(yaw) <= FACING_MAX_YAW_DEG &&
            Math.abs(pitch) <= FACING_MAX_PITCH_DEG
          ) {
            acc.facing += 1;
          }
          acc.headMovementSum += (Math.abs(yaw) + Math.abs(pitch)) / 2;

          const scores = new Map(blendshapes.map((c) => [c.categoryName, c.score]));
          const smile =
            ((scores.get("mouthSmileLeft") ?? 0) + (scores.get("mouthSmileRight") ?? 0)) / 2;
          if (smile >= SMILE_THRESHOLD) acc.smiling += 1;
          const expressiveness =
            EXPRESSIVE_BLENDSHAPES.reduce((sum, name) => sum + (scores.get(name) ?? 0), 0) /
            EXPRESSIVE_BLENDSHAPES.length;
          acc.expressivenessSum += expressiveness;
        }

        // Report roughly once per second.
        if (acc.samples % 4 === 0) {
          const summary = buildSummary(acc);
          setLiveSummary(summary);
          onSummaryChangeRef.current(summary);
        }
      }, SAMPLE_INTERVAL_MS);
    })();

    return () => {
      cancelled = true;
      if (intervalId !== null) window.clearInterval(intervalId);
      landmarker?.close();
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const statusLabel =
    state === "starting"
      ? "Starting camera..."
      : state === "tracking"
        ? "Camera on \u00b7 nonverbal tracking active"
        : state === "camera-only"
          ? "Camera on \u00b7 tracking unavailable"
          : "Camera unavailable";

  return (
    <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
      <h3 className="text-sm font-semibold text-slate-700">Your camera</h3>
      <div className="mt-3 overflow-hidden rounded-lg bg-slate-900">
        <video
          ref={videoRef}
          muted
          playsInline
          className="h-40 w-full object-cover"
          style={{ transform: "scaleX(-1)" }}
          aria-label="Your webcam preview (processed locally, never uploaded)"
        />
      </div>
      <p className="mt-2 text-xs text-slate-500" role="status" aria-live="polite">
        {statusLabel}
      </p>
      {error && <p className="mt-1 text-xs text-amber-700">{error}</p>}
      {state === "tracking" && liveSummary && (
        <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-slate-600">
          <div className="flex justify-between">
            <dt>Present</dt>
            <dd className="font-medium">{Math.round(liveSummary.face_presence_ratio * 100)}%</dd>
          </div>
          <div className="flex justify-between">
            <dt>Facing camera</dt>
            <dd className="font-medium">{Math.round(liveSummary.camera_facing_ratio * 100)}%</dd>
          </div>
        </dl>
      )}
      <p className="mt-2 text-[11px] leading-4 text-slate-400">
        Video is analyzed on your device only. Only aggregate attending metrics are
        saved with your session.
      </p>
    </div>
  );
}
