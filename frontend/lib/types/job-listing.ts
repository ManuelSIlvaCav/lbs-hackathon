// Job Info from parser
export interface JobInfo {
  job_title: string | null;
  company_name: string | null;
  location: string | null;
  industry_primary: string | null;
  job_company_type: string | null;
  overall_role_functions: string[];
}

// Experience by role item
export interface ExperienceByRoleItem {
  role_function: string | null;
  experience_years_min: number | null;
  experience_years_max: number | null;
}

// Requirements (minimum and preferred)
export interface JobRequirements {
  experience_years_min: number | null;
  experience_years_max: number | null;
  experience_by_role: ExperienceByRoleItem[];
  role_functions: string[];
  company_type_background: string[];
  industry_background: string[];
  hard_skills: string[];
  soft_skills: string[];
  degrees: string[];
  languages: string[];
  other_requirements: string[];
  summary: string | null;
}

// Full requirements structure
export interface JobRequirementsStructure {
  minimum: JobRequirements;
  preferred: JobRequirements;
}

// Categorization schema from parser
export interface JobCategorizationSchema {
  job_info: JobInfo;
  requirements: JobRequirementsStructure;
  description_summary: string | null;
}

// Metadata
export interface JobListingMetadata {
  categorization_schema: JobCategorizationSchema | null;
}

// Main job listing interface (aligned with JobListingResponse from backend)
export interface JobListing {
  _id: string;
  url: string;
  title: string | null;
  company: string | null;
  company_id: string | null;
  location: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  description: string | null;
  posted_at: string | null;
  last_seen_at: string | null;
  provider: string;
  provider_job_id: string | null;
  job_enrichment_id: string | null;
  metadata: JobListingMetadata | null;
  status: string;
  created_at: string;
  updated_at: string | null;
}

export interface JobListingCreate {
  url: string;
  title: string;
  company?: string;
  company_id?: string;
  location?: string;
  city?: string;
  state?: string;
  country?: string;
  description?: string;
  posted_at?: string;
  last_seen_at?: string;
  provider?: string;
  provider_job_id?: string;
  job_enrichment_id?: string;
}

export interface JobListingUpdate {
  url?: string;
  title?: string;
  company?: string;
  location?: string;
  description?: string;
  metadata?: JobListingMetadata;
  status?: string;
}
