"""
Job listing categories and taxonomies
Organized by profile categories with specific role titles
"""

from typing import Dict, List

BLUE_COLLAR_PROFILE_CATEGORIES = {
    "Retail": [
        "Retail Sales Associate",
        "Store Manager",
        "Cashier",
        "Merchandiser",
        "Inventory Specialist",
        "Assistant Store Manager",
        "Retail Supervisor",
        "Customer Service Representative",
        "Loss Prevention Officer",
        "Visual Merchandiser",
    ],
    "Culinary": [
        "Chef",
        "Cook",
        "Sous Chef",
        "Pastry Chef",
        "Line Cook",
        "Kitchen Manager",
        "Food Service Worker",
        "Catering Manager",
        "Dishwasher",
        "Restaurant Manager",
    ],
    "Transportation & Delivery": [
        "Delivery Driver",
        "Truck Driver",
        "Courier",
        "Route Driver",
        "Bus Driver",
        "Forklift Operator",
        "Transport Driver",
        "Logistics Driver",
        "Chauffeur",
        "Delivery Coordinator",
    ],
    "Education": [
        "Teacher",
        "Professor",
        "Instructor",
        "Tutor",
        "Principal",
        "School Counselor",
        "Education Administrator",
        "Teaching Assistant",
        "Special Education Teacher",
        "Curriculum Developer",
    ],
    "Construction & Trades": [
        "Construction Worker",
        "Carpenter",
        "Electrician",
        "Plumber",
        "Construction Manager",
        "General Contractor",
        "HVAC Technician",
        "Welder",
        "Painter",
        "Construction Supervisor",
    ],
    "Administrative & Office Support": [
        "Administrative Assistant",
        "Office Manager",
        "Executive Assistant",
        "Receptionist",
        "Clerk",
        "Office Administrator",
        "Data Entry Clerk",
        "Administrative Coordinator",
        "Office Assistant",
        "Secretary",
        "Medical Secretary",
    ],
    "Healthcare & Medical": [
        "Registered Nurse",
        "Physician",
        "Medical Assistant",
        "Pharmacist",
        "Healthcare Administrator",
        "Physical Therapist",
        "Occupational Therapist",
        "Medical Technician",
        "Nurse Practitioner",
        "Radiologic Technologist",
        "Dental Hygienist",
        "Veterinarian",
        "Respiratory Therapist",
        "Dental Assistant",
    ],
    "Hospitality & Food Service": [
        "Hotel Manager",
        "Front Desk Agent",
        "Housekeeping Supervisor",
        "Restaurant Manager",
        "Chef",
        "Waiter",
        "Waitress",
        "Bartender",
        "Event Coordinator",
        "Concierge",
        "Guest Services Manager",
    ],
}

