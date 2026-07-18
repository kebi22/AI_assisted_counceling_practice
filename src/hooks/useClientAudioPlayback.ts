import { useCallback, useEffect, useRef, useState } from "react";

/** Reliable client TTS playback for voice/video sessions (handles browser autoplay rules). */
export function useClientAudioPlayback(clientAudioUrl: string | null) {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [callJoined, setCallJoined] = useState(false);

  const playAudio = useCallback(async () => {
    const el = audioRef.current;
    if (!el || !clientAudioUrl) return false;
    try {
      if (el.src !== clientAudioUrl) el.src = clientAudioUrl;
      el.currentTime = 0;
      await el.play();
      return true;
    } catch {
      return false;
    }
  }, [clientAudioUrl]);

  /** Run inside a click handler so the browser allows audio output. */
  const joinCall = useCallback(() => {
    void playAudio();
    setCallJoined(true);
  }, [playAudio]);

  // Auto-play later client replies once the student has joined.
  useEffect(() => {
    if (!callJoined || !clientAudioUrl || !audioRef.current) return;
    void audioRef.current.play().catch(() => undefined);
  }, [clientAudioUrl, callJoined]);

  return { audioRef, callJoined, joinCall, playAudio };
}
