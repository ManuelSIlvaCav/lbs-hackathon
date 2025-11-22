import { JobListing, JobListingCreate, JobListingUpdate } from "@/lib/types/job-listing";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const jobListingApi = {
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
