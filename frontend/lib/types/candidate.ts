// Types matching the backend CandidateModel

export interface ContactInfo {
  full_name: string | null;
  phone: string | null;
  email: string | null;
  linkedin: string | null;
  other_links: string[];
}

export interface EducationItem {
  degree_type: string | null;
  degree_name: string | null;
  major: string | null;
  institution: string | null;
  start_date: string | null;
  end_date: string | null;
  grades: string | null;
  description: string | null;
}

export interface ExperienceItem {
  company_name: string | null;
  role_title: string | null;
  location: string | null;
  start_date: string | null;
  end_date: string | null;
  duration_years: number | null;
  industry_primary: string | null;
  industries_secondary: string[];
  company_type: string | null;
  role_functions: string[];
  hard_skills: string[];
  soft_skills: string[];
  summary: string | null;
  is_internship: boolean;
}

export interface SkillsSummary {
  hard_skills_overall: string[];
  soft_skills_overall: string[];
  software_knowledge: string[];
  languages: string[];
  interests: string[];
  other_attributes: string | null;
}

export interface ExperienceByRoleItem {
  role_family: string | null;
  total_years: number | null;
}

export interface IndustryPrimarySummaryItem {
  industry: string | null;
  total_years: number | null;
}

export interface IndustrySecondarySummaryItem {
  industry: string | null;
  total_years: number | null;
}

export interface CompanyTypeSummaryItem {
  company_type: string | null;
  total_years: number | null;
}

export interface RoleFunctionSummaryItem {
  role_function: string | null;
  total_years: number | null;
}

export interface Meta {
  total_experience_years: number | null;
  experience_by_role: ExperienceByRoleItem[];
  industry_primary_summary: IndustryPrimarySummaryItem[];
  industry_secondary_summary: IndustrySecondarySummaryItem[];
  company_type_summary: CompanyTypeSummaryItem[];
  role_function_summary: RoleFunctionSummaryItem[];
}

export interface CategorizationSchema {
  contact_info: ContactInfo;
  education: EducationItem[];
  experience: ExperienceItem[];
  skills_summary: SkillsSummary;
  meta: Meta;
}

export interface CandidateMetadata {
  categorization_schema: CategorizationSchema | null;
}

export interface SearchPreferences {
  locations?: string[];
  visa_sponsorship?: boolean;
  languages?: string[];
  role_type?: string[];
  role_level?: string[];
  minimum_salary?: number;
  role_priorities?: string[];
  favourite_industries?: string[];
  hidden_industries?: string[];
  favourite_technologies?: string[];
  hidden_technologies?: string[];
  company_size?: string[];
  followed_companies?: string[];
  hidden_companies?: string[];
}

export interface Candidate {
  _id: string;
  name: string;
  email: string | null;
  metadata: CandidateMetadata | null;
  search_preferences?: SearchPreferences | null;
  created_at: string;
  updated_at: string;
}
