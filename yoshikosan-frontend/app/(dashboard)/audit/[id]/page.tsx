"use client";

/**
 * Audit session detail page for supervisor review and approval.
 */

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";
import type { paths } from "@/lib/api/schema";

type WorkSession =
  paths["/api/v1/audit/sessions/{session_id}"]["get"]["responses"][200]["content"]["application/json"];

type SOPSchema =
  paths["/api/v1/sops/{sop_id}"]["get"]["responses"][200]["content"]["application/json"];

export default function AuditDetailPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = params.id as string;

  const [session, setSession] = useState<WorkSession | null>(null);
  const [sop, setSOP] = useState<SOPSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [rejectReason, setRejectReason] = useState("");
  const [showRejectDialog, setShowRejectDialog] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      const sessionResponse = await apiClient.audit.getSession(sessionId);

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

  const handleApprove = async () => {
    if (!confirm("Are you sure you want to approve this session?")) {
      return;
    }

    setProcessing(true);
    setError(null);

    try {
      const response = await apiClient.audit.approve(sessionId);

      if (response.error) {
        setError(response.error);
      } else {
        router.push("/audit");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setProcessing(false);
    }
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      setError("Please provide a reason for rejection");
      return;
    }

    setProcessing(true);
    setError(null);

    try {
      const response = await apiClient.audit.reject(sessionId, rejectReason);

      if (response.error) {
        setError(response.error);
      } else {
        router.push("/audit");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rejection failed");
    } finally {
      setProcessing(false);
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

  const failedChecks = session.checks.filter((check) => check.result === "fail");
  const passedChecks = session.checks.filter((check) => check.result === "pass");
  const overriddenChecks = session.checks.filter((check) => check.result === "override");

  const getCheckResultColor = (result: string) => {
    switch (result) {
      case "pass":
        return "bg-green-100 text-green-800 border-green-200";
      case "fail":
        return "bg-red-100 text-red-800 border-red-200";
      case "override":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="mb-2 text-3xl font-bold">Audit Review</h1>
        <h2 className="text-xl text-gray-700">{sop.title}</h2>
        <div className="mt-4 flex items-center gap-4 text-sm text-gray-600">
          <span>Worker ID: {session.worker_id}</span>
          <span>•</span>
          <span>Started: {new Date(session.started_at).toLocaleString()}</span>
          {session.completed_at && (
            <>
              <span>•</span>
              <span>Completed: {new Date(session.completed_at).toLocaleString()}</span>
            </>
          )}
        </div>
      </div>

      {error && <div className="mb-4 rounded-lg bg-red-50 p-4 text-red-800">{error}</div>}

      {/* Summary Stats */}
      <div className="mb-8 grid gap-4 md:grid-cols-3">
        <div className="rounded-lg border border-green-200 bg-green-50 p-6">
          <div className="text-3xl font-bold text-green-800">{passedChecks.length}</div>
          <div className="text-sm font-medium text-green-700">Passed Checks</div>
        </div>

        <div className="rounded-lg border border-red-200 bg-red-50 p-6">
          <div className="text-3xl font-bold text-red-800">{failedChecks.length}</div>
          <div className="text-sm font-medium text-red-700">Failed Checks</div>
        </div>

        <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-6">
          <div className="text-3xl font-bold text-yellow-800">{overriddenChecks.length}</div>
          <div className="text-sm font-medium text-yellow-700">Overridden Checks</div>
        </div>
      </div>

      {/* Action Buttons */}
      {session.status === "completed" && (
        <div className="mb-8 flex gap-4">
          <button
            onClick={handleApprove}
            disabled={processing}
            className="flex-1 rounded-lg bg-green-600 px-6 py-3 font-medium text-white hover:bg-green-700 disabled:bg-gray-400"
          >
            {processing ? "Approving..." : "✓ Approve Session"}
          </button>
          <button
            onClick={() => setShowRejectDialog(true)}
            disabled={processing}
            className="flex-1 rounded-lg bg-red-600 px-6 py-3 font-medium text-white hover:bg-red-700 disabled:bg-gray-400"
          >
            ✗ Reject Session
          </button>
        </div>
      )}

      {/* Reject Dialog */}
      {showRejectDialog && (
        <div className="mb-8 rounded-lg border-2 border-red-500 bg-red-50 p-6">
          <h3 className="mb-4 text-lg font-semibold text-red-900">Reject Session</h3>
          <textarea
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            rows={4}
            placeholder="Enter reason for rejection..."
            className="mb-4 w-full rounded-lg border border-red-300 px-4 py-2 focus:border-red-500 focus:outline-none"
          />
          <div className="flex gap-2">
            <button
              onClick={handleReject}
              disabled={processing || !rejectReason.trim()}
              className="rounded-lg bg-red-600 px-6 py-2 font-medium text-white hover:bg-red-700 disabled:bg-gray-400"
            >
              {processing ? "Rejecting..." : "Confirm Rejection"}
            </button>
            <button
              onClick={() => {
                setShowRejectDialog(false);
                setRejectReason("");
              }}
              className="rounded-lg border border-gray-300 px-6 py-2 font-medium text-gray-700 hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Safety Checks Detail */}
      <div className="rounded-lg border border-gray-200 bg-white p-6">
        <h2 className="mb-6 text-xl font-semibold">Safety Check Details</h2>

        {session.checks.length === 0 ? (
          <div className="text-center text-gray-500">No safety checks performed.</div>
        ) : (
          <div className="space-y-4">
            {session.checks.map((check, index) => (
              <div
                key={check.id}
                className={`rounded-lg border p-4 ${getCheckResultColor(check.result)}`}
              >
                <div className="mb-3 flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <span className="font-semibold">Check #{index + 1}</span>
                    <span className="rounded-full bg-white px-3 py-1 text-xs font-bold">
                      {check.result.toUpperCase()}
                    </span>
                  </div>
                  {check.confidence_score && (
                    <span className="text-sm font-medium">
                      Confidence: {(check.confidence_score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>

                <p className="mb-2 text-sm font-medium">{check.feedback_text}</p>

                <div className="mt-3 flex items-center gap-4 text-xs text-gray-600">
                  <span>Checked: {new Date(check.checked_at).toLocaleString()}</span>
                  {check.needs_review && (
                    <span className="rounded bg-yellow-200 px-2 py-1 font-medium text-yellow-900">
                      NEEDS REVIEW
                    </span>
                  )}
                </div>

                {check.override_reason && (
                  <div className="mt-3 rounded-lg bg-white p-3">
                    <div className="text-xs font-semibold">Override Reason:</div>
                    <div className="mt-1 text-sm">{check.override_reason}</div>
                    {check.override_by && (
                      <div className="mt-1 text-xs text-gray-600">
                        Overridden by: {check.override_by}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
