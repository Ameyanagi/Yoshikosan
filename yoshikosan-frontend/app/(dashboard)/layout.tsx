"use client";

/**
 * Dashboard layout with navigation.
 */

import { ReactNode } from "react";
import Link from "next/link";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      {/* Navigation */}
      <nav className="border-b bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <Link href="/" className="text-2xl font-bold">
            ヨシコさん、ヨシッ！
          </Link>

          <div className="flex items-center gap-6">
            <Link
              href="/sops"
              className="text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              SOPs
            </Link>
            <Link
              href="/sessions"
              className="text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Sessions
            </Link>
            <Link
              href="/audit"
              className="text-sm font-medium text-gray-700 hover:text-gray-900"
            >
              Audit
            </Link>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 bg-gray-50">{children}</main>
    </div>
  );
}
