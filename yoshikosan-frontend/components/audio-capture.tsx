"use client";

/**
 * Audio capture component for safety checks.
 */

import { useRef, useState, useEffect } from "react";

interface AudioCaptureProps {
  onCapture: (audioBase64: string) => void;
  disabled?: boolean;
}

export function AudioCapture({ onCapture, disabled }: AudioCaptureProps) {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      // Cleanup: stop recording and timer when component unmounts
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop();
      }
    };
  }, [isRecording]);

  const startRecording = async () => {
    try {
      setError(null);
      chunksRef.current = [];

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
        const reader = new FileReader();

        reader.onloadend = () => {
          const base64 = (reader.result as string).split(",")[1];
          onCapture(base64);
        };

        reader.readAsDataURL(audioBlob);

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());

        // Clear timer
        if (timerRef.current) {
          clearInterval(timerRef.current);
        }
        setRecordingTime(0);
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to access microphone");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
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
