const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface JobApplicationRequest {
  candidate_id: string;
  application_id?: string;
}

export interface JobApplicationResponse {
  success: boolean;
  message: string;
  application_id: string;
  status: string;
}

export const automationApi = {
  triggerJobApplication: async (
    request: JobApplicationRequest
  ): Promise<JobApplicationResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/automation/apply`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response
        .json()
        .catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to trigger job application");
    }

    return response.json();
  },
};