# Profile Categories with their associated role titles
PROFILE_CATEGORIES: Dict[str, List[str]] = {
    "Engineering": [
        "Mechanical Engineer",
        "Electrical Engineer",
        "Civil Engineer",
        "Chemical Engineer",
        "Industrial Engineer",
        "Aerospace Engineer",
        "Project Engineer",
        "Design Engineer",
        "Manufacturing Engineer",
        "Maintenance Engineer",
        "Construction Manager",
    ],
    "Operations & Logistics": [
        "Operations Manager",
        "Logistics Coordinator",
        "Supply Chain Manager",
        "Warehouse Manager",
        "Inventory Manager",
        "Production Planner",
        "Operations Analyst",
        "Transportation Manager",
        "Distribution Manager",
        "Fleet Manager",
        "Market Research Analyst",
    ],
    "Business Strategy & Analysis": [
        "Business Analyst",
        "Strategy Manager",
        "Business Operations Manager",
        "Business Development Manager",
        "Business Consultant",
        "Corporate Strategist",
        "Business Process Analyst",
        "Operations Analyst",
        "Growth Manager",
        "Strategic Planning Manager",
        "Management Analyst",
    ],
    "Customer Service & Support": [
        "Customer Service Representative",
        "Technical Support Specialist",
        "Client Success Manager",
        "Customer Support Agent",
        "Help Desk Technician",
        "Call Center Representative",
        "Customer Experience Manager",
        "Support Engineer",
        "Customer Care Specialist",
        "Customer Service Manager",
    ],
    "Business Development": [
        "Business Development Manager",
        "Business Development Representative",
        "Partnership Manager",
        "Sales Development Representative",
        "Growth Manager",
        "Business Development Executive",
        "Account Executive",
        "Corporate Development Manager",
        "Market Development Manager",
        "Strategic Partnerships Manager",
    ],
    "Quality Assurance": [
        "Quality Assurance Engineer",
        "QA Tester",
        "Quality Control Inspector",
        "Test Engineer",
        "Quality Analyst",
        "Software Tester",
        "QA Manager",
        "Quality Technician",
        "Validation Engineer",
        "QA Specialist",
    ],
    "Research & Development": [
        "Research Scientist",
        "Research Assistant",
        "Lab Technician",
        "Clinical Research Coordinator",
        "Research Analyst",
        "Data Scientist",
        "Research Associate",
        "Laboratory Manager",
        "Biochemist",
        "Research Engineer",
    ],
    "Human Resources & Security": [
        "HR Manager",
        "Recruiter",
        "Talent Acquisition Specialist",
        "HR Generalist",
        "HR Coordinator",
        "Benefits Administrator",
        "HR Assistant",
        "Compensation Analyst",
        "Training and Development Manager",
        "Employee Relations Specialist",
        "Security Guard",
        "Cybersecurity Specialist",
    ],
    "Technology & IT": [
        "Software Developer",
        "Software Engineer",
        "Full Stack Engineer",
        "Frontend Engineer",
        "Backend Engineer",
        "Data Engineer",
        "AI Engineer",
        "Machine Learning Engineer",
        "Data Scientist",
        "IT Manager",
        "Systems Administrator",
        "Network Engineer",
        "Database Administrator",
        "IT Support Specialist",
        "Web Developer",
        "Cybersecurity Analyst",
        "Data Analyst",
        "DevOps Engineer",
        "Computer Systems Analyst",
        "Computer Programmer",
        "Computer Systems Administrator",
        "Engineer Manager",
    ],
    "Accounting & Finance": [
        "Accountant",
        "Financial Analyst",
        "Payroll Specialist",
        "Accounts Payable Clerk",
        "Accounts Receivable Clerk",
        "Controller",
        "Tax Accountant",
        "Financial Planner",
        "Budget Analyst",
        "Bookkeeper",
        "Financial Manager",
    ],
    "Banking & Investment": [
        "Investment Banker",
        "Financial Advisor",
        "Portfolio Manager",
        "Credit Analyst",
        "Trader",
        "Risk Analyst",
        "Equity Analyst",
        "Loan Officer",
        "Bank Teller",
        "Financial Controller",
    ],
    "Project Management": [
        "Project Manager",
        "Program Manager",
        "Project Coordinator",
        "Project Scheduler",
        "Scrum Master",
        "Agile Coach",
        "PMO Manager",
        "Product Manager",
        "Technical Project Manager",
        "Implementation Manager",
    ],
    "Compliance & Risk": [
        "Compliance Officer",
        "Risk Manager",
        "Internal Auditor",
        "Compliance Analyst",
        "Risk Analyst",
        "Regulatory Affairs Specialist",
        "Fraud Investigator",
        "AML Analyst",
        "Governance Manager",
        "Compliance Manager",
    ],
    "Sales": [
        "Sales Representative",
        "Account Manager",
        "Sales Associate",
        "Business Development Representative",
        "Sales Manager",
        "Territory Manager",
        "Inside Sales Representative",
        "Outside Sales Representative",
        "Retail Sales Associate",
        "Sales Engineer",
    ],
    "Marketing": [
        "Marketing Manager",
        "Digital Marketing Specialist",
        "Content Marketing Manager",
        "SEO Specialist",
        "Social Media Manager",
        "Marketing Coordinator",
        "Brand Manager",
        "Marketing Analyst",
        "Product Marketing Manager",
        "Marketing Director",
    ],
    "Consulting": [
        "Consultant",
        "Management Consultant",
        "Strategy Consultant",
        "IT Consultant",
        "Business Consultant",
        "Financial Consultant",
        "HR Consultant",
        "Environmental Consultant",
        "Sales Consultant",
        "Marketing Consultant",
    ],
    "Procurement & Purchasing": [
        "Purchasing Manager",
        "Procurement Specialist",
        "Buyer",
        "Supply Chain Analyst",
        "Commodity Manager",
        "Purchasing Agent",
        "Sourcing Specialist",
        "Procurement Manager",
        "Vendor Manager",
        "Supply Chain Coordinator",
    ],
    "IT Support": [
        "IT Support Specialist",
        "Help Desk Technician",
        "Technical Support Engineer",
        "Desktop Support Technician",
        "Systems Support Specialist",
        "IT Technician",
        "Support Analyst",
        "Network Support Technician",
        "Field Service Technician",
        "Technical Support Specialist",
    ],
    "Design & Creative": [
        "Graphic Designer",
        "UX/UI Designer",
        "Art Director",
        "Illustrator",
        "Creative Director",
        "Interior Designer",
        "Multimedia Artist",
        "Animator",
        "Web Designer",
        "Photographer",
    ],
    "Legal": [
        "Lawyer",
        "Paralegal",
        "Legal Assistant",
        "Legal Secretary",
        "Corporate Counsel",
        "Legal Analyst",
        "Contract Manager",
        "Litigation Attorney",
        "Intellectual Property Lawyer",
        "Legal Counsel",
    ],
}

