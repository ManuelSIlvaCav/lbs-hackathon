const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Recommendation {
  _id: string;
  candidate_id: string;
  job_listing_id: string;
  company_id: string;
  reason?: string;
  recommendation_status: "pending" | "recommended" | "viewed" | "applied" | "rejected" | "deleted";
  created_at: string;
  recommended_at?: string;
  deleted_at?: string;
  job_listing?: any; // Will be populated with full job listing data
  company?: any; // Will be populated with full company data
}

export interface RecommendationCreate {
  candidate_id: string;
  job_listing_id: string;
  company_id: string;
  reason?: string;
  recommendation_status?: "pending" | "recommended" | "viewed" | "applied" | "rejected";
}

export interface PaginatedRecommendationResponse {
  items: Recommendation[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export const recommendationApi = {
  getRecommendations: async (params?: {
    candidate_id?: string;
    job_listing_id?: string;
    company_id?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<PaginatedRecommendationResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.candidate_id) searchParams.append("candidate_id", params.candidate_id);
    if (params?.job_listing_id) searchParams.append("job_listing_id", params.job_listing_id);
    if (params?.company_id) searchParams.append("company_id", params.company_id);
    if (params?.status) searchParams.append("status", params.status);
    if (params?.skip !== undefined) searchParams.append("skip", params.skip.toString());
    if (params?.limit !== undefined) searchParams.append("limit", params.limit.toString());

    const url = `${API_BASE_URL}/api/recommendations${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to get recommendations: ${response.statusText}`);
    }
    
    return response.json();
  },

  getRecommendation: async (recommendationId: string): Promise<Recommendation> => {
    const response = await fetch(`${API_BASE_URL}/api/recommendations/${recommendationId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch recommendation: ${response.statusText}`);
    }
    
    return response.json();
  },

  createRecommendation: async (data: RecommendationCreate): Promise<Recommendation> => {
    const response = await fetch(`${API_BASE_URL}/api/recommendations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to create recommendation");
    }

    return response.json();
  },

  createRecommendationsBulk: async (data: RecommendationCreate[]): Promise<{
    inserted_ids: string[];
    inserted_count: number;
    skipped_count: number;
  }> => {
    const response = await fetch(`${API_BASE_URL}/api/recommendations/bulk`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to create recommendations");
    }

    return response.json();
  },

  updateRecommendationStatus: async (
    recommendationId: string,
    status: "pending" | "recommended" | "viewed" | "applied" | "rejected"
  ): Promise<Recommendation> => {
    const response = await fetch(
      `${API_BASE_URL}/api/recommendations/${recommendationId}/status?status=${status}`,
      {
        method: "PATCH",
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to update recommendation status");
    }

    return response.json();
  },

  deleteRecommendation: async (recommendationId: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/api/recommendations/${recommendationId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to delete recommendation");
    }
  },
};
