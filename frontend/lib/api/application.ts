import { Application, RecommendationRequest } from "@/lib/types/application";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const applicationApi = {
  getApplications: async (params: { 
    candidate_id: string; 
    skip?: number; 
    limit?: number; 
    include_details?: boolean 
  }): Promise<Application[]> => {
    const searchParams = new URLSearchParams();
    searchParams.append("candidate_id", params.candidate_id);
    if (params.skip !== undefined) searchParams.append("skip", params.skip.toString());
    if (params.limit !== undefined) searchParams.append("limit", params.limit.toString());
    if (params.include_details !== undefined) searchParams.append("include_details", params.include_details.toString());

    const url = `${API_BASE_URL}/api/applications?${searchParams.toString()}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch applications: ${response.statusText}`);
    }
    
    return response.json();
  },

  createRecommendations: async (request: RecommendationRequest): Promise<Application[]> => {
    const response = await fetch(`${API_BASE_URL}/api/applications/recommendation`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to create recommendations");
    }

    return response.json();
  },

  updateApplicationStatus: async (applicationId: string, status: string): Promise<Application> => {
    const response = await fetch(
      `${API_BASE_URL}/api/applications/${applicationId}/status?status=${encodeURIComponent(status)}`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to update application status");
    }

    return response.json();
  },

  deleteApplication: async (applicationId: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/api/applications/${applicationId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to delete application");
    }
  },
};
