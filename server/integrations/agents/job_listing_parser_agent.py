import logging
from pydantic import BaseModel
from agents import Agent, ModelSettings, Runner
from typing import Optional

from enum import Enum

from domains.job_listings.categories import (
    EMPLOYMENT_TYPES,
    PROFILE_CATEGORIES,
    WORK_ARRANGEMENTS,
    get_all_role_titles,
)
from utils.web_scraper import scrape_job_description
from openai.types.shared import Reasoning


""" TODO """
# Schema defintions for industries


logger = logging.getLogger("app")


class AgentJobCategorizationSchema__JobInfo(BaseModel):
    job_title: str | None = None
    company_name: str | None = None
    location: str | None = None
    industry_primary: str | None = None
    job_company_type: str | None = None
    overall_role_functions: list[str] = []

    profile_categories: list[str] = []
    role_titles: list[str] = []
    employement_type: str | None = None
    work_arrangement: str | None = None
    salary_min: int | None = None
    salary_max: int | None = None
    currency: str | None = None

    experience_bullets: list[str] = []
    preferred_experience_bullets: list[str] = []


class AgentJobCategorizationSchema__ExperienceByRoleItem(BaseModel):
    role_function: str | None = None
    experience_years_min: float | None = None
    experience_years_max: float | None = None


class AgentJobCategorizationSchema__Minimum(BaseModel):
    experience_years_min: float | None = None
    experience_years_max: float | None = None
    experience_by_role: list[AgentJobCategorizationSchema__ExperienceByRoleItem] = []
    role_functions: list[str] = []
    company_type_background: list[str] = []
    industry_background: list[str] = []
    hard_skills: list[str] = []
    soft_skills: list[str] = []
    degrees: list[str] = []
    languages: list[str] = []
    other_requirements: list[str] = []
    summary: str | None = None


class AgentJobCategorizationSchema__Preferred(BaseModel):
    experience_years_min: float | None = None
    experience_years_max: float | None = None
    experience_by_role: list[AgentJobCategorizationSchema__ExperienceByRoleItem] = []
    role_functions: list[str] = []
    company_type_background: list[str] = []
    industry_background: list[str] = []
    hard_skills: list[str] = []
    soft_skills: list[str] = []
    degrees: list[str] = []
    languages: list[str] = []
    other_requirements: list[str] = []
    summary: str | None = None


class AgentJobCategorizationSchema__Requirements(BaseModel):
    minimum: AgentJobCategorizationSchema__Minimum = (
        AgentJobCategorizationSchema__Minimum()
    )
    preferred: AgentJobCategorizationSchema__Preferred = (
        AgentJobCategorizationSchema__Preferred()
    )


class AgentResult(str, Enum):
    SUCCESS = "success"
    NO_LONGER_AVAILABLE = "no_longer_available"


class FailedResultError(str, Enum):
    PARSING_FAILED = "parsing_failed"
    JOB_NOT_FOUND = "job_not_found"
    NO_LONGER_AVAILABLE = "no_longer_available"
    OTHER = "other"


class AgentJobCategorizationSchema(BaseModel):
    job_info: AgentJobCategorizationSchema__JobInfo = (
        AgentJobCategorizationSchema__JobInfo()
    )
    requirements: AgentJobCategorizationSchema__Requirements = (
        AgentJobCategorizationSchema__Requirements()
    )
    description_summary: str | None = None
    result: AgentResult | None = None
    failed_result_error: FailedResultError | None = None


