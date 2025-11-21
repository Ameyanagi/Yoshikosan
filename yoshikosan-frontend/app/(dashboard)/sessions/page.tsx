"use client";

/**
 * Sessions list page.
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api";
import type { paths } from "@/lib/api/schema";

type WorkSession =
  paths["/api/v1/sessions"]["get"]["responses"][200]["content"]["application/json"][number];

export default function SessionsPage() {
  const [sessions, setSessions] = useState<WorkSession[]>([]);
  const [currentSession, setCurrentSession] = useState<WorkSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      // Fetch current session
      const currentResponse = await apiClient.sessions.current();
      if (currentResponse.data) {
        setCurrentSession(currentResponse.data);
      }

      // Fetch all sessions
      const sessionsResponse = await apiClient.sessions.list();
      if (sessionsResponse.error) {
        setError(sessionsResponse.error);
      } else if (sessionsResponse.data) {
        setSessions(sessionsResponse.data);
      }

      setLoading(false);
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "in_progress":
        return "bg-blue-100 text-blue-800";
      case "paused":
        return "bg-purple-100 text-purple-800";
      case "completed":
        return "bg-yellow-100 text-yellow-800";
      case "aborted":
        return "bg-gray-100 text-gray-800";
      case "approved":
        return "bg-green-100 text-green-800";
      case "rejected":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const handlePauseSession = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const response = await apiClient.sessions.pause(id);
    if (response.error) {
      setError(response.error);
    } else {
      // Refresh sessions
      const sessionsResponse = await apiClient.sessions.list();
      if (sessionsResponse.data) {
        setSessions(sessionsResponse.data);
      }
    }
  };

  const handleResumeSession = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const response = await apiClient.sessions.resume(id);
    if (response.error) {
      setError(response.error);
    } else {
      // Refresh sessions
      const sessionsResponse = await apiClient.sessions.list();
      if (sessionsResponse.data) {
        setSessions(sessionsResponse.data);
      }
    }
  };

  const handleAbortSession = async (id: string, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    const reason = prompt("Enter reason for aborting (optional):");
    if (reason === null) return; // User cancelled

    const response = await apiClient.sessions.abort(id, reason || undefined);
    if (response.error) {
      setError(response.error);
    } else {
      // Refresh sessions
      const sessionsResponse = await apiClient.sessions.list();
      if (sessionsResponse.data) {
        setSessions(sessionsResponse.data);
      }
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Work Sessions</h1>
      </div>

      {error && <div className="mb-4 rounded-lg bg-red-50 p-4 text-red-800">{error}</div>}

      {/* Current Active Session */}
      {currentSession && (
        <div className="mb-8 rounded-lg border-2 border-blue-500 bg-blue-50 p-6">
          <div className="mb-2 flex items-center justify-between">
            <h2 className="text-xl font-semibold">Active Session</h2>
            <Link
              href={`/sessions/${currentSession.id}`}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Continue Session
            </Link>
          </div>
          <div className="space-y-1 text-sm text-gray-700">
            <p>Session ID: {currentSession.id}</p>
            <p>Started: {new Date(currentSession.started_at).toLocaleString()}</p>
            <p>Safety Checks: {currentSession.checks.length}</p>
          </div>
        </div>
      )}

      {/* Sessions List */}
      {sessions.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
          <p className="text-gray-500">No sessions found. Start a session from an SOP to begin.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {sessions.map((session) => (
            <Link
              key={session.id}
              href={`/sessions/${session.id}`}
              className="block rounded-lg border border-gray-200 bg-white p-6 transition-shadow hover:shadow-md"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="mb-2 flex items-center gap-3">
                    <h3 className="text-lg font-semibold">
                      {(session as any).sop_title || `Session ${session.id.slice(0, 8)}`}
                    </h3>
                    <span
                      className={`rounded-full px-3 py-1 text-xs font-medium ${getStatusColor(
                        session.status
                      )}`}
                    >
                      {session.status.replace("_", " ").toUpperCase()}
                    </span>
                  </div>
                  <div className="space-y-1 text-sm text-gray-600">
                    <p>Started: {new Date(session.started_at).toLocaleString()}</p>
                    {session.completed_at && (
                      <p>Completed: {new Date(session.completed_at).toLocaleString()}</p>
                    )}
                    {(session as any).paused_at && (
                      <p>Paused: {new Date((session as any).paused_at).toLocaleString()}</p>
                    )}
                    {(session as any).aborted_at && (
                      <p>Aborted: {new Date((session as any).aborted_at).toLocaleString()}</p>
                    )}
                    <p>Safety Checks: {session.checks.length}</p>
                  </div>
                </div>
                <div className="ml-4 flex flex-col gap-2">
                  {session.status === "in_progress" && (
                    <>
                      <button
                        onClick={(e) => handlePauseSession(session.id, e)}
                        className="rounded bg-purple-600 px-3 py-1 text-xs font-medium text-white hover:bg-purple-700"
                      >
                        Pause
                      </button>
                      <button
                        onClick={(e) => handleAbortSession(session.id, e)}
                        className="rounded bg-red-600 px-3 py-1 text-xs font-medium text-white hover:bg-red-700"
                      >
                        Abort
                      </button>
                    </>
                  )}
                  {session.status === "paused" && (
                    <>
                      <button
                        onClick={(e) => handleResumeSession(session.id, e)}
                        className="rounded bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700"
                      >
                        Resume
                      </button>
                      <button
                        onClick={(e) => handleAbortSession(session.id, e)}
                        className="rounded bg-red-600 px-3 py-1 text-xs font-medium text-white hover:bg-red-700"
                      >
                        Abort
                      </button>
                    </>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
