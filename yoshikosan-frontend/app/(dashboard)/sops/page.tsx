"use client";

/**
 * SOPs list page.
 */

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";
import type { paths } from "@/lib/api/schema";

type SOPListItem =
  paths["/api/v1/sops"]["get"]["responses"][200]["content"]["application/json"][number];

export default function SOPsPage() {
  const router = useRouter();
  const [sops, setSOPs] = useState<SOPListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSOPs = async () => {
      const response = await apiClient.sops.list();

      if (response.error) {
        setError(response.error);
      } else if (response.data) {
        setSOPs(response.data);
      }

      setLoading(false);
    };

    fetchSOPs();
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
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-3xl font-bold">Standard Operating Procedures</h1>
        <Link
          href="/sops/upload"
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Upload SOP
        </Link>
      </div>

      {error && <div className="mb-4 rounded-lg bg-red-50 p-4 text-red-800">{error}</div>}

      {sops.length === 0 ? (
        <div className="rounded-lg border border-gray-200 bg-white p-12 text-center">
          <p className="text-gray-500">No SOPs found. Upload your first SOP to get started.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sops.map((sop) => (
            <Link
              key={sop.id}
              href={`/sops/${sop.id}`}
              className="block rounded-lg border border-gray-200 bg-white p-6 transition-shadow hover:shadow-md"
            >
              <h3 className="mb-2 text-lg font-semibold">{sop.title}</h3>
              <div className="space-y-1 text-sm text-gray-600">
                <p>{sop.task_count} tasks</p>
                <p>{sop.step_count} steps</p>
                <p className="text-xs text-gray-400">
                  Created {new Date(sop.created_at).toLocaleDateString()}
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
