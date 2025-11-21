"use client";

/**
 * Text confirmation component - debug mode alternative to audio recording.
 * Allows typing confirmation text for testing and accessibility.
 */

import { useState, type ChangeEvent } from "react";

interface TextConfirmationProps {
  onCapture: (text: string) => void;
  disabled?: boolean;
}

export function TextConfirmation({ onCapture, disabled }: TextConfirmationProps) {
  const [text, setText] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setText(e.target.value);
    setSubmitted(false);
    setError(null);
  };

  const handleSubmit = () => {
    if (!text.trim()) {
      setError("Please enter a confirmation message");
      return;
    }

    setError(null);
    setSubmitted(true);
    onCapture(text.trim());
  };

  const handleClear = () => {
    setText("");
    setSubmitted(false);
    setError(null);
  };

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-lg bg-red-50 p-3 text-sm text-red-800">
          {error}
        </div>
      )}

      <div>
        <input
          type="text"
          value={text}
          onChange={handleChange}
          disabled={disabled || submitted}
          placeholder="例：バルブ閉ヨシッ！"
          className="w-full rounded-lg border border-gray-300 px-4 py-3 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
        />
        <p className="mt-1 text-xs text-gray-500">
          Type what you would say (e.g., "バルブ閉ヨシッ！" or "確認完了")
        </p>
      </div>

      {!submitted ? (
        <button
          onClick={handleSubmit}
          disabled={disabled || !text.trim()}
          className="w-full rounded-lg bg-blue-600 px-4 py-3 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
        >
          ✏️ Submit Confirmation
        </button>
      ) : (
        <div className="flex gap-2">
          <button
            onClick={handleClear}
            disabled={disabled}
            className="flex-1 rounded-lg border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50 disabled:bg-gray-100"
          >
            Clear
          </button>
          <div className="flex-1 rounded-lg bg-green-100 px-4 py-2 text-center font-medium text-green-800">
            ✓ Confirmation Submitted
          </div>
        </div>
      )}
    </div>
  );
}
