import { Candidate } from "./candidate";
import { JobListing } from "./job-listing";

export interface DimensionScore {
  score: number;
  active: boolean;
  explanation: string;
}

export interface DimensionBreakdown {
  experience_total: DimensionScore;
  experience_by_role: DimensionScore;
  role_functions: DimensionScore;
  company_type_background: DimensionScore;
  industry_background: DimensionScore;
  hard_skills: DimensionScore;
  soft_skills: DimensionScore;
  degrees: DimensionScore;
  languages: DimensionScore;
  other_requirements: DimensionScore;
}

export interface ScoringMetadata {
  overall_match_score: number;
  deterministic_score: number;
  subjective_score: number;
  minimum_score: number;
  preferred_score: number;
  dimension_breakdown: {
    minimum: DimensionBreakdown;
    preferred: DimensionBreakdown;
  };
  subjective_rationale: string;
}

export interface Application {
  _id: string;
  job_listing_id: string;
  candidate_id: string;
  accuracy_score: number | null;
  scoring_metadata?: ScoringMetadata | null;
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
