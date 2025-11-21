/**
 * Type-safe API client for Yoshikosan backend.
 * Generated from OpenAPI schema.
 */

import type { paths } from "./schema";

type ApiResponse<T> = {
  data: T | null;
  error: string | null;
  status: number;
};

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = "/api") {
    this.baseUrl = baseUrl;
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        ...options,
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...options.headers,
        },
      });

      const data = response.ok ? await response.json() : null;
      const error = !response.ok
        ? data?.detail || `Request failed with status ${response.status}`
        : null;

      return {
        data,
        error,
        status: response.status,
      };
    } catch (error) {
      return {
        data: null,
        error: error instanceof Error ? error.message : "Unknown error",
        status: 0,
      };
    }
  }

  private async requestMultipart<T>(path: string, formData: FormData): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${path}`, {
        method: "POST",
        credentials: "include",
        body: formData,
      });

      const data = response.ok ? await response.json() : null;
      const error = !response.ok
        ? data?.detail || `Request failed with status ${response.status}`
        : null;

      return {
        data,
        error,
        status: response.status,
      };
    } catch (error) {
      return {
        data: null,
        error: error instanceof Error ? error.message : "Unknown error",
        status: 0,
      };
    }
  }

  // ============================================================================
  // Authentication Endpoints
  // ============================================================================

  auth = {
    register: async (data: { email: string; password: string; name: string }) =>
      this.request<
        paths["/api/auth/register"]["post"]["responses"][200]["content"]["application/json"]
      >("/auth/register", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    login: async (data: { email: string; password: string }) =>
      this.request<
        paths["/api/auth/login"]["post"]["responses"][200]["content"]["application/json"]
      >("/auth/login", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    logout: async () =>
      this.request<
        paths["/api/auth/logout"]["post"]["responses"][200]["content"]["application/json"]
      >("/auth/logout", {
        method: "POST",
      }),

    me: async () =>
      this.request<paths["/api/auth/me"]["get"]["responses"][200]["content"]["application/json"]>(
        "/auth/me"
      ),

    google: {
      initiate: () => {
        window.location.href = `${this.baseUrl}/auth/google`;
      },
    },

    discord: {
      initiate: () => {
        window.location.href = `${this.baseUrl}/auth/discord`;
      },
    },
  };

  // ============================================================================
  // SOP Endpoints
  // ============================================================================

  sops = {
    upload: async (data: { title: string; images: File[]; text_content?: string }) => {
      const formData = new FormData();
      formData.append("title", data.title);
      if (data.text_content) {
        formData.append("text_content", data.text_content);
      }
      data.images.forEach((image) => {
        formData.append("images", image);
      });

      return this.requestMultipart<
        paths["/api/v1/sops"]["post"]["responses"][201]["content"]["application/json"]
      >("/v1/sops", formData);
    },

    list: async () =>
      this.request<paths["/api/v1/sops"]["get"]["responses"][200]["content"]["application/json"]>(
        "/v1/sops"
      ),

    get: async (id: string) =>
      this.request<
        paths["/api/v1/sops/{sop_id}"]["get"]["responses"][200]["content"]["application/json"]
      >(`/v1/sops/${id}`),

    delete: async (id: string) =>
      this.request<void>(`/v1/sops/${id}`, {
        method: "DELETE",
      }),
  };

  // ============================================================================
  // Session Endpoints
  // ============================================================================

  sessions = {
    start: async (data: { sop_id: string }) =>
      this.request<
        paths["/api/v1/sessions"]["post"]["responses"][201]["content"]["application/json"]
      >("/v1/sessions", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    current: async () =>
      this.request<
        paths["/api/v1/sessions/current"]["get"]["responses"][200]["content"]["application/json"]
      >("/v1/sessions/current"),

    list: async () =>
      this.request<
        paths["/api/v1/sessions"]["get"]["responses"][200]["content"]["application/json"]
      >("/v1/sessions"),

    get: async (id: string) =>
      this.request<
        paths["/api/v1/sessions/{session_id}"]["get"]["responses"][200]["content"]["application/json"]
      >(`/v1/sessions/${id}`),

    complete: async (id: string) =>
      this.request<
        paths["/api/v1/sessions/{session_id}/complete"]["post"]["responses"][200]["content"]["application/json"]
      >(`/v1/sessions/${id}/complete`, {
        method: "POST",
      }),

    getWelcomeAudioUrl: (sessionId: string) => `${this.baseUrl}/v1/sessions/${sessionId}/welcome-audio`,
  };

  // ============================================================================
  // Safety Check Endpoints
  // ============================================================================

  checks = {
    execute: async (data: {
      session_id: string;
      step_id: string;
      image_base64: string;
      audio_base64?: string;
      audio_transcript?: string;
    }) =>
      this.request<
        paths["/api/v1/checks"]["post"]["responses"][201]["content"]["application/json"]
      >("/v1/checks", {
        method: "POST",
        body: JSON.stringify(data),
      }),

    override: async (checkId: string, data: { supervisor_id: string; reason: string }) =>
      this.request<
        paths["/api/v1/checks/{check_id}/override"]["post"]["responses"][200]["content"]["application/json"]
      >(`/v1/checks/${checkId}/override`, {
        method: "POST",
        body: JSON.stringify(data),
      }),

    getAudioUrl: (checkId: string) => `${this.baseUrl}/v1/checks/${checkId}/audio`,
  };

  // ============================================================================
  // Audit Endpoints
  // ============================================================================

  audit = {
    listSessions: async (statusFilter: string = "completed") =>
      this.request<
        paths["/api/v1/audit/sessions"]["get"]["responses"][200]["content"]["application/json"]
      >(`/v1/audit/sessions?status_filter=${statusFilter}`),

    getSession: async (id: string) =>
      this.request<
        paths["/api/v1/audit/sessions/{session_id}"]["get"]["responses"][200]["content"]["application/json"]
      >(`/v1/audit/sessions/${id}`),

    approve: async (id: string) =>
      this.request<
        paths["/api/v1/audit/sessions/{session_id}/approve"]["post"]["responses"][200]["content"]["application/json"]
      >(`/v1/audit/sessions/${id}/approve`, {
        method: "POST",
      }),

    reject: async (id: string, reason: string) =>
      this.request<
        paths["/api/v1/audit/sessions/{session_id}/reject"]["post"]["responses"][200]["content"]["application/json"]
      >(`/v1/audit/sessions/${id}/reject`, {
        method: "POST",
        body: JSON.stringify({ reason }),
      }),
  };
}

// Export singleton instance
export const apiClient = new ApiClient();
export type { ApiResponse };