# Employment Types
EMPLOYMENT_TYPES: List[str] = [
    "Full-Time",
    "Part-Time",
    "Contract",
    "Internship",
]

# Work Arrangements
WORK_ARRANGEMENTS: List[str] = [
    "Remote",
    "On-Site",
    "Hybrid",
]


# Helper functions
def get_all_profile_categories() -> List[str]:
    """Get list of all profile category names"""
    return list(PROFILE_CATEGORIES.keys())


def get_role_titles_by_category(category: str) -> List[str]:
    """Get all role titles for a specific profile category"""
    return PROFILE_CATEGORIES.get(category, [])


def find_category_by_role_title(role_title: str) -> str | None:
    """Find the profile category for a given role title"""
    for category, roles in PROFILE_CATEGORIES.items():
        if role_title in roles:
            return category
    return None


def get_all_role_titles() -> List[str]:
    """Get a flat list of all unique role titles across all categories"""
    all_roles = []
    for roles in PROFILE_CATEGORIES.values():
        all_roles.extend(roles)
    return sorted(list(set(all_roles)))


def is_valid_employment_type(employment_type: str) -> bool:
    """Check if employment type is valid"""
    return employment_type in EMPLOYMENT_TYPES


def is_valid_work_arrangement(work_arrangement: str) -> bool:
    """Check if work arrangement is valid"""
    return work_arrangement in WORK_ARRANGEMENTS


def get_category_stats() -> Dict[str, int]:
    """Get statistics about categories"""
    return {
        "total_categories": len(PROFILE_CATEGORIES),
        "total_role_titles": sum(len(roles) for roles in PROFILE_CATEGORIES.values()),
        "employment_types": len(EMPLOYMENT_TYPES),
        "work_arrangements": len(WORK_ARRANGEMENTS),
    }


# Export all for easy imports
__all__ = [
    "PROFILE_CATEGORIES",
    "EMPLOYMENT_TYPES",
    "WORK_ARRANGEMENTS",
    "get_all_profile_categories",
    "get_role_titles_by_category",
    "find_category_by_role_title",
    "get_all_role_titles",
    "is_valid_employment_type",
    "is_valid_work_arrangement",
    "get_category_stats",
]
