"""
Test script to demonstrate job listing categories usage
"""

from domains.job_listings.categories import (
    PROFILE_CATEGORIES,
    EMPLOYMENT_TYPES,
    WORK_ARRANGEMENTS,
    get_all_profile_categories,
    get_role_titles_by_category,
    find_category_by_role_title,
    get_all_role_titles,
    is_valid_employment_type,
    is_valid_work_arrangement,
    get_category_stats,
)


def test_categories():
    """Test category functionality"""
    print("=" * 80)
    print("JOB LISTING CATEGORIES TEST")
    print("=" * 80)

    # 1. Display statistics
    print("\n📊 CATEGORY STATISTICS:")
    stats = get_category_stats()
    for key, value in stats.items():
        print(f"  • {key.replace('_', ' ').title()}: {value}")

    # 2. Display all profile categories
    print(f"\n📁 PROFILE CATEGORIES ({len(PROFILE_CATEGORIES)}):")
    for i, category in enumerate(get_all_profile_categories(), 1):
        role_count = len(get_role_titles_by_category(category))
        print(f"  {i:2d}. {category:<35} ({role_count} roles)")

    # 3. Display employment types
    print(f"\n💼 EMPLOYMENT TYPES ({len(EMPLOYMENT_TYPES)}):")
    for i, emp_type in enumerate(EMPLOYMENT_TYPES, 1):
        print(f"  {i}. {emp_type}")

    # 4. Display work arrangements
    print(f"\n🏢 WORK ARRANGEMENTS ({len(WORK_ARRANGEMENTS)}):")
    for i, arrangement in enumerate(WORK_ARRANGEMENTS, 1):
        print(f"  {i}. {arrangement}")

    # 5. Test role title lookup
    print("\n🔍 ROLE TITLE LOOKUP EXAMPLES:")
    test_roles = [
        "Software Engineer",
        "Data Scientist",
        "Marketing Manager",
        "Registered Nurse",
        "Project Manager",
    ]
    for role in test_roles:
        category = find_category_by_role_title(role)
        print(f"  • '{role}' → Category: {category}")

    # 6. Display sample category with all roles
    print("\n📋 SAMPLE CATEGORY - Technology & IT:")
    tech_roles = get_role_titles_by_category("Technology & IT")
    for i, role in enumerate(tech_roles, 1):
        print(f"  {i:2d}. {role}")

    # 7. Test validation functions
    print("\n✅ VALIDATION TESTS:")
    print(
        f"  • Is 'Full-Time' valid employment type? {is_valid_employment_type('Full-Time')}"
    )
    print(
        f"  • Is 'Temporary' valid employment type? {is_valid_employment_type('Temporary')}"
    )
    print(
        f"  • Is 'Remote' valid work arrangement? {is_valid_work_arrangement('Remote')}"
    )
    print(
        f"  • Is 'In-Office' valid work arrangement? {is_valid_work_arrangement('In-Office')}"
    )

    print("\n" + "=" * 80)
    print("✨ All tests completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    test_categories()
