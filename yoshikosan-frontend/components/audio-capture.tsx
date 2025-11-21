"use client";

/**
 * Audio capture component for safety checks.
 */

import { useRef, useState, useEffect } from "react";
import MicRecorder from "mic-recorder-to-mp3";

interface AudioCaptureProps {
  onCapture: (audioBase64: string) => void;
  disabled?: boolean;
}

export function AudioCapture({ onCapture, disabled }: AudioCaptureProps) {
  const recorderRef = useRef<MicRecorder | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startedAtRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      // Cleanup on unmount: stop recording and timer
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (recorderRef.current) {
        recorderRef.current.stop().catch(() => {
          // Ignore stop errors during unmount
        });
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      setError(null);
      setRecordingTime(0);

      if (!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)) {
        setError("Microphone is not available in this browser.");
        return;
      }

      const recorder = new MicRecorder({
        bitRate: 128,
      });

      recorderRef.current = recorder;

      await recorder.start();
      console.log("🎤 Recorder started");

      startedAtRef.current = Date.now();
      setIsRecording(true);

      // Start timer directly here
      console.log("⏱️ Starting timer at:", startedAtRef.current);
      timerRef.current = setInterval(() => {
        if (!startedAtRef.current) {
          console.log("❌ No start time, skipping tick");
          return;
        }
        const elapsed = Math.max(
          0,
          Math.round((Date.now() - startedAtRef.current) / 1000)
        );
        console.log("⏱️ Timer tick - Elapsed:", elapsed, "seconds");
        setRecordingTime(elapsed);
      }, 1000);
      console.log("✅ Timer created:", timerRef.current);
    } catch (err) {
      console.error("Failed to start recording:", err);
      setError(err instanceof Error ? err.message : "Failed to access microphone.");
      setIsRecording(false);
    }
  };

  const stopRecording = async () => {
    if (!recorderRef.current || !isRecording) return;

    try {
      const [, blob] = await recorderRef.current.stop().getMp3();

      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      startedAtRef.current = null;

      if (!blob || blob.size === 0) {
        setError("No audio captured. Please check microphone permission and try again.");
        setRecordingTime(0);
        setIsRecording(false);
        return;
      }

      const reader = new FileReader();

      reader.onloadend = () => {
        const base64 = (reader.result as string).split(",")[1];
        onCapture(base64);
      };

      reader.readAsDataURL(blob);

      setRecordingTime(0);
      setIsRecording(false);
      recorderRef.current = null;
      startedAtRef.current = null;
    } catch (err) {
      console.error("Failed to stop recording:", err);
      setError(err instanceof Error ? err.message : "Failed to save recording. Please try again.");
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      setRecordingTime(0);
      setIsRecording(false);
      recorderRef.current = null;
      startedAtRef.current = null;
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="space-y-4">
      {error && <div className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{error}</div>}

      {!isRecording ? (
        <button
          onClick={startRecording}
          disabled={disabled}
          className="w-full rounded-lg bg-red-600 px-4 py-3 font-medium text-white hover:bg-red-700 disabled:bg-gray-400"
        >
          🎤 Start Recording
        </button>
      ) : (
        <>
          <div className="rounded-lg border-2 border-red-500 bg-red-50 p-6 text-center">
            <div className="mb-2 text-4xl">🔴</div>
            <div className="text-xl font-bold text-red-900">Recording...</div>
            <div className="mt-2 text-2xl font-mono text-red-700">{formatTime(recordingTime)}</div>
          </div>

          <button
            onClick={stopRecording}
            className="w-full rounded-lg bg-red-600 px-4 py-3 font-medium text-white hover:bg-red-700"
          >
            ⏹️ Stop Recording
          </button>
        </>
      )}
    </div>
  );
}
