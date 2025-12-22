/**
 * TypeScript types for CV Builder
 */

// ============================================================================
// CV Content Types
// ============================================================================

export interface CVContactInfo {
  full_name: string;
  email?: string | null;
  phone?: string | null;
  linkedin?: string | null;
  location?: string | null;
  website?: string | null;
  other_links: string[];
}

export interface CVEducationItem {
  id: string;
  institution: string;
  degree_type?: string | null;
  degree_name?: string | null;
  major?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  grades?: string | null;
  description?: string | null;
  bullets: string[];
}

export interface CVExperienceItem {
  id: string;
  company_name: string;
  role_title: string;
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  is_current: boolean;
  description?: string | null;
  bullets: string[];
}

export interface CVSkillsSummary {
  technical_skills: string[];
  soft_skills: string[];
  tools: string[];
  languages: string[];
  certifications: string[];
}

export interface CVProject {
  id: string;
  name: string;
  description?: string | null;
  url?: string | null;
  technologies: string[];
  bullets: string[];
}

export interface CVSummary {
  text: string;
}

// ============================================================================
// CV Document Type
// ============================================================================

export interface CVScore {
  _id?: string;
  cv_id: string;
  candidate_id: string;
  overall_score: number;
  breakdown: CVScoreBreakdown;
  top_recommendations: string[];
  scored_at: string;
  template_used?: string | null;
}

export interface CVBuilderDocument {
  _id?: string;
  candidate_id: string;
  contact_info: CVContactInfo;
  summary: CVSummary;
  experience: CVExperienceItem[];
  education: CVEducationItem[];
  skills: CVSkillsSummary;
  projects: CVProject[];
  selected_template: string;
  name: string;
  is_primary: boolean;
  created_at: string;
  updated_at: string;
  latest_score?: CVScore | null;
}

// ============================================================================
// Template Types
// ============================================================================

export interface TemplateSection {
  name: string;
  order: number;
  visible: boolean;
}

export interface CVTemplate {
  _id?: string;
  id: string; // Alias for template_id for convenience
  template_id: string;
  name: string;
  description: string;
  preview_image?: string | null;
  font_family: string;
  font_size_base: number;
  accent_color: string;
  line_spacing: number;
  margins: {
    top: number;
    bottom: number;
    left: number;
    right: number;
  };
  sections: TemplateSection[];
  is_ats_friendly: boolean;
  uses_columns: boolean;
  uses_graphics: boolean;
  is_default: boolean;
  created_at?: string;
  styling: {
    font_family: string;
    font_size_base: number;
    accent_color: string;
    line_spacing: number;
    margins: {
      top: number;
      bottom: number;
      left: number;
      right: number;
    };
  };
}

// ============================================================================
// Scoring Types
// ============================================================================

export type ScoreCategory =
  | "keyword_optimization"
  | "format_compliance"
  | "content_quality"
  | "section_completeness"
  | "action_verbs"
  | "quantification"
  | "length_optimization";

export interface CVScoreItem {
  category: ScoreCategory;
  score: number;
  weight: number;
  feedback: string;
  suggestions: string[];
}

export interface CVScoreBreakdown {
  keyword_optimization: CVScoreItem;
  format_compliance: CVScoreItem;
  content_quality: CVScoreItem;
  section_completeness: CVScoreItem;
  action_verbs: CVScoreItem;
  quantification: CVScoreItem;
  length_optimization: CVScoreItem;
}

// ============================================================================
// Enhancement Types
// ============================================================================

export type EnhancementType =
  | "bullet_improvement"
  | "summary_improvement"
  | "skill_suggestion"
  | "keyword_addition";

export interface BulletEnhancement {
  original: string;
  enhanced: string;
  explanation: string;
  improvements: string[];
}

export interface EnhancementSuggestion {
  section_type: string;
  section_id?: string | null;
  enhancement_type: EnhancementType;
  bullet_enhancements: BulletEnhancement[];
  summary_enhancement?: string | null;
  suggested_skills: string[];
  suggested_keywords: string[];
  generated_at?: string;
  target_job_title?: string | null;
  target_job_description?: string | null;
}

// ============================================================================
// Request/Response Types
// ============================================================================

export interface CVBuilderCreate {
  name?: string;
  from_parsed_cv?: boolean;
  selected_template?: string;
}

export interface CVBuilderUpdate {
  contact_info?: CVContactInfo;
  summary?: CVSummary;
  experience?: CVExperienceItem[];
  education?: CVEducationItem[];
  skills?: CVSkillsSummary;
  projects?: CVProject[];
  selected_template?: string;
  name?: string;
}

export interface EnhanceBulletsRequest {
  section_type: string;
  section_id: string;
  bullets: string[];
  context?: string | null;
  target_job_title?: string | null;
  target_job_description?: string | null;
}

export interface EnhanceSummaryRequest {
  current_summary: string;
  experience_context?: { role_title: string; company_name: string }[] | null;
  target_job_title?: string | null;
  target_job_description?: string | null;
}

export interface ExportCVRequest {
  template_id: string;
  format?: string;
}
