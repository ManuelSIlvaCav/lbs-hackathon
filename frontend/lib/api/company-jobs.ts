import { JobListing } from "../types/job-listing";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Fetch job listings for a specific company
 */
export async function getCompanyJobListings(
  companyId: string,
  token?: string
): Promise<JobListing[]> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(
    `${API_BASE_URL}/api/companies/${companyId}/job-listings`,
    {
      method: "GET",
      headers,
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || "Failed to fetch job listings");
  }

  return response.json();
}

/**
 * Check if a company has been enriched (has enrichment data)
 */
export async function checkCompanyEnriched(
  companyId: string,
  token?: string
): Promise<boolean> {
  try {
    // Try to fetch job listings - this will fail if not enriched
    await getCompanyJobListings(companyId, token);
    return true;
  } catch (error) {
    // If the error mentions "not been enriched", return false
    if (error instanceof Error && error.message.includes("not been enriched")) {
      return false;
    }
    // For other errors, we assume it's enriched but jobs failed
    return true;
  }
}
