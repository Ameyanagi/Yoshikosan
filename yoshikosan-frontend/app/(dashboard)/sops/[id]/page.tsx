"use client";

/**
 * SOP detail page showing tasks, steps, and hazards.
 */

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";
import type { paths } from "@/lib/api/schema";

type SOPSchema =
  paths["/api/v1/sops/{sop_id}"]["get"]["responses"][200]["content"]["application/json"];

export default function SOPDetailPage() {
  const params = useParams();
  const router = useRouter();
  const sopId = params.id as string;

  const [sop, setSOP] = useState<SOPSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startingSession, setStartingSession] = useState(false);

  useEffect(() => {
    const fetchSOP = async () => {
      const response = await apiClient.sops.get(sopId);

      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        setSOP(response.data);
      }

      setLoading(false);
    };

    fetchSOP();
  }, [sopId]);

  const handleStartSession = async () => {
    setStartingSession(true);
    setError(null);

    try {
      // Log the request for debugging
      console.log("Starting session for SOP:", sopId);
      
      const response = await apiClient.sessions.start({ sop_id: sopId });

      if (response.error) {
        console.error("Session start failed:", response.error);
        setError(response.error);
      } else if (response.data) {
        console.log("Session started successfully:", response.data.session.id);
        // Use replace instead of push to avoid history.pushState warning
        router.replace(`/sessions/${response.data.session.id}`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to start session";
      console.error("Exception during session start:", err);
      setError(errorMessage);
    } finally {
      setStartingSession(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this SOP?")) {
      return;
    }

    const response = await apiClient.sops.delete(sopId);

    if (response.error) {
      setError(response.error);
    } else {
      router.push("/sops");
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  if (!sop) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          SOP not found
        </div>
      </div>
    );
  }

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "high":
        return "bg-red-100 text-red-800 border-red-200";
      case "medium":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "low":
        return "bg-blue-100 text-blue-800 border-blue-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="mb-2 text-3xl font-bold">{sop.title}</h1>
          <div className="space-y-1 text-sm text-gray-600">
            <p>Created: {new Date(sop.created_at).toLocaleDateString()}</p>
            <p>Last Updated: {new Date(sop.updated_at).toLocaleDateString()}</p>
            <p>
              {sop.tasks.length} tasks,{" "}
              {sop.tasks.reduce((acc, task) => acc + task.steps.length, 0)} steps
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleStartSession}
            disabled={startingSession}
            className="rounded-lg bg-green-600 px-6 py-3 font-medium text-white hover:bg-green-700 disabled:bg-gray-400"
          >
            {startingSession ? "Starting..." : "Start Session"}
          </button>
          <button
            onClick={handleDelete}
            className="rounded-lg border border-red-300 px-4 py-3 font-medium text-red-600 hover:bg-red-50"
          >
            Delete
          </button>
        </div>
      </div>

      {error && <div className="mb-4 rounded-lg bg-red-50 p-4 text-red-800">{error}</div>}

      {/* Tasks */}
      <div className="space-y-6">
        {sop.tasks.map((task, taskIndex) => (
          <div key={task.id} className="rounded-lg border border-gray-200 bg-white p-6">
            <div className="mb-4 flex items-start justify-between">
              <div>
                <h2 className="text-xl font-semibold">
                  Task {taskIndex + 1}: {task.title}
                </h2>
                {task.description && <p className="mt-1 text-gray-600">{task.description}</p>}
              </div>
              <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-800">
                {task.steps.length} steps
              </span>
            </div>

            {/* Steps */}
            <div className="space-y-4">
              {task.steps.map((step, stepIndex) => (
                <div key={step.id} className="rounded-lg border border-gray-100 bg-gray-50 p-4">
                  <div className="mb-3">
                    <h3 className="font-medium text-gray-900">Step {stepIndex + 1}</h3>
                    <p className="mt-1 text-sm text-gray-700">{step.description}</p>
                  </div>

                  {step.expected_action && (
                    <div className="mb-2 text-sm">
                      <span className="font-medium text-gray-700">想定される作業:</span>{" "}
                      <span className="text-gray-600">{step.expected_action}</span>
                    </div>
                  )}

                  {step.expected_result && (
                    <div className="mb-2 text-sm">
                      <span className="font-medium text-gray-700">期待される結果:</span>{" "}
                      <span className="text-gray-600">{step.expected_result}</span>
                    </div>
                  )}

                  {/* Hazards */}
                  {step.hazards.length > 0 && (
                    <div className="mt-3 space-y-2">
                      <h4 className="text-sm font-medium text-gray-900">⚠️ 危険箇所:</h4>
                      {step.hazards.map((hazard) => (
                        <div
                          key={hazard.id}
                          className={`rounded border p-3 ${getSeverityColor(hazard.severity)}`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="text-sm font-medium">{hazard.description}</p>
                              {hazard.mitigation && (
                                <p className="mt-1 text-xs">
                                  <span className="font-medium">対策:</span>{" "}
                                  {hazard.mitigation}
                                </p>
                              )}
                            </div>
                            <span className="ml-2 text-xs font-bold uppercase">
                              {hazard.severity}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
