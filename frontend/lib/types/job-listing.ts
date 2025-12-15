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

// Company info embedded in job listing
export interface CompanyInfo {
  _id: string;
  name?: string;
  company_url?: string;
  linkedin_url?: string;
  logo_url?: string;
  domain?: string;
  industries?: string[];
  description?: string;
}

// Main job listing interface (aligned with JobListingModel from backend)
// Note: Provider tracking moved to JobListingSourceModel
export interface JobListing {
  _id: string;
  url: string;
  title?: string | null;
  company?: string | null;
  company_id?: string | null;
  location?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  description?: string | null;
  posted_at?: string | null;
  last_seen_at?: string | null;
  metadata?: JobListingMetadata | null;
  status?: string;
  created_at?: string;
  updated_at?: string | null;
  origin?: "linkedin" | "greenhouse" | "workday" | "careers" | "other";
  origin_domain?: string;
  profile_categories?: string[];
  role_titles?: string[];
  employement_type?: string;
  work_arrangement?: string;
  listing_status?: "active" | "expired";
  source_status?: "enriched" | "scrapped" | "active" | "deactivated";
  salary_range_min?: number;
  salary_range_max?: number;
  salary_currency?: string;
  company_info?: CompanyInfo | null;
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

export interface PaginatedJobListingResponse {
  items: JobListing[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}
