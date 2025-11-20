"use client";

/**
 * Camera capture component for safety checks.
 */

import { useRef, useState, useEffect } from "react";

interface CameraCaptureProps {
  onCapture: (imageBase64: string) => void;
  disabled?: boolean;
}

export function CameraCapture({ onCapture, disabled }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [isActive, setIsActive] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      // Cleanup: stop stream when component unmounts
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [stream]);

  const startCamera = async () => {
    try {
      setError(null);
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });

      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }

      setStream(mediaStream);
      setIsActive(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to access camera");
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
    setIsActive(false);
  };

  const captureImage = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    if (!context) return;

    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw current video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert to base64
    const imageBase64 = canvas.toDataURL("image/jpeg").split(",")[1];

    onCapture(imageBase64);
    stopCamera();
  };

  return (
    <div className="space-y-4">
      {error && <div className="rounded-lg bg-red-50 p-3 text-sm text-red-800">{error}</div>}

      {!isActive ? (
        <button
          onClick={startCamera}
          disabled={disabled}
          className="w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
        >
          📷 Start Camera
        </button>
      ) : (
        <>
          <div className="relative overflow-hidden rounded-lg bg-black">
            <video ref={videoRef} autoPlay playsInline className="w-full" />
          </div>

          <div className="flex gap-2">
            <button
              onClick={captureImage}
              className="flex-1 rounded-lg bg-green-600 px-4 py-3 font-medium text-white hover:bg-green-700"
            >
              📸 Capture Image
            </button>
            <button
              onClick={stopCamera}
              className="rounded-lg border border-gray-300 px-4 py-3 font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </>
      )}

      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
}
