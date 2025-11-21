"use client";

/**
 * Photo upload component - debug mode alternative to camera capture.
 * Allows uploading photos from filesystem for testing and accessibility.
 */

import { useRef, useState, type ChangeEvent } from "react";

interface PhotoUploadProps {
  onCapture: (imageBase64: string) => void;
  disabled?: boolean;
}

export function PhotoUpload({ onCapture, disabled }: PhotoUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith("image/")) {
      setError("Please select an image file (JPEG, PNG, etc.)");
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError("File size must be less than 10MB");
      return;
    }

    setError(null);

    try {
      // Read file as data URL
      const reader = new FileReader();

      reader.onloadend = () => {
        const dataUrl = reader.result as string;
        // Extract base64 part (remove "data:image/jpeg;base64," prefix)
        const base64 = dataUrl.split(",")[1];

        // Set preview
        setPreview(dataUrl);

        // Call callback with base64 data
        onCapture(base64);
      };

      reader.onerror = () => {
        setError("Failed to read file");
      };

      reader.readAsDataURL(file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload photo");
    }
  };

  const handleClear = () => {
    setPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-800">
          {error}
        </div>
      )}

      {!preview ? (
        <>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            disabled={disabled}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            className="w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
          >
            📁 Upload Photo (Debug)
          </button>
          <p className="text-center text-xs text-gray-500">
            Upload a photo from your filesystem instead of using the camera
          </p>
        </>
      ) : (
        <>
          <div className="overflow-hidden rounded-lg border-2 border-green-500 bg-gray-50">
            <img
              src={preview}
              alt="Uploaded preview"
              className="h-auto w-full object-cover"
              style={{ maxHeight: "300px" }}
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleClear}
              className="flex-1 rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50"
            >
              Clear
            </button>
            <div className="flex-1 rounded-lg bg-green-100 px-4 py-2 text-center font-medium text-green-800">
              ✓ Photo Uploaded
            </div>
          </div>
        </>
      )}
    </div>
  );
}
