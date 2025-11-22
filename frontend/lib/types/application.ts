import { Candidate } from "./candidate";
import { JobListing } from "./job-listing";

export interface Application {
  _id: string;
  job_listing_id: string;
  candidate_id: string;
  accuracy_score: number | null;
  status: string;
  created_at: string;
  updated_at: string;
  job_listing?: JobListing;
  candidate?: Candidate;
}

export interface ApplicationCreate {
  job_listing_id: string;
  candidate_id: string;
  accuracy_score?: number;
  status?: string;
}

export interface RecommendationRequest {
  candidate_id: string;
}
