import { authenticatedFetch, createAuthHeaders } from "@/lib/auth";
import {
    CVBuilderCreate,
    CVBuilderDocument,
    CVBuilderUpdate,
    CVScore,
    CVTemplate,
    EnhanceBulletsRequest,
    EnhanceSummaryRequest,
    EnhancementSuggestion,
    ExportCVRequest,
} from "@/lib/types/cv-builder";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CVBuilderApiParams {
  jwt?: string;
  authStrategy?: "refresh" | "logout";
}

export const cvBuilderApi = {
  // =========================================================================
  // CV Document Operations
  // =========================================================================

  createCV: async (
    data: CVBuilderCreate,
    params: CVBuilderApiParams = {}
  ): Promise<CVBuilderDocument> => {
    const { jwt, authStrategy = "refresh" } = params;

    const response = await authenticatedFetch(
      `${API_BASE_URL}/api/cv-builder/`,
      {
        method: "POST",
        headers: {
          ...createAuthHeaders(jwt),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      },
      { strategy: authStrategy }
    );

    if (!response.ok) {
      throw new Error(`Failed to create CV: ${response.statusText}`);
    }

    return response.json();
  },

  getMyCVs: async (
    params: CVBuilderApiParams = {}
  ): Promise<CVBuilderDocument[]> => {
    const { jwt, authStrategy = "refresh" } = params;

    const response = await authenticatedFetch(
      `${API_BASE_URL}/api/cv-builder/`,
      {
        method: "GET",
        headers: {
          ...createAuthHeaders(jwt),
        },
      },
      { strategy: authStrategy }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch CVs: ${response.statusText}`);
    }

    return response.json();
  },

  getPrimaryCV: async (
    params: CVBuilderApiParams = {}
  ): Promise<CVBuilderDocument | null> => {
    const { jwt, authStrategy = "refresh" } = params;

    const response = await authenticatedFetch(
      `${API_BASE_URL}/api/cv-builder/primary`,
      {
        method: "GET",
        headers: {
          ...createAuthHeaders(jwt),
        },
      },
      { strategy: authStrategy }
    );

    if (!response.ok) {
      if (response.status === 404) {
        return null;
      }
      throw new Error(`Failed to fetch primary CV: ${response.statusText}`);
    }

    return response.json();
  },

  getCV: async (
    cvId: string,
    params: CVBuilderApiParams = {}
  ): Promise<CVBuilderDocument> => {
    const { jwt, authStrategy = "refresh" } = params;

    const response = await authenticatedFetch(
      `${API_BASE_URL}/api/cv-builder/${cvId}`,
      {
        method: "GET",
        headers: {
          ...createAuthHeaders(jwt),
        },
      },
      { strategy: authStrategy }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch CV: ${response.statusText}`);
    }

    return response.json();
  },

  updateCV: async (
    cvId: string,
    data: CVBuilderUpdate,
    params: CVBuilderApiParams = {}
  ): Promise<CVBuilderDocument> => {
    const { jwt, authStrategy = "refresh" } = params;

    const response = await authenticatedFetch(
      `${API_BASE_URL}/api/cv-builder/${cvId}`,
      {
        method: "PATCH",
        headers: {
          ...createAuthHeaders(jwt),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      },
      { strategy: authStrategy }
    );

    if (!response.ok) {
      throw new Error(`Failed to update CV: ${response.statusText}`);
    }

    return response.json();
  },

  deleteCV: async (
    cvId: string,
    params: CVBuilderApiParams = {}
  ): Promise<void> => {
    const { jwt, authStrategy = "refresh" } = params;

    const response = await authenticatedFetch(
      `${API_BASE_URL}/api/cv-builder/${cvId}`,
      {
        method: "DELETE",
        headers: {
          ...createAuthHeaders(jwt),
        },
      },
      { strategy: authStrategy }
    );

    if (!response.ok) {
      throw new Error(`Failed to delete CV: ${response.statusText}`);
    }
  },

  setPrimaryCV: async (
    cvId: string,
    params: CVBuilderApiParams = {}
  ): Promise<{ success: boolean; message: string }> => {
    const { jwt, authStrategy = "refresh" } = params;

    const response = await authenticatedFetch(
      `${API_BASE_URL}/api/cv-builder/${cvId}/set-primary`,
      {
        method: "POST",
        headers: {
          ...createAuthHeaders(jwt),
        },
      },
      { strategy: authStrategy }
    );

    if (!response.ok) {
      throw new Error(`Failed to set primary CV: ${response.statusText}`);
    }

    return response.json();
  },

  // =========================================================================
  // Template Operations
  // =========================================================================

  getTemplates: async (
    params: CVBuilderApiParams = {}
  ): Promise<CVTemplate[]> => {
    const { jwt, authStrategy = "refresh" } = params;

    const response = await authenticatedFetch(
      `${API_BASE_URL}/api/cv-builder/templates/all`,
      {
        method: "GET",
        headers: {
          ...createAuthHeaders(jwt),
        },
      },
      { strategy: authStrategy }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch templates: ${response.statusText}`);
    }

    const templates = await response.json();
    // Add convenience `id` field that maps to `template_id`
    return templates.map((t: CVTemplate) => ({
      ...t,
      id: t.template_id,
      styling: {
        font_family: t.font_family,
        font_size_base: t.font_size_base,
        accent_color: t.accent_color,
        line_spacing: t.line_spacing,
        margins: t.margins,
      },
    }));
  },

  getTemplate: async (
    templateId: string,
    params: CVBuilderApiParams = {}
  ): Promise<CVTemplate> => {
    const { jwt, authStrategy = "refresh" } = params;

    const response = await authenticatedFetch(
      `${API_BASE_URL}/api/cv-builder/templates/${templateId}`,
      {
        method: "GET",
        headers: {
          ...createAuthHeaders(jwt),
        },
      },
      { strategy: authStrategy }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch template: ${response.statusText}`);
    }

    return response.json();
  },

  // =========================================================================
  // Enhancement Operations
  // =========================================================================

  enhanceBullets: async (
    cvId: string,
    data: EnhanceBulletsRequest,
    params: CVBuilderApiParams = {}
  ): Promise<EnhancementSuggestion> => {
    const { jwt, authStrategy = "refresh" } = params;

    const response = await authenticatedFetch(
      `${API_BASE_URL}/api/cv-builder/${cvId}/enhance-bullets`,
      {
        method: "POST",
        headers: {
          ...createAuthHeaders(jwt),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      },
      { strategy: authStrategy }
    );

    if (!response.ok) {
      throw new Error(`Failed to enhance bullets: ${response.statusText}`);
    }

    return response.json();
  },

  enhanceSummary: async (
    cvId: string,
    data: EnhanceSummaryRequest,
    params: CVBuilderApiParams = {}
  ): Promise<EnhancementSuggestion> => {
    const { jwt, authStrategy = "refresh" } = params;

    const response = await authenticatedFetch(
      `${API_BASE_URL}/api/cv-builder/${cvId}/enhance-summary`,
      {
        method: "POST",
        headers: {
          ...createAuthHeaders(jwt),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      },
      { strategy: authStrategy }
    );

    if (!response.ok) {
      throw new Error(`Failed to enhance summary: ${response.statusText}`);
    }

    return response.json();
  },

  // =========================================================================
  // Scoring Operations
  // =========================================================================

  scoreCV: async (
    cvId: string,
    params: CVBuilderApiParams = {}
  ): Promise<CVScore> => {
    const { jwt, authStrategy = "refresh" } = params;

    const response = await authenticatedFetch(
      `${API_BASE_URL}/api/cv-builder/${cvId}/score`,
      {
        method: "POST",
        headers: {
          ...createAuthHeaders(jwt),
        },
      },
      { strategy: authStrategy }
    );

    if (!response.ok) {
      throw new Error(`Failed to score CV: ${response.statusText}`);
    }

    return response.json();
  },

  getScoreHistory: async (
    cvId: string,
    limit: number = 10,
    params: CVBuilderApiParams = {}
  ): Promise<CVScore[]> => {
    const { jwt, authStrategy = "refresh" } = params;

    const response = await authenticatedFetch(
      `${API_BASE_URL}/api/cv-builder/${cvId}/score/history?limit=${limit}`,
      {
        method: "GET",
        headers: {
          ...createAuthHeaders(jwt),
        },
      },
      { strategy: authStrategy }
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch score history: ${response.statusText}`);
    }

    return response.json();
  },

  // =========================================================================
  // Export Operations
  // =========================================================================

  exportCV: async (
    cvId: string,
    data: ExportCVRequest,
    params: CVBuilderApiParams = {}
  ): Promise<Blob> => {
    const { jwt, authStrategy = "refresh" } = params;

    const response = await authenticatedFetch(
      `${API_BASE_URL}/api/cv-builder/${cvId}/export`,
      {
        method: "POST",
        headers: {
          ...createAuthHeaders(jwt),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      },
      { strategy: authStrategy }
    );

    if (!response.ok) {
      throw new Error(`Failed to export CV: ${response.statusText}`);
    }

    return response.blob();
  },
};
