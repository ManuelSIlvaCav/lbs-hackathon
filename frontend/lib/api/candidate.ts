import {
    authenticatedFetch,
    createAuthHeaders
} from "@/lib/auth";
import { Candidate } from "@/lib/types/candidate";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface CandidateApiParams {
  jwt?: string;
  /**
   * Strategy for handling authentication errors
   * - "refresh": Try to refresh token, then logout if refresh fails (default)
   * - "logout": Immediately logout on auth error
   */
  authStrategy?: "refresh" | "logout";
}

export const candidateApi = {
  getCandidate: async (
    candidateId: string,
    params: CandidateApiParams = {}
  ): Promise<Candidate> => {
    const { jwt, authStrategy = "refresh" } = params;

    try {
      const response = await authenticatedFetch(
        `${API_BASE_URL}/api/candidates/${candidateId}`,
        {
          method: "GET",
          headers: {
            ...createAuthHeaders(jwt),
          },
        },
        { strategy: authStrategy }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch candidate: ${response.statusText}`);
      }

      return response.json();
    } catch (error: any) {
      // Auth errors are already handled by authenticatedFetch
      // Re-throw for other errors
      throw error;
    }
  },

  getCandidates: async (
    params: CandidateApiParams = {}
  ): Promise<Candidate[]> => {
    const { jwt, authStrategy = "refresh" } = params;

    try {
      const response = await authenticatedFetch(
        `${API_BASE_URL}/api/candidates`,
        {
          method: "GET",
          headers: {
            ...createAuthHeaders(jwt),
          },
        },
        { strategy: authStrategy }
      );

      if (!response.ok) {
        throw new Error(`Failed to fetch candidates: ${response.statusText}`);
      }

      return response.json();
    } catch (error: any) {
      throw error;
    }
  },

  uploadAndParseCV: async (
    candidateId: string,
    file: File,
    params: CandidateApiParams = {}
  ): Promise<Candidate> => {
    const { jwt, authStrategy = "refresh" } = params;

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await authenticatedFetch(
        `${API_BASE_URL}/api/candidates/${candidateId}/upload-cv`,
        {
          method: "POST",
          headers: {
            ...createAuthHeaders(jwt),
            // Don't set Content-Type for FormData - browser will set it with boundary
          },
          body: formData,
        },
        { strategy: authStrategy }
      );

      if (!response.ok) {
        const error = await response
          .json()
          .catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || "Failed to upload and parse CV");
      }

      return response.json();
    } catch (error: any) {
      throw error;
    }
  },

  updateCandidateMetadata: async (
    candidateId: string,
    metadata: Candidate["metadata"],
    params: CandidateApiParams = {}
  ): Promise<Candidate> => {
    const { jwt, authStrategy = "refresh" } = params;

    try {
      const response = await authenticatedFetch(
        `${API_BASE_URL}/api/candidates/${candidateId}`,
        {
          method: "PUT",
          headers: {
            ...createAuthHeaders(jwt),
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ metadata }),
        },
        { strategy: authStrategy }
      );

      if (!response.ok) {
        const error = await response
          .json()
          .catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || "Failed to update candidate metadata");
      }

      return response.json();
    } catch (error: any) {
      throw error;
    }
  },

  updateSearchPreferences: async (
    candidateId: string,
    searchPreferences: any,
    params: CandidateApiParams = {}
  ): Promise<Candidate> => {
    const { jwt, authStrategy = "refresh" } = params;

    try {
      const response = await authenticatedFetch(
        `${API_BASE_URL}/api/candidates/${candidateId}/search-preferences`,
        {
          method: "PATCH",
          headers: {
            ...createAuthHeaders(jwt),
            "Content-Type": "application/json",
          },
          body: JSON.stringify(searchPreferences),
        },
        { strategy: authStrategy }
      );

      if (!response.ok) {
        const error = await response
          .json()
          .catch(() => ({ detail: response.statusText }));
        throw new Error(error.detail || "Failed to update search preferences");
      }

      return response.json();
    } catch (error: any) {
      throw error;
    }
  },
};
