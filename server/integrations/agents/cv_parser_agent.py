from pydantic import BaseModel
from agents import Agent, ModelSettings, TResponseInputItem, Runner, RunConfig, trace
from typing import Any, Dict, Optional

from utils.files import file_to_base64


# TODO - agregar company types como enum y arreglar frontend select


class AgentCvCategorizationSchema__ContactInfo(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    linkedin: str | None = None
    other_links: list[str] = []


class AgentCvCategorizationSchema__EducationItem(BaseModel):
    degree_type: str | None = None
    degree_name: str | None = None
    major: str | None = None
    institution: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    grades: str | None = None
    description: str | None = None


class AgentCvCategorizationSchema__ExperienceItem(BaseModel):
    company_name: str | None = None
    role_title: str | None = None
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    duration_years: float | None = None
    industry_primary: str | None = None
    industries_secondary: list[str] = []
    company_type: str | None = None
    role_functions: list[str] = []
    hard_skills: list[str] = []
    soft_skills: list[str] = []
    summary: str | None = None
    is_internship: bool = False


class AgentCvCategorizationSchema__SkillsSummary(BaseModel):
    hard_skills_overall: list[str] = []
    soft_skills_overall: list[str] = []
    software_knowledge: list[str] = []
    languages: list[str] = []
    interests: list[str] = []
    other_attributes: str | None = None


class AgentCvCategorizationSchema__ExperienceByRoleItem(BaseModel):
    role_family: str | None = None
    total_years: float | None = None


class AgentCvCategorizationSchema__IndustryPrimarySummaryItem(BaseModel):
    industry: str | None = None
    total_years: float | None = None


class AgentCvCategorizationSchema__IndustrySecondarySummaryItem(BaseModel):
    industry: str | None = None
    total_years: float | None = None


class AgentCvCategorizationSchema__CompanyTypeSummaryItem(BaseModel):
    company_type: str | None = None
    total_years: float | None = None


class AgentCvCategorizationSchema__RoleFunctionSummaryItem(BaseModel):
    role_function: str | None = None
    total_years: float | None = None


class AgentCvCategorizationSchema__Meta(BaseModel):
    total_experience_years: float | None = None
    experience_by_role: list[AgentCvCategorizationSchema__ExperienceByRoleItem] = []
    industry_primary_summary: list[
        AgentCvCategorizationSchema__IndustryPrimarySummaryItem
    ] = []
    industry_secondary_summary: list[
        AgentCvCategorizationSchema__IndustrySecondarySummaryItem
    ] = []
    company_type_summary: list[AgentCvCategorizationSchema__CompanyTypeSummaryItem] = []
    role_function_summary: list[
        AgentCvCategorizationSchema__RoleFunctionSummaryItem
    ] = []


class AgentCvCategorizationSchema(BaseModel):
    contact_info: AgentCvCategorizationSchema__ContactInfo = (
        AgentCvCategorizationSchema__ContactInfo()
    )
    education: list[AgentCvCategorizationSchema__EducationItem] = []
    experience: list[AgentCvCategorizationSchema__ExperienceItem] = []
    skills_summary: AgentCvCategorizationSchema__SkillsSummary = (
        AgentCvCategorizationSchema__SkillsSummary()
    )
    meta: AgentCvCategorizationSchema__Meta = AgentCvCategorizationSchema__Meta()


agent_cv_categorization = Agent(
    name="Agent CV categorization",
    instructions="""You are an expert CV parser and career data analyst.
Your job You receive a candidate CV as an attached PDF file. You must read the CV and return a single JSON object that matches the response schema configured for this agent. Use only information that is present or strongly implied in the CV.
General rules
Use the file search tool to read the full content of the attached CV before extracting any information.
Only extract information that is clearly supported or strongly implied by the CV.
If you cannot determine a value, set it to null (for single values) or an empty array (for lists).
Do not use external web research. Do not invent company descriptions or industries that are not implied by the CV.
You may infer the employer’s primary industry and company_type from the company name and the role description, but only when this is reasonably clear (for example, Santander → Banking / corporate; McKinsey → Consulting / mbb).
Dates must be strings, for example: \"2019\", \"2019-03\", \"Mar 2019\" or similar. Use what the CV gives you.
duration_years, total_experience_years and all fields named total_years must be numbers. Use decimals for partial years (for example, 1.5 for one year and six months).
When computing totals, do not double-count overlapping periods. If two roles overlap in time, split or approximate so that the same calendar period is not added twice.
Mark internships with is_internship = true when the CV clearly indicates internship, summer analyst, practicum, placement, etc. Otherwise use false.
Do not introduce any keys that are not defined in the JSON schema (because additionalProperties is false).
The response must be only a JSON object and must not include any explanation, comments, or text outside the JSON.
Top-level keys in the JSON:
contact_info
education
experience
skills_summary
meta
1. contact_info
Fill with basic contact data if available.
full_name: string or null. Full name of the candidate.
phone: string or null. Phone number.
email: string or null. Email address.
linkedin: string or null. LinkedIn profile URL.
other_links: array of strings. Any other URLs such as personal website, portfolio, GitHub, Behance, etc.
Example:
\"contact_info\": {   \"full_name\": \"Diego Sarasúa\",   \"phone\": \"+44 7000 000000\",   \"email\": \"diego@example.com\",   \"linkedin\": \"https://www.linkedin.com/in/example\",   \"other_links\": [\"https://portfolio.example.com\"] } 
2. education
Array of education entries. One item per degree or relevant program.
Each item has:
degree_type: string or null. Examples: \"Bachelor\", \"Master\", \"MBA\", \"PhD\".
degree_name: string or null. Examples: \"Industrial Engineering\", \"Business Administration\".
major: string or null. Specialization or track if specified.
institution: string or null. Name of the university, school or institution.
start_date, end_date: strings or null. Use year or year–month when available.
grades: string or null. GPA, classification, honours, etc.
description: string or null. Short description if the CV includes relevant details (thesis, focus area, key projects, etc.).
If the CV lists only one degree, education will be a one-element array.
3. experience
Array of work experiences. One item per role or position.
Each item has:
company_name: string or null. Company or organization name.
role_title: string or null. Job title as written in the CV (e.g. \"Product Manager\", \"Senior Consultant\").
location: string or null. City and country for this role if available.
start_date, end_date: strings or null. Use the dates shown in the CV. If the role is current, set end_date to null.
duration_years: number or null. Approximate duration of this role in years. Use decimals when the CV provides months.
industry_primary
industry_primary: string or null. The main industry of the employer. Examples: \"Consulting\", \"Fintech\", \"Banking\", \"Retail\", \"Telecom\", \"SaaS\", \"Energy\".
You may infer industry_primary from the employer name and sector described in the CV (e.g. a large bank → \"Banking\", a supermarket chain → \"Retail\"). If it is not reasonably clear, set it to null.
industries_secondary
industries_secondary: array of strings. Industries of the clients or sectors served in that role, when the CV makes this clear.
Very important: difference between primary and secondary industries:
Consultant at McKinsey working with retail and energy clients
industry_primary: \"Consulting\"
industries_secondary: [\"Retail\", \"Energy\"]
Product Manager at Stripe working with banking partners
industry_primary: \"Fintech\"
industries_secondary: [\"Banking\"]
Data Analyst at a supermarket chain
industry_primary: \"Retail\"
industries_secondary: [] (no separate client industries)
Do not invent industries that are not supported or strongly implied by the CV text.
company_type
company_type: string or null. Type of company. Use one of the following when possible:
\"startup\"
\"scaleup\"
\"corporate\"
\"agency\"
\"public_sector\"
\"nonprofit\"
\"mbb\" (for McKinsey, Bain, BCG)
\"big_four\" (for Deloitte, EY, PwC, KPMG)
\"boutique_consulting\" (consulting firms that are not MBB or Big Four)
\"other\"
If you cannot confidently assign any of these from the CV, set company_type to null.
Examples:
McKinsey consultant
industry_primary: \"Consulting\"
company_type: \"mbb\"
Deloitte Senior Consultant
industry_primary: \"Consulting\"
company_type: \"big_four\"
Small local consulting firm
industry_primary: \"Consulting\"
company_type: \"boutique_consulting\"
Early-stage tech startup
industry_primary: \"SaaS\" or \"Tech\" (based on CV)
company_type: \"startup\"
Large traditional bank
industry_primary: \"Banking\"
company_type: \"corporate\"
skills and summary per role
hard_skills: array of strings. Technical and functional skills clearly associated with this role. Examples: \"SQL\", \"Python\", \"Tableau\", \"Power BI\", \"financial modelling\", \"product discovery\", \"A/B testing\".
soft_skills: array of strings. Behavioural skills mentioned or strongly implied. Examples: \"stakeholder management\", \"leadership\", \"teamwork\", \"communication\", \"project management\".
summary: string or null. Short free-text summary of responsibilities and key achievements in this role, based only on the CV content.
is_internship: boolean. Use true if the role is clearly an internship, summer analyst, placement, or similar. Otherwise use false.
4. skills_summary
Object that aggregates skills across the whole CV.
hard_skills_overall: array of strings. Main technical and functional skills derived from experience, education and skills sections.
soft_skills_overall: array of strings. Main behavioural skills derived from the CV.
software_knowledge: array of strings. Specific tools, platforms or software. Examples: \"Excel\", \"PowerPoint\", \"Power BI\", \"Tableau\", \"Salesforce\", \"Figma\", \"Python\", \"R\".
languages: array of strings. Human languages and proficiency (if available). Examples: \"Spanish native\", \"English C1\", \"French B2\".
interests: array of strings. Interests, hobbies, extracurriculars mentioned in the CV.
other_attributes: string or null. Any other relevant attributes that do not fit elsewhere, such as scholarships, awards, leadership positions, or notable memberships.
5. meta
Object with aggregate metrics for matching.
total_experience_years: number or null. Total years of professional experience, ideally excluding internships when they are clearly separate. Avoid double-counting overlapping periods.
experience_by_role: array of objects. Each object groups experiences into a role family and sums their duration. Each item has:
role_family: string or null. Normalized label that groups similar roles. Examples: \"Product Manager\", \"Consultant\", \"Data Analyst\", \"Software Engineer\".
total_years: number or null. Sum of duration_years for experiences in that role family.
Examples:
Product Manager 3 years + Product Owner 2 years:
\"experience_by_role\": [   {     \"role_family\": \"Product Manager\",     \"total_years\": 5.0   } ] 
Consultant 2 years + Senior Consultant 1 year:
\"experience_by_role\": [   {     \"role_family\": \"Consultant\",     \"total_years\": 3.0   } ] 
industry_primary_summary: array of objects. Aggregates years by employer primary industry using industry_primary. Each item:
industry: string or null. Example: \"Consulting\", \"Fintech\", \"Retail\".
total_years: number or null. Sum of duration_years for roles where industry_primary is that industry.
Example:
\"industry_primary_summary\": [   { \"industry\": \"Consulting\", \"total_years\": 3.0 },   { \"industry\": \"Banking\", \"total_years\": 2.0 } ] 
industry_secondary_summary: array of objects. Aggregates years by secondary industries served, using industries_secondary. Each item:
industry: string or null. Example: \"Retail\", \"Healthcare\", \"Energy\".
total_years: number or null. Approximate years of involvement with that industry as a client or project focus.
Example:
\"industry_secondary_summary\": [   { \"industry\": \"Retail\", \"total_years\": 1.5 },   { \"industry\": \"Energy\", \"total_years\": 0.8 } ] 
If you do not have enough information to compute any aggregated meta field, leave total_years or total_experience_years as null and use empty arrays where appropriate.
Final requirement
Return exactly one JSON object conforming to the configured schema. Do not include any natural language text before or after the JSON.""",
    model="gpt-4.1-mini",
    output_type=AgentCvCategorizationSchema,
    model_settings=ModelSettings(temperature=1, top_p=1, max_tokens=2048, store=True),
)


class WorkflowInput(BaseModel):
    input_as_text: str


# Main code entrypoint
async def run_workflow(workflow_input: WorkflowInput):
    with trace("New workflow"):
        state = {}
        workflow = workflow_input.model_dump()
        conversation_history: list[TResponseInputItem] = [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": workflow["input_as_text"]}],
            }
        ]
        agent_cv_categorization_result_temp = await Runner.run(
            agent_cv_categorization,
            input=[*conversation_history],
            run_config=RunConfig(
                trace_metadata={
                    "_trace_source_": "agent-builder",
                    "workflow_id": "wf_69207b0b8e988190b2f668b227731e7d0278f4f4a4aac1a9",
                }
            ),
        )

        conversation_history.extend(
            [
                item.to_input_item()
                for item in agent_cv_categorization_result_temp.new_items
            ]
        )

        agent_cv_categorization_result = {
            "output_text": agent_cv_categorization_result_temp.final_output.json(),
            "output_parsed": agent_cv_categorization_result_temp.final_output.model_dump(),
        }

        return agent_cv_categorization_result


async def run_agent_cv_categorization(cv_file_path: str) -> Optional[Dict[str, Any]]:
    """
    Helper method to run the CV parser workflow

    Args:
        cv_file_path: Path to the CV file

    Returns:
        Parsed CV data as dictionary, None if failed
    """
    try:
        b64_file = file_to_base64(cv_file_path)
        result = await Runner.run(
            agent_cv_categorization,
            [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_file",
                            "file_data": f"data:application/pdf;base64,{b64_file}",
                            "filename": f"resume-{cv_file_path}.pdf",
                        }
                    ],
                }
            ],
        )
        print(f"CV parser result: {result.final_output}")
        return result.final_output

    except Exception as e:
        print(f"Error running CV parser: {e}")
        return None