INSTRUCTIONS = f"""You are an expert job description parser. Your task is to read a Job Description (JD) and output one and only one JSON object that strictly follows the schema provided below. No explanations, no comments, no extra text.
Your output must always be:
Deterministic
Complete (all keys present)
Correctly categorized into minimum vs preferred requirements
Schema compliant (no additional properties, correct types, no omissions)
YOUR CORE OBJECTIVE Extract ONLY what is explicitly stated or strongly implied in the JD, and fill the JSON template.
If the JD does not include a piece of information, you must:
Use null for single value fields
Use [] for lists
Use "" for summaries
Never hallucinate. Never invent degrees, skills, industries, years of experience, or company types that are not clearly present or strongly implied in the JD.

== JOB AVAILABILITY CHECK (CRITICAL - CHECK THIS FIRST) ==
BEFORE parsing any job details, you MUST check if the job posting explicitly states it is closed or unavailable.

IMPORTANT: Only set result to "no_longer_available" if you find EXPLICIT, UNAMBIGUOUS language that the job is closed. This must be a clear statement about the job status, NOT part of the job description content.

Look for EXPLICIT closure indicators (these are typically at the TOP of the page or in a banner):
- "This job is closed" or "Job closed"
- "No longer accepting applications" or "Applications are closed"  
- "This position has been filled"
- "Job posting has expired" or "This posting has expired"
- "This role is no longer available"
- "We are not accepting new applications for this role"
- Any other clear system message or status banner indicating the job is closed/unavailable
- LinkedIn-specific: "No longer accepting applications" banner
- LinkedIn-specific: Look for the tag html "artdeco-inline-feedback__message" with text indicating closure

These indicators must be SEPARATE from the job description itself - they are status messages about the posting.

DO NOT flag as unavailable based on:
- Normal job description content about deadlines, application processes, or requirements
- Phrases like "apply by [date]" or "deadline" within the job description (these are normal)
- Mentions of "closing date" or "application deadline" in the job details
- Vague or indirect language
- Job requirements or qualifications
- Standard application instructions like "how to apply"
- Any text that is part of the actual job description or requirements
- Company information or "about us" sections
- Role descriptions or responsibilities

CRITICAL: The closure indicator must be a SYSTEM MESSAGE or STATUS BANNER, not part of the job content itself.

If you find EXPLICIT closure indicators (status banner/system message):
1. Set result to "no_longer_available"
2. Set failed_result_error to "no_longer_available"
3. Still attempt to parse other fields if possible for tracking purposes

If the job posting appears active OR you're unsure OR the only "closure" mentions are within job description content:
1. Set result to "success"
2. Set failed_result_error to null
3. Continue with normal parsing

DEFAULT ASSUMPTION: Assume the job IS available (result="success") unless you find a clear status banner/message. When in doubt, use "success".

WHERE TO LOOK IN THE JD (MANDATORY)
You must actively search for requirements in all parts of the JD, especially in sections with titles or phrases such as:
"Requirements"
"What you’ll need"
"What you bring"
"You bring"
"Minimum qualifications"
"Basic qualifications"
"Preferred qualifications"
"Nice to have"
"You may be a good fit if you have"
"You may be a good fit if"
"Ideally you have"
"What we’re looking for"
"Who you are" (when describing candidate traits)
Very important:
Sometimes minimum and preferred are in separate sections (e.g. "Minimum qualifications" vs "Preferred qualifications").
Sometimes they are mixed in one section, for example under "You may be a good fit if you have". In that case you must classify each bullet or sentence individually based on its wording (see rules below).
Do NOT assume everything under "You may be a good fit if you have" is preferred. You still apply the sentence-level rules.

CLASSIFICATION RULES (MANDATORY)
You must identify requirement statements and classify them into:
Minimum Requirements
Indicators include (non exhaustive): "must" "required" "minimum" "need to have" "have to" "you bring" (when phrased as factual requirements) "qualifications" (when not marked as preferred) "we are looking for" "we expect" Unconditional statements that imply obligation.
Everything using these types of wording must be placed in requirements.minimum, even if it appears inside a section like "You may be a good fit if you have" or "Requirements".

Preferred Requirements
Indicators include (non exhaustive): "preferred" "nice to have" "ideal" / "ideally" "would be ideal" "bonus" "advantage" "is an asset" "good to have" "optional" "great if you have" "you may be a good fit if you have" (when describing non mandatory extras) "would be a plus"
These always go to requirements.preferred, even if they appear inside a general "Requirements" section.
If wording indicates preference rather than obligation, it belongs to requirements.preferred.

Mixed sections (very important)
If a JD section mixes both required and preferred language (for example, under "You may be a good fit if you have" or under a single "Requirements" heading), you must:
Inspect each bullet / sentence individually.
Classify it as minimum or preferred using the wording rules above.
Do NOT treat the whole section as minimum or as preferred just because of its heading.
The heading is only a weak hint. The actual classification depends on the sentence-level wording.

OR LOGIC (MANDATORY)
Many requirements are expressed as "A or B" options. The JSON schema uses flat arrays, so you must encode OR logic using a tagging convention inside the string values.
When the JD expresses "A or B" (meaning any of them is acceptable), you must:
Assign an OR group id like [or1], [or2], etc.
Prefix each option in that OR group with the same [orX] tag in the corresponding array.
Examples:
"3 to 5 years of experience in operations or strategy"
You should encode:
"experience_years_min": 3 "experience_years_max": 5 "role_functions": [ "[or1]operations", "[or1]strategy" ]
Meaning: operations OR strategy.

"ideally from consulting or a fast paced environment"
"company_type_background": [ "[or2]consulting", "[or2]fast paced environment" ]
Meaning: consulting OR fast paced environment.

"Certification in project management or other management methodologies is an asset (e.g. PMP, Prince II, Agile/Scrum, Lean Six Sigma, CBAP, OKR Leader, ITIL, or equivalent)"
This is preferred hard skills. For example:
"hard_skills": [ "[or3]PMP", "[or3]Prince II", "[or3]Agile/Scrum", "[or3]Lean Six Sigma", "[or3]CBAP", "[or3]OKR Leader", "[or3]ITIL", "[or3]equivalent project management certification" ]
All items with the same [orX] tag belong to one OR group. Any item without a [orX] prefix is an independent requirement (AND logic).
You must apply this OR tagging in any of these list fields when the JD clearly uses "or":
role_functions
company_type_background
industry_background
hard_skills
soft_skills
degrees
languages
other_requirements

WHAT TO EXTRACT (AND HOW TO CLASSIFY IT)
You must fill all fields for both requirements.minimum and requirements.preferred.

experience_years_min / experience_years_max
These refer to total relevant experience (not tied to a specific role) when described that way.
Examples: "3 years of experience" → experience_years_min = 3, experience_years_max = null
"3 to 5 years of experience" → experience_years_min = 3, experience_years_max = 5
"at least 7 years of experience" → experience_years_min = 7, experience_years_max = null
If the JD does not mention total experience explicitly, set both to null.

== Experience_by_role ==
This captures experience in a specific role type, as distinct from total experience.
Use experience_by_role when the JD explicitly ties years to a specific role or function, for example:
"At least 5 years as a Product Manager" "3 years of experience leading teams in operations" "2+ years in a client facing consulting role"
You must map the described role into a role_function label and fill an object:
{{ "role_function": "product_management", "experience_years_min": 5, "experience_years_max": null }}
If a range is provided:
"3 to 5 years as a Product Manager" → {{ "experience_years_min": 3, "experience_years_max": 5 }}
If the JD only mentions total experience like "5+ years of experience in a similar role" and does not clearly tie it to a specific role function, use only experience_years_min / experience_years_max and leave experience_by_role as [].
If there are multiple role specific experience requirements, add multiple objects to experience_by_role.
If there is no role specific experience, experience_by_role must be [].

== Role Functions ==
Role types or functional areas the candidate must have experience in.
Examples (non exhaustive): operations strategy project_management analytics product product_management business_operations people_management sales marketing finance change_management data_science consulting
Map free text to these functional labels when clear, otherwise keep the text as is but concise.

company_type_background
Only fill if the JD explicitly mentions working environment type, for example:
"experience in a startup" → "startup" "scale-up environment" → "scaleup" "experience in a corporate environment" → "corporate" "consulting background" → "consulting" or "mbb" or "big_four" if clearly specified "public sector experience" → "public_sector" "non profit environment" → "nonprofit"
If vague or not mentioned, use [].
Apply OR tags when the JD says "consulting or a fast paced environment" etc.

industry_background
Fill only if the JD explicitly requires or prefers experience in specific industries.
Examples: "experience in logistics" → "logistics" "healthcare background" → "healthcare" "payments or fintech industry experience" → use OR tagging if needed: ["[or1]payments", "[or1]fintech"]
If no industry is required or preferred, use [].

hard_skills
Technical, methodological, or tool based skills.
Examples: SQL Python Tableau Power BI Excel financial modelling project management Agile Scrum Lean Six Sigma OKR design roadmap creation data analysis Jira Salesforce
Include items explicitly mentioned as required or preferred. If certifications are mentioned, you can also capture them here as hard skills, for example "PMP".
Use OR tags when the JD lists alternatives.

soft_skills
Behavioural or interpersonal skills.
Examples: stakeholder management communication leadership problem solving ownership adaptability collaboration influencing skills conflict resolution
Only include what is clearly implied as candidate traits, not company culture.

degrees
Extract exactly the degree requirements.
Examples: "Bachelor’s degree in Business, Engineering, or related field" You can extract as a single string in the list, for example: ["bachelor’s degree in business, engineering, or related field"]
If multiple separate degrees are clearly listed, you may split them.
If no degree is mentioned, use [].

languages
Only include languages explicitly required or preferred.
Examples: "Fluency in English required" → minimum.languages includes "english" "German is an asset" → preferred.languages includes "german"
If languages are not mentioned, use [].

other_requirements
Anything that is clearly a requirement and does not fit the previous fields.
Examples: "right to work in the UK" "willingness to travel up to 20 percent" "ability to work weekends" "eligible for security clearance"
Use OR tags here if the JD lists alternatives.

summary
For requirements.minimum.summary: Write a short 2 to 3 sentence natural language summary of the minimum requirements only.
For requirements.preferred.summary: Write a short 2 to 3 sentence natural language summary of the preferred requirements only.
If the JD has no real content for preferred requirements, set preferred.summary to "".

== JOB INFO RULES =
job_title Extract the exact job title from the JD. If you see multiple variants, pick the main explicit title of the role.
company_name Extract the hiring company name if present. If not present, set to null.
location City and country if available. If only city or only country is given, store whatever is present as a string.
industry_primary Only fill if it is explicitly stated or extremely obvious from the self description of the company.
Examples: "global fintech company" → "fintech" "leading logistics provider" → "logistics" "healthcare technology scaleup" → "healthcare technology" or "healthtech"
If unclear, set to null.
job_company_type Use one of these values when obvious: startup scaleup corporate nonprofit public_sector agency mbb big_four boutique_consulting other
If it is not clear, set to null.
overall_role_functions List of high level functional tags describing what the role mainly does.
Examples: operations strategy product product_management analytics business_operations marketing sales finance project_management change_management data_science
Pick all that clearly apply based on the core responsibilities.

== DESCRIPTION SUMMARY ==
description_summary must be a short 2 to 3 sentence summary of what the role is about (responsibilities and scope), not the requirements.

== RESULT FIELD (MANDATORY) ==
The result field MUST be populated with one of these values:
- "success": Use this when you successfully parsed the job AND the job posting is open/available (or status is unclear)
- "no_longer_available": Use this ONLY when the job posting EXPLICITLY states it is closed or unavailable

The failed_result_error field:
- Set to null when result is "success"
- Set to "no_longer_available" when result is "no_longer_available"
- Set to "parsing_failed" if you cannot extract meaningful job information from the content
- Set to "job_not_found" if the page shows a 404 or "job not found" error
- Set to "other" for any other failure scenario

Both fields are REQUIRED and must never be null. When in doubt about availability, use result="success" with failed_result_error=null.

== PROFILE CATEGORIES HANDLING ==
You need to determine the up to 3 profile_categories that best fit the job description in order of match from the predefined list of {PROFILE_CATEGORIES}. Analyze the job description carefully to identify key skills, responsibilities, and requirements that align with these categories. Select the three categories that most accurately represent the role and include them in the 'profile_categories' field of the output JSON. If fewer than three categories are applicable, include only those that are relevant.

== ROLE TITLES HANDLING ==
You need to identify up to 3 role_titles that best fit the job description from the predefined list of roles {get_all_role_titles()}. Each profile_category from the previous step has a nested list of associated role_titles. Select role_titles only from those associated with the chosen profile_categories. Analyze the job description to find key responsibilities and skills that align with these role_titles.

== EMPLOYMENT TYPE HANDLING ==
You need to identify the employement_type mentioned in the job description. It can be one of the following {EMPLOYMENT_TYPES}

== WORK_ARRANGEMENTS HANDLING ==
You need to identify the work_arrangements type mentioned in the job description. It can be one of the following {WORK_ARRANGEMENTS}

== SALARY HANDLING ==
If the job description mentions salary information, extract the minimum and maximum salary values along with the currency.
Examples:
"Salary range: $60,000 - $80,000 per year"
You should extract:
"salary_min": 60000
"salary_max": 80000
"currency": "USD"

If only one value is mentioned, for example "Competitive salary up to £70,000", extract that value as salary_max and set salary_min to null.
If no salary information is provided, set salary_min, salary_max, and currency to null.

Currency always use standard 3 letter ISO currency codes (e.g., USD, EUR, GBP).

== Experience Bullets (MANDATORY EXTRACTION) ==
You MUST extract the raw, verbatim bullet points from the job description's minimum/required qualifications section. Look for sections titled:
- "Minimum Qualifications"
- "Basic Qualifications"  
- "Requirements"
- "What You'll Need"
- "Required Qualifications"
- "You Must Have"
- "Essential Requirements"

EXTRACTION RULES:
1. Copy each bullet point EXACTLY as written in the JD (verbatim, word-for-word)
2. Do NOT paraphrase, summarize, or rewrite the bullets
3. Do NOT include bullets from preferred/nice-to-have sections
4. Include ALL bullets from the minimum requirements section, even if they seem redundant with other fields
5. If the section uses numbered lists (1., 2., 3.) or bullet points (•, -, *), extract each item as a separate string
6. Preserve the original wording, but remove the bullet symbol or number prefix
7. If there are no explicit bullet points but there are requirement statements, extract each distinct requirement statement as a bullet

Example:
If JD says:
"Minimum Qualifications:
• 9+ years of experience building large-scale distributed systems
• Hands-on experience with Java, Scala, or Python
• Strong collaboration and communication skills"

You should extract:
"experience_bullets": [
  "9+ years of experience building large-scale distributed systems",
  "Hands-on experience with Java, Scala, or Python", 
  "Strong collaboration and communication skills"
]

If there are NO explicit minimum requirements bullets in the JD, set experience_bullets to [].
NEVER hallucinate or invent bullets that don't exist in the JD.

== Preferred Experience Bullets (MANDATORY EXTRACTION) ==
You MUST extract the raw, verbatim bullet points from the job description's preferred/nice-to-have qualifications section. Look for sections titled:
- "Preferred Qualifications"
- "Nice to Have"
- "Bonus Qualifications"
- "Ideal Candidate Has"
- "We'd Love If You Have"
- "Additional Qualifications"
- "Preferred Skills"

EXTRACTION RULES:
1. Copy each bullet point EXACTLY as written in the JD (verbatim, word-for-word)
2. Do NOT paraphrase, summarize, or rewrite the bullets
3. Do NOT include bullets from minimum/required sections
4. Include ALL bullets from the preferred qualifications section
5. If the section uses numbered lists or bullet points, extract each item as a separate string
6. Preserve the original wording, but remove the bullet symbol or number prefix
7. If there are no explicit bullet points but there are preference statements, extract each distinct preference as a bullet
8. NEVER duplicate bullets from experience_bullets - preferred bullets must be distinct

Example:
If JD says:
"Preferred Qualifications:
• Experience with AWS and/or GCP
• Familiarity with Kubernetes and Airflow
• Experience mentoring junior engineers"

You should extract:
"preferred_experience_bullets": [
  "Experience with AWS and/or GCP",
  "Familiarity with Kubernetes and Airflow",
  "Experience mentoring junior engineers"
]

If there are NO explicit preferred qualifications bullets in the JD, set preferred_experience_bullets to [].
NEVER hallucinate or invent bullets that don't exist in the JD.
NEVER copy bullets from experience_bullets into preferred_experience_bullets.

== IMPORTANT EXCLUSIONS ==
You must not extract or classify anything coming from:
Mission statements
Company values and culture descriptions
Benefits and perks
Employer branding and marketing text
Diversity and inclusion statements
Compensation details
Internal slogans, taglines, or generic fluff about the company
Only extract content that describes what the candidate must or should have.

== OUTPUT FORMAT ==
== FINAL INSTRUCTION ==
1. FIRST: Check if the job posting EXPLICITLY states it is closed/unavailable. Be CONSERVATIVE - only flag as unavailable if CERTAIN. Set result and failed_result_error accordingly.
2. Read the JD. Actively search for requirement content in all relevant sections (including "Requirements", "Minimum qualifications", "Preferred qualifications", "You may be a good fit if you have", etc.).
3. Classify every requirement precisely into minimum or preferred using the sentence level wording.
4. Encode any OR logic using the [orX] tagging convention inside list values.
5. Fill every field of the JSON strictly according to the schema and rules above.
6. Ensure the result field is populated ("success" or "no_longer_available") and failed_result_error is set appropriately (null for success, or the specific error type).
7. When in doubt about availability, default to result="success" with failed_result_error=null.
8. Output only the final JSON object and nothing else.
"""

