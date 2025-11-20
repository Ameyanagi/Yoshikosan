"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export default function Home() {
  const { user, loading, logout } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      {/* Navigation */}
      <nav className="border-b bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <h1 className="text-2xl font-bold">ヨシコさん、ヨシッ！</h1>
          <div className="flex items-center gap-4">
            {user ? (
              <>
                <div className="flex items-center gap-3">
                  {user.avatar_url && (
                    <img src={user.avatar_url} alt={user.name} className="h-8 w-8 rounded-full" />
                  )}
                  <span className="text-sm font-medium">{user.name}</span>
                </div>
                <button
                  onClick={logout}
                  className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50"
                >
                  Sign in
                </Link>
                <Link
                  href="/register"
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                >
                  Sign up
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex flex-1 items-center justify-center bg-gray-50">
        <div className="text-center">
          <h2 className="text-4xl font-bold text-gray-900">Welcome to ヨシコさん、ヨシッ！</h2>
          <p className="mt-4 text-lg text-gray-600">Industrial Safety Management System</p>
          {user ? (
            <div className="mt-8">
              <p className="text-xl text-gray-700">Hello, {user.name}! 👋</p>
              <p className="mt-2 text-gray-600">You are successfully authenticated.</p>
            </div>
          ) : (
            <div className="mt-8 flex justify-center gap-4">
              <Link
                href="/login"
                className="rounded-lg bg-blue-600 px-6 py-3 font-medium text-white hover:bg-blue-700"
              >
                Get Started
              </Link>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
