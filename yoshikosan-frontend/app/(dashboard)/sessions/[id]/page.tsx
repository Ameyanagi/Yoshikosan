"use client";

/**
 * Active work session page with step-by-step guidance and safety checks.
 */

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";
import { CameraCapture } from "@/components/camera-capture";
import { AudioCapture } from "@/components/audio-capture";
import type { paths } from "@/lib/api/schema";

type WorkSession =
  paths["/api/v1/sessions/{session_id}"]["get"]["responses"][200]["content"]["application/json"];

type SOPSchema =
  paths["/api/v1/sops/{sop_id}"]["get"]["responses"][200]["content"]["application/json"];

export default function SessionDetailPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;

  const [session, setSession] = useState<WorkSession | null>(null);
  const [sop, setSOP] = useState<SOPSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [capturedImage, setCapturedImage] = useState<string | null>(null);
  const [capturedAudio, setCapturedAudio] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);
  const [feedbackAudio, setFeedbackAudio] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      const sessionResponse = await apiClient.sessions.get(sessionId);

      if (sessionResponse.error) {
        setError(sessionResponse.error);
        setLoading(false);
        return;
      }

      if (sessionResponse.data) {
        setSession(sessionResponse.data);

        // Fetch SOP details
        const sopResponse = await apiClient.sops.get(sessionResponse.data.sop_id);
        if (sopResponse.data) {
          setSOP(sopResponse.data);
        }
      }

      setLoading(false);
    };

    fetchData();
  }, [sessionId]);

  const handleImageCapture = (imageBase64: string) => {
    setCapturedImage(imageBase64);
  };

  const handleAudioCapture = (audioBase64: string) => {
    setCapturedAudio(audioBase64);
  };

  const handleExecuteCheck = async () => {
    if (!capturedImage || !capturedAudio || !session?.current_step_id) {
      setError("Please capture both image and audio before executing check");
      return;
    }

    setChecking(true);
    setError(null);

    try {
      const response = await apiClient.checks.execute({
        session_id: sessionId,
        step_id: session.current_step_id,
        image_base64: capturedImage,
        audio_base64: capturedAudio,
      });

      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        // Play feedback audio
        if (response.data.feedback_audio_base64) {
          setFeedbackAudio(response.data.feedback_audio_base64);
          const audio = new Audio(`data:audio/webm;base64,${response.data.feedback_audio_base64}`);
          audio.play();
        }

        // Refresh session
        const sessionResponse = await apiClient.sessions.get(sessionId);
        if (sessionResponse.data) {
          setSession(sessionResponse.data);
        }

        // Reset captures
        setCapturedImage(null);
        setCapturedAudio(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Check failed");
    } finally {
      setChecking(false);
    }
  };

  const handleCompleteSession = async () => {
    const response = await apiClient.sessions.complete(sessionId);

    if (response.error) {
      setError(response.error);
    } else {
      router.push("/sessions");
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (!session || !sop) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          Session not found
        </div>
      </div>
    );
  }

  const currentStep = sop.tasks
    .flatMap((task) => task.steps)
    .find((step) => step.id === session.current_step_id);

  const allSteps = sop.tasks.flatMap((task) => task.steps);
  const currentStepIndex = allSteps.findIndex((step) => step.id === session.current_step_id);

  const getCheckResultColor = (result: string) => {
    switch (result) {
      case "pass":
        return "bg-green-100 text-green-800";
      case "fail":
        return "bg-red-100 text-red-800";
      case "override":
        return "bg-yellow-100 text-yellow-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold">{sop.title}</h1>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <span className="rounded-full bg-blue-100 px-3 py-1 font-medium text-blue-800">
            {session.status.replace("_", " ").toUpperCase()}
          </span>
          <span>
            Step {currentStepIndex + 1} of {allSteps.length}
          </span>
          <span>{session.checks.length} safety checks performed</span>
        </div>
      </div>

      {error && <div className="mb-4 rounded-lg bg-red-50 p-4 text-red-800">{error}</div>}

      <div className="grid gap-8 lg:grid-cols-2">
        {/* Left Column: Current Step */}
        <div className="space-y-6">
          <div className="rounded-lg border border-gray-200 bg-white p-6">
            <h2 className="mb-4 text-xl font-semibold">Current Step</h2>

            {currentStep ? (
              <>
                <p className="mb-4 text-gray-700">{currentStep.description}</p>

                {currentStep.expected_action && (
                  <div className="mb-3 rounded-lg bg-blue-50 p-3">
                    <div className="text-sm font-medium text-blue-900">Expected Action:</div>
                    <div className="mt-1 text-sm text-blue-800">{currentStep.expected_action}</div>
                  </div>
                )}

                {currentStep.expected_result && (
                  <div className="mb-3 rounded-lg bg-green-50 p-3">
                    <div className="text-sm font-medium text-green-900">Expected Result:</div>
                    <div className="mt-1 text-sm text-green-800">{currentStep.expected_result}</div>
                  </div>
                )}

                {currentStep.hazards.length > 0 && (
                  <div className="mt-4">
                    <h3 className="mb-2 text-sm font-semibold text-red-900">⚠️ Safety Hazards:</h3>
                    <div className="space-y-2">
                      {currentStep.hazards.map((hazard) => (
                        <div
                          key={hazard.id}
                          className="rounded-lg border border-red-200 bg-red-50 p-3"
                        >
                          <div className="text-sm font-medium text-red-900">
                            {hazard.description}
                          </div>
                          {hazard.mitigation && (
                            <div className="mt-1 text-xs text-red-700">
                              Mitigation: {hazard.mitigation}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center text-gray-500">
                All steps completed! You can now complete the session.
              </div>
            )}
          </div>

          {session.status === "in_progress" && !currentStep && (
            <button
              onClick={handleCompleteSession}
              className="w-full rounded-lg bg-green-600 px-6 py-3 font-medium text-white hover:bg-green-700"
            >
              Complete Session
            </button>
          )}
        </div>

        {/* Right Column: Safety Check */}
        {currentStep && session.status === "in_progress" && (
          <div className="space-y-6">
            <div className="rounded-lg border border-gray-200 bg-white p-6">
              <h2 className="mb-4 text-xl font-semibold">Safety Verification</h2>

              <div className="space-y-4">
                <div>
                  <h3 className="mb-2 text-sm font-medium text-gray-700">
                    1. Capture Current Work
                  </h3>
                  <CameraCapture onCapture={handleImageCapture} disabled={checking} />
                  {capturedImage && (
                    <div className="mt-2 text-sm text-green-600">✓ Image captured</div>
                  )}
                </div>

                <div>
                  <h3 className="mb-2 text-sm font-medium text-gray-700">
                    2. Describe What You Did
                  </h3>
                  <AudioCapture onCapture={handleAudioCapture} disabled={checking} />
                  {capturedAudio && (
                    <div className="mt-2 text-sm text-green-600">✓ Audio captured</div>
                  )}
                </div>

                <button
                  onClick={handleExecuteCheck}
                  disabled={!capturedImage || !capturedAudio || checking}
                  className="w-full rounded-lg bg-blue-600 px-6 py-3 font-medium text-white hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {checking ? "Verifying with AI..." : "Execute Safety Check"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Safety Check History */}
      {session.checks.length > 0 && (
        <div className="mt-8 rounded-lg border border-gray-200 bg-white p-6">
          <h2 className="mb-4 text-xl font-semibold">Safety Check History</h2>
          <div className="space-y-3">
            {session.checks.map((check) => (
              <div
                key={check.id}
                className="flex items-start justify-between rounded-lg border border-gray-100 p-4"
              >
                <div className="flex-1">
                  <div className="mb-1 flex items-center gap-2">
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-medium ${getCheckResultColor(
                        check.result
                      )}`}
                    >
                      {check.result.toUpperCase()}
                    </span>
                    {check.confidence_score && (
                      <span className="text-xs text-gray-500">
                        Confidence: {(check.confidence_score * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700">{check.feedback_text}</p>
                  <p className="mt-1 text-xs text-gray-500">
                    {new Date(check.checked_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
