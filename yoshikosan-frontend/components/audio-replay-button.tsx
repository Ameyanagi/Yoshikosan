"use client";

import { Volume2 } from "lucide-react";
import { useRef, useState } from "react";
import { Button } from "./ui/button";

interface AudioReplayButtonProps {
  audioUrl: string;
  label?: string;
  variant?: "default" | "outline" | "ghost";
  size?: "default" | "sm" | "lg" | "icon";
  autoPlay?: boolean;
  onPlayStart?: () => void;
  onPlayEnd?: () => void;
}

/**
 * Audio replay button component for TTS feedback.
 * Allows workers to replay audio feedback in noisy environments.
 */
export function AudioReplayButton({
  audioUrl,
  label = "音声を再生",
  variant = "outline",
  size = "default",
  autoPlay = false,
  onPlayStart,
  onPlayEnd,
}: AudioReplayButtonProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasPlayed, setHasPlayed] = useState(false);

  const playAudio = async () => {
    if (!audioRef.current) {
      audioRef.current = new Audio(audioUrl);

      audioRef.current.addEventListener("play", () => {
        setIsPlaying(true);
        onPlayStart?.();
      });

      audioRef.current.addEventListener("ended", () => {
        setIsPlaying(false);
        setHasPlayed(true);
        onPlayEnd?.();
      });

      audioRef.current.addEventListener("pause", () => {
        setIsPlaying(false);
      });

      audioRef.current.addEventListener("error", (e) => {
        console.error("Audio playback error:", e);
        setIsPlaying(false);
      });
    }

    try {
      // Reset to beginning if already played
      audioRef.current.currentTime = 0;
      await audioRef.current.play();
    } catch (error) {
      console.error("Failed to play audio:", error);
      setIsPlaying(false);
    }
  };

  // Auto-play on mount if enabled
  useState(() => {
    if (autoPlay && !hasPlayed) {
      // Delay to ensure DOM is ready
      const timer = setTimeout(() => {
        playAudio();
      }, 100);
      return () => clearTimeout(timer);
    }
  });

  return (
    <Button
      variant={variant}
      size={size}
      onClick={playAudio}
      disabled={isPlaying}
      className="gap-2"
    >
      <Volume2 className={`h-4 w-4 ${isPlaying ? "animate-pulse" : ""}`} />
      {size !== "icon" && (isPlaying ? "再生中..." : label)}
    </Button>
  );
}