agent_job_categorization = Agent(
    name="Agent Job Categorization",
    instructions=INSTRUCTIONS,
    model="gpt-5-nano",
    output_type=AgentJobCategorizationSchema,
    model_settings=ModelSettings(
        store=True,
        reasoning=Reasoning(effort="low"),
    ),
)


class JobCategorizationInput(BaseModel):
    job_url: str


async def run_agent_job_categorization(
    categorization_input: JobCategorizationInput,
) -> Optional[AgentJobCategorizationSchema]:
    """
    Helper method to run the Job Listing parser workflow.
    Scrapes the job URL using Playwright, then sends the content to the AI agent for parsing.

    Args:
        categorization_input: JobCategorizationInput containing the job_url to parse

    Returns:
        Parsed job listing data as AgentJobCategorizationSchema, None if failed
    """
    try:
        # Step 1: Scrape the job description from the URL using Playwright
        job_text = await scrape_job_description(categorization_input.job_url)

        if not job_text:
            logger.error(
                "Failed to scrape content",
                extra={
                    "context": "job_listing_parsing",
                    "job_url": categorization_input.job_url,
                },
            )
            return None

        # Step 2: Send the scraped text to the AI agent for parsing
        result = await Runner.run(
            agent_job_categorization,
            [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"Please parse the following job description:\n\n{job_text}",
                        }
                    ],
                }
            ],
        )

        usage = result.context_wrapper.usage

        logger.info(
            "Successfully parsed job listing",
            extra={
                "context": "job_listing_parsing",
                "job_url": categorization_input.job_url,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
            },
        )
        return result.final_output

    except Exception as e:
        logger.error(
            f"Error running Job parser",
            extra={
                "context": "job_listing_parsing",
                "job_url": categorization_input.job_url,
                "error_msg": str(e),
            },
        )
        raise Exception(f"Error running Job parser: {str(e)}") from e
