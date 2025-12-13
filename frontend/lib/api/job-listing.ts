import { JobListing, JobListingCreate, JobListingUpdate, PaginatedJobListingResponse } from "@/lib/types/job-listing";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const jobListingApi = {
  searchJobListings: async (params?: {
    company_id?: string;
    country?: string;
    city?: string;
    origin?: string;
    profile_category?: string;
    role_title?: string;
    skip?: number;
    limit?: number;
  }): Promise<PaginatedJobListingResponse> => {
    const searchParams = new URLSearchParams();
    if (params?.company_id) searchParams.append("company_id", params.company_id);
    if (params?.country) searchParams.append("country", params.country);
    if (params?.city) searchParams.append("city", params.city);
    if (params?.origin) searchParams.append("origin", params.origin);
    if (params?.profile_category) searchParams.append("profile_category", params.profile_category);
    if (params?.role_title) searchParams.append("role_title", params.role_title);
    if (params?.skip !== undefined) searchParams.append("skip", params.skip.toString());
    if (params?.limit !== undefined) searchParams.append("limit", params.limit.toString());

    const url = `${API_BASE_URL}/api/job-listings/search${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to search job listings: ${response.statusText}`);
    }
    
    return response.json();
  },

  getJobListings: async (params?: { skip?: number; limit?: number; status?: string }): Promise<JobListing[]> => {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined) searchParams.append("skip", params.skip.toString());
    if (params?.limit !== undefined) searchParams.append("limit", params.limit.toString());
    if (params?.status) searchParams.append("status", params.status);

    const url = `${API_BASE_URL}/api/job-listings${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch job listings: ${response.statusText}`);
    }
    
    return response.json();
  },

  getJobListing: async (jobListingId: string): Promise<JobListing> => {
    const response = await fetch(`${API_BASE_URL}/api/job-listings/${jobListingId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch job listing: ${response.statusText}`);
    }
    
    return response.json();
  },

  createJobListing: async (data: JobListingCreate): Promise<JobListing> => {
    const response = await fetch(`${API_BASE_URL}/api/job-listings`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to create job listing");
    }

    return response.json();
  },

  updateJobListing: async (jobListingId: string, data: JobListingUpdate): Promise<JobListing> => {
    const response = await fetch(`${API_BASE_URL}/api/job-listings/${jobListingId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to update job listing");
    }

    return response.json();
  },

  deleteJobListing: async (jobListingId: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/api/job-listings/${jobListingId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to delete job listing");
    }
  },

  getJobListingCount: async (status?: string): Promise<{ count: number }> => {
    const url = status 
      ? `${API_BASE_URL}/api/job-listings/stats/count?status=${status}`
      : `${API_BASE_URL}/api/job-listings/stats/count`;
    
    const response = await fetch(url);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch job listing count: ${response.statusText}`);
    }
    
    return response.json();
  },
};
