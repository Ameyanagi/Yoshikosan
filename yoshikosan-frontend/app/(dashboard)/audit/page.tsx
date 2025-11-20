"use client";

/**
 * Audit dashboard page for supervisors.
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { apiClient } from "@/lib/api";
import type { paths } from "@/lib/api/schema";

type AuditSessionListItem =
  paths["/api/v1/audit/sessions"]["get"]["responses"][200]["content"]["application/json"][number];

export default function AuditPage() {
  const [sessions, setSessions] = useState<AuditSessionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSessions = async () => {
      const response = await apiClient.audit.listSessions("completed");

      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        setSessions(response.data);
      }

      setLoading(false);
    };

    fetchSessions();
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Audit Dashboard</h1>
        <p className="mt-2 text-gray-600">Review and approve completed work sessions</p>
      </div>

      {error && <div className="mb-4 rounded-lg bg-red-50 p-4 text-red-800">{error}</div>}

      {sessions.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
          <p className="text-gray-500">No sessions pending review.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {sessions.map((session) => (
            <Link
              key={session.session_id}
              href={`/audit/${session.session_id}`}
              className="block rounded-lg border border-gray-200 bg-white p-6 transition-shadow hover:shadow-md"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="mb-2 text-lg font-semibold">{session.sop_title}</h3>
                  <div className="space-y-1 text-sm text-gray-600">
                    <p>Worker ID: {session.worker_id}</p>
                    {session.completed_at && (
                      <p>Completed: {new Date(session.completed_at).toLocaleString()}</p>
                    )}
                    <p>Total Checks: {session.check_count}</p>
                    {session.failed_check_count > 0 && (
                      <p className="font-medium text-red-600">
                        Failed Checks: {session.failed_check_count}
                      </p>
                    )}
                  </div>
                </div>
                <div className="ml-4 flex items-center">
                  <span className="text-sm text-gray-500">Review →</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
