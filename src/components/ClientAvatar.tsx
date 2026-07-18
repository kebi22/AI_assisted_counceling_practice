import { useEffect, useRef, useState } from "react";
import type { RefObject } from "react";

interface Props {
  clientName: string;
  audioRef: RefObject<HTMLAudioElement | null>;
  audioUrl: string | null;
  /** hero = centered call view; inline = compact row (legacy) */
  variant?: "hero" | "inline";
}

function AvatarFace({
  speaking,
  blink,
  mouthRef,
  sizeClass,
}: {
  speaking: boolean;
  blink: boolean;
  mouthRef: RefObject<SVGEllipseElement | null>;
  sizeClass: string;
}) {
  return (
    <div
      className={`relative shrink-0 overflow-hidden rounded-full ring-2 transition-shadow ${sizeClass} ${
        speaking ? "ring-teal-400 shadow-[0_0_24px_rgba(45,212,191,0.45)]" : "ring-white/20"
      }`}
      aria-hidden="true"
    >
      <svg viewBox="0 0 120 120" className="h-full w-full">
        <rect width="120" height="120" fill="#dbeafe" />
        <circle cx="60" cy="64" r="42" fill="#f5c9a2" />
        <path d="M 18 62 A 42 42 0 0 1 102 62 L 102 50 A 44 46 0 0 0 18 50 Z" fill="#4a3626" />
        <circle cx="18" cy="66" r="6" fill="#f0bd93" />
        <circle cx="102" cy="66" r="6" fill="#f0bd93" />
        <path d="M 36 48 Q 44 44 52 48" stroke="#4a3626" strokeWidth="2.5" fill="none" strokeLinecap="round" />
        <path d="M 68 48 Q 76 44 84 48" stroke="#4a3626" strokeWidth="2.5" fill="none" strokeLinecap="round" />
        <g transform={`translate(44 58) scale(1 ${blink ? 0.1 : 1})`}>
          <ellipse rx="4" ry="5" fill="#2b2b2b" />
        </g>
        <g transform={`translate(76 58) scale(1 ${blink ? 0.1 : 1})`}>
          <ellipse rx="4" ry="5" fill="#2b2b2b" />
        </g>
        <path d="M 60 62 Q 57 72 60 74" stroke="#d9a97e" strokeWidth="2" fill="none" strokeLinecap="round" />
        <ellipse ref={mouthRef} cx="60" cy="86" rx="11" ry="1.5" fill="#8c3b3b" />
      </svg>
    </div>
  );
}

/**
 * Animated talking-head avatar for the simulated client.
 * Lip-sync is driven by a Web Audio analyser on the TTS playback element.
 */
export default function ClientAvatar({
  clientName,
  audioRef,
  audioUrl,
  variant = "hero",
}: Props) {
  const [speaking, setSpeaking] = useState(false);
  const [blink, setBlink] = useState(false);
  const mouthRef = useRef<SVGEllipseElement>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    let closeTimer: number;
    let openTimer: number;
    const scheduleBlink = () => {
      closeTimer = window.setTimeout(() => {
        setBlink(true);
        openTimer = window.setTimeout(() => {
          setBlink(false);
          scheduleBlink();
        }, 140);
      }, 2500 + Math.random() * 3000);
    };
    scheduleBlink();
    return () => {
      window.clearTimeout(closeTimer);
      window.clearTimeout(openTimer);
    };
  }, []);

  useEffect(() => {
    const el = audioRef.current;
    if (!el || !audioUrl) return;

    const ensureGraph = () => {
      if (audioCtxRef.current) return;
      const AudioCtx =
        window.AudioContext ??
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new AudioCtx();
      const source = ctx.createMediaElementSource(el);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 512;
      analyser.smoothingTimeConstant = 0.6;
      source.connect(analyser);
      analyser.connect(ctx.destination);
      audioCtxRef.current = ctx;
      analyserRef.current = analyser;
    };

    const buffer = new Uint8Array(512);

    const animate = () => {
      const analyser = analyserRef.current;
      if (analyser && mouthRef.current) {
        analyser.getByteTimeDomainData(buffer);
        let sumSquares = 0;
        for (let i = 0; i < buffer.length; i += 1) {
          const centered = (buffer[i] - 128) / 128;
          sumSquares += centered * centered;
        }
        const rms = Math.sqrt(sumSquares / buffer.length);
        const openness = 1.5 + Math.min(1, rms * 4) * 9;
        mouthRef.current.setAttribute("ry", openness.toFixed(2));
      }
      rafRef.current = requestAnimationFrame(animate);
    };

    const handlePlay = () => {
      ensureGraph();
      void audioCtxRef.current?.resume();
      setSpeaking(true);
      cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(animate);
    };
    const handleStop = () => {
      setSpeaking(false);
      cancelAnimationFrame(rafRef.current);
      mouthRef.current?.setAttribute("ry", "1.5");
    };

    el.addEventListener("play", handlePlay);
    el.addEventListener("pause", handleStop);
    el.addEventListener("ended", handleStop);
    if (!el.paused) handlePlay();

    return () => {
      el.removeEventListener("play", handlePlay);
      el.removeEventListener("pause", handleStop);
      el.removeEventListener("ended", handleStop);
      cancelAnimationFrame(rafRef.current);
    };
  }, [audioRef, audioUrl]);

  useEffect(
    () => () => {
      void audioCtxRef.current?.close();
    },
    [],
  );

  const sizeClass = variant === "hero" ? "h-36 w-36 sm:h-44 sm:w-44 lg:h-52 lg:w-52" : "h-20 w-20";

  if (variant === "inline") {
    return (
      <div className="flex items-center gap-4 bg-gradient-to-r from-navy-800 to-navy-700 px-4 py-3">
        <AvatarFace speaking={speaking} blink={blink} mouthRef={mouthRef} sizeClass={sizeClass} />
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold text-white">{clientName}</p>
          <p className="text-xs text-navy-100" role="status" aria-live="polite">
            {speaking ? "Speaking..." : "Listening"}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-4 text-center">
      <AvatarFace speaking={speaking} blink={blink} mouthRef={mouthRef} sizeClass={sizeClass} />
      <div>
        <p className="text-lg font-semibold text-white sm:text-xl">{clientName}</p>
        <p className="mt-1 text-sm text-slate-300" role="status" aria-live="polite">
          {speaking ? "Speaking..." : isLoadingLabel(speaking, audioUrl)}
        </p>
        {speaking && (
          <div className="mt-3 flex items-end justify-center gap-1" aria-hidden="true">
            {[0, 1, 2, 3, 4, 5].map((i) => (
              <span
                key={i}
                className="w-1 animate-pulse rounded-full bg-teal-400"
                style={{ height: `${8 + (i % 3) * 6}px`, animationDelay: `${i * 100}ms` }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function isLoadingLabel(speaking: boolean, audioUrl: string | null): string {
  if (speaking) return "Speaking...";
  return audioUrl ? "Listening" : "Waiting for you";
}
