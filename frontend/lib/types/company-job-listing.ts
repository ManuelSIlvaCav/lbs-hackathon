/**
 * Company job listing - matches JobListingModel from backend
 * This represents jobs available at a specific company
 */
export interface CompanyJobListing {
  _id: string;
  url: string;
  title?: string;
  company?: string;
  company_id?: string;
  location?: string;
  city?: string;
  state?: string;
  country?: string;
  description?: string;
  posted_at?: string;
  last_seen_at?: string;
  status?: string;
  created_at?: string;
  updated_at?: string;
  origin?: "linkedin" | "greenhouse" | "workday" | "careers" | "other";
  origin_domain?: string;
  profile_categories?: string[];
  role_titles?: string[];
  employement_type?: string;
  work_arrangement?: string;
  listing_status?: "active" | "expired";
  source_status?: "enriched" | "scrapped" | "active";
  salary_range_min?: number;
  salary_range_max?: number;
  salary_currency?: string;
}
