/**
 * Company job listing from Apollo.io provider
 * This represents jobs available at a specific company
 */
export interface CompanyJobListing {
  _id: string;
  title: string;
  url: string;
  location?: string;
  city?: string;
  state?: string;
  country?: string;
  posted_at?: string;
  last_seen_at?: string;
  provider: string;
  provider_job_id: string;
}
