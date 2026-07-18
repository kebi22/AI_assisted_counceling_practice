import { useEffect, useRef, useState } from "react";
import { FaceLandmarker, FilesetResolver } from "@mediapipe/tasks-vision";
import type { NonverbalSummary } from "../types";

interface Props {
  onSummaryChange: (summary: NonverbalSummary) => void;
  /** pip = overlay tile on the video stage; panel = standalone card (unused in new layouts) */
  variant?: "pip" | "panel";
}

type TrackerState = "starting" | "tracking" | "camera-only" | "error";

const WASM_CDN_URL =
  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.35/wasm";
const FACE_MODEL_URL =
  "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task";

const SAMPLE_INTERVAL_MS = 250;
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

function headAngles(matrixData: Float32Array | number[]): { yaw: number; pitch: number } {
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

export default function WebcamMonitor({ onSummaryChange, variant = "pip" }: Props) {
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
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480, facingMode: "user" },
        });
      } catch {
        if (!cancelled) {
          setState("error");
          setError("Camera access denied");
        }
        return;
      }
      if (cancelled || !videoRef.current) {
        stream.getTracks().forEach((t) => t.stop());
        return;
      }
      videoRef.current.srcObject = stream;
      await videoRef.current.play().catch(() => undefined);

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
          setError("Tracking unavailable");
        }
        return;
      }
      if (cancelled) {
        landmarker.close();
        return;
      }
      setState("tracking");
      acc.startedAt = Date.now();

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

  const trackingActive = state === "tracking";
  const presencePct = liveSummary ? Math.round(liveSummary.face_presence_ratio * 100) : null;

  if (variant === "pip") {
    return (
      <div className="overflow-hidden rounded-xl bg-slate-900 shadow-2xl ring-2 ring-white/20">
        <div className="relative aspect-[4/3]">
          <video
            ref={videoRef}
            muted
            playsInline
            className="h-full w-full object-cover"
            style={{ transform: "scaleX(-1)" }}
            aria-label="Your camera (processed locally only)"
          />
          {state === "starting" && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 text-xs text-slate-300">
              Starting camera...
            </div>
          )}
          {state === "error" && (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-900 p-3 text-center text-xs text-red-300">
              {error}
            </div>
          )}
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent px-2 pb-2 pt-6">
            <p className="text-[11px] font-medium text-white">You</p>
            {trackingActive && presencePct !== null && (
              <p className="text-[10px] text-slate-300">Present {presencePct}%</p>
            )}
            {state === "camera-only" && (
              <p className="text-[10px] text-amber-300">Preview only</p>
            )}
          </div>
          {trackingActive && (
            <span className="absolute right-2 top-2 flex items-center gap-1 rounded-full bg-black/50 px-2 py-0.5 text-[10px] text-teal-300">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-teal-400" />
              Tracking
            </span>
          )}
        </div>
      </div>
    );
  }

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
          aria-label="Your webcam preview"
        />
      </div>
      {error && <p className="mt-2 text-xs text-amber-700">{error}</p>}
    </div>
  );
}
