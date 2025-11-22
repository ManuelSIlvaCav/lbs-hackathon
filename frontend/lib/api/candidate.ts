import { Candidate } from "@/lib/types/candidate";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const candidateApi = {
  getCandidate: async (candidateId: string): Promise<Candidate> => {
    const response = await fetch(`${API_BASE_URL}/api/candidates/${candidateId}`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch candidate: ${response.statusText}`);
    }
    
    return response.json();
  },

  getCandidates: async (): Promise<Candidate[]> => {
    const response = await fetch(`${API_BASE_URL}/api/candidates`);
    
    if (!response.ok) {
      throw new Error(`Failed to fetch candidates: ${response.statusText}`);
    }
    
    return response.json();
  },

  uploadAndParseCV: async (candidateId: string, file: File): Promise<Candidate> => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(
      `${API_BASE_URL}/api/candidates/${candidateId}/upload-cv`,
      {
        method: "POST",
        body: formData,
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to upload and parse CV");
    }

    return response.json();
  },

  updateCandidateMetadata: async (candidateId: string, metadata: Candidate["metadata"]): Promise<Candidate> => {
    const response = await fetch(
      `${API_BASE_URL}/api/candidates/${candidateId}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ metadata }),
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(error.detail || "Failed to update candidate metadata");
    }

    return response.json();
  },
};
