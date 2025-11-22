"""
Playwright script to automatically fill job application form on Greenhouse.io
This script fills the application form for OMG UK job postings.
"""

import asyncio
import json
import os
from pathlib import Path
from playwright.async_api import async_playwright, Page, expect


async def fill_text_field(page: Page, selector: str, value: str, field_name: str = ""):
    """Helper function to fill text fields with error handling"""
    try:
        if value:
            await page.fill(selector, value)
            print(f"✓ Filled {field_name or selector}: {value}")
    except Exception as e:
        print(f"✗ Error filling {field_name or selector}: {e}")


async def select_dropdown(page: Page, selector: str, value: str, field_name: str = ""):
    """Helper function to select dropdown options with error handling"""
    try:
        if value:
            await page.select_option(selector, label=value)
            print(f"✓ Selected {field_name or selector}: {value}")
    except Exception as e:
        print(f"✗ Error selecting {field_name or selector}: {e}")


async def upload_file(page: Page, selector: str, file_path: str, field_name: str = ""):
    """Helper function to upload files with error handling"""
    try:
        if file_path and os.path.exists(file_path):
            await page.set_input_files(selector, file_path)
            print(f"✓ Uploaded {field_name or selector}: {file_path}")
        elif file_path:
            print(f"⚠ File not found: {file_path}")
    except Exception as e:
        print(f"✗ Error uploading {field_name or selector}: {e}")


async def fill_greenhouse_application(url: str, application_data_path: str, headless: bool = False):
    """
    Fill out a Greenhouse job application form automatically.
    
    Args:
        url: The job application URL
        application_data_path: Path to JSON file containing application data
        headless: Whether to run browser in headless mode
    """
    
    # Load application data
    with open(application_data_path, 'r') as f:
        data = json.load(f)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context()
        page = await context.new_page()
        
        print(f"\n🚀 Navigating to: {url}")
        await page.goto(url)
        
        # Wait for the form to load
        await page.wait_for_selector('input[id="first_name"]', timeout=10000)
        print("✓ Form loaded successfully\n")
        
        # ===== PERSONAL INFORMATION =====
        print("📝 Filling Personal Information...")
        personal = data.get('personal_info', {})
        
        await fill_text_field(page, 'input[id="first_name"]', personal.get('first_name', ''), "First Name")
        await fill_text_field(page, 'input[id="last_name"]', personal.get('last_name', ''), "Last Name")
        await fill_text_field(page, 'input[id="email"]', personal.get('email', ''), "Email")
        
        # Phone number - might need to select country code first
        country_code = personal.get('country_code', '')
        if country_code:
            try:
                # Try to find and click the country code dropdown
                await page.click('div[class*="country-select"]', timeout=5000)
                await page.click(f'text="{country_code}"', timeout=5000)
                print(f"✓ Selected country code: {country_code}")
            except Exception as e:
                print(f"⚠ Could not select country code: {e}")
        
        await fill_text_field(page, 'input[name="phone"]', personal.get('phone', ''), "Phone")
        
        # ===== DOCUMENTS =====
        print("\n📄 Uploading Documents...")
        documents = data.get('documents', {})
        
        # Resume upload
        resume_path = documents.get('resume_path', '')
        if resume_path:
            try:
                # Look for resume upload input
                resume_input = page.locator('input[name="resume"]').first
                await resume_input.set_input_files(resume_path)
                print(f"✓ Uploaded Resume: {resume_path}")
                await asyncio.sleep(1)  # Wait for upload to process
            except Exception as e:
                print(f"✗ Error uploading resume: {e}")
        
        # Cover letter upload
        cover_letter_path = documents.get('cover_letter_path', '')
        if cover_letter_path:
            try:
                cover_input = page.locator('input[name="cover_letter"]').first
                await cover_input.set_input_files(cover_letter_path)
                print(f"✓ Uploaded Cover Letter: {cover_letter_path}")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"✗ Error uploading cover letter: {e}")
        
        # Scroll down to see more fields
        await page.evaluate("window.scrollBy(0, 300)")
        await asyncio.sleep(0.5)
        
        # ===== PREFERRED NAMES =====
        print("\n👤 Filling Preferred Names...")
        await fill_text_field(
            page, 
            'input[name*="preferred"][name*="first" i]', 
            personal.get('preferred_first_name', ''), 
            "Preferred First Name"
        )
        await fill_text_field(
            page, 
            'input[name*="preferred"][name*="last" i]', 
            personal.get('preferred_last_name', ''), 
            "Preferred Last Name"
        )
        
        # ===== ADDRESS =====
        print("\n🏠 Filling Address Information...")
        address = data.get('address', {})
        
        await fill_text_field(
            page, 
            'input[name*="address" i][name*="line" i][name*="1" i]', 
            address.get('address_line_1', ''), 
            "Address Line 1"
        )
        await fill_text_field(
            page, 
            'input[name*="address" i][name*="line" i][name*="2" i]', 
            address.get('address_line_2', ''), 
            "Address Line 2"
        )
        await fill_text_field(
            page, 
            'input[name*="city" i]', 
            address.get('city', ''), 
            "City"
        )
        
        # Country dropdown
        country = address.get('country', '')
        if country:
            try:
                await page.select_option('select[name*="country" i]', label=country)
                print(f"✓ Selected Country: {country}")
            except Exception as e:
                print(f"✗ Error selecting country: {e}")
        
        await fill_text_field(
            page, 
            'input[name*="post" i][name*="code" i]', 
            address.get('post_code', ''), 
            "Post Code"
        )
        
        # Scroll down more
        await page.evaluate("window.scrollBy(0, 300)")
        await asyncio.sleep(0.5)
        
        # ===== APPLICATION DETAILS =====
        print("\n💼 Filling Application Details...")
        app_details = data.get('application_details', {})
        
        # Where did you hear about this role
        where_heard = app_details.get('where_did_you_hear', '')
        if where_heard:
            try:
                await page.select_option('select[name*="hear" i]', label=where_heard)
                print(f"✓ Selected Where Heard: {where_heard}")
            except Exception as e:
                print(f"✗ Error selecting where heard: {e}")
        
        # UK Right to Work Status
        right_to_work = app_details.get('uk_right_to_work_status', '')
        if right_to_work:
            try:
                await page.select_option('select[name*="right" i][name*="work" i]', label=right_to_work)
                print(f"✓ Selected Right to Work: {right_to_work}")
            except Exception as e:
                print(f"✗ Error selecting right to work: {e}")
        
        # Visa end date (if applicable)
        visa_date = app_details.get('visa_end_date', '')
        if visa_date:
            await fill_text_field(
                page, 
                'input[name*="visa" i][name*="date" i]', 
                visa_date, 
                "Visa End Date"
            )
        
        # Salary expectations
        await fill_text_field(
            page, 
            'input[name*="salary" i]', 
            app_details.get('annual_salary_expectations', ''), 
            "Salary Expectations"
        )
        
        # LinkedIn profile
        await fill_text_field(
            page, 
            'input[name*="linkedin" i]', 
            app_details.get('linkedin_profile', ''), 
            "LinkedIn Profile"
        )
        
        # Previously employed by Omnicom
        previously_employed = app_details.get('previously_employed_by_omnicom', '')
        if previously_employed:
            try:
                await page.select_option('select[name*="employed" i][name*="omnicom" i]', label=previously_employed)
                print(f"✓ Selected Previously Employed: {previously_employed}")
            except Exception as e:
                print(f"✗ Error selecting previously employed: {e}")
        
        # Scroll to demographic questions
        await page.evaluate("window.scrollBy(0, 400)")
        await asyncio.sleep(0.5)
        
        # ===== DEMOGRAPHIC QUESTIONS =====
        print("\n📊 Filling Demographic Questions...")
        demographic = data.get('demographic_questions', {})
        
        # Gender
        gender = demographic.get('gender', '')
        if gender:
            try:
                # Find the gender select dropdown - might need to be more specific
                gender_selects = await page.locator('select').all()
                for select in gender_selects:
                    # Check if this is the gender dropdown by looking at nearby text
                    try:
                        await select.select_option(label=gender, timeout=1000)
                        print(f"✓ Selected Gender: {gender}")
                        break
                    except:
                        continue
            except Exception as e:
                print(f"⚠ Could not select gender: {e}")
        
        # Trans
        trans = demographic.get('trans', '')
        if trans:
            try:
                # This will need to find the specific dropdown for trans question
                await asyncio.sleep(0.3)
                # Implementation depends on exact HTML structure
                print(f"⚠ Trans field needs manual selection: {trans}")
            except Exception as e:
                print(f"⚠ Could not select trans: {e}")
        
        # Ethnic group
        ethnic = demographic.get('ethnic_group', '')
        if ethnic:
            try:
                await asyncio.sleep(0.3)
                print(f"⚠ Ethnic group needs manual selection: {ethnic}")
            except Exception as e:
                print(f"⚠ Could not select ethnic group: {e}")
        
        # Sexual orientation
        orientation = demographic.get('sexual_orientation', '')
        if orientation:
            try:
                await asyncio.sleep(0.3)
                print(f"⚠ Sexual orientation needs manual selection: {orientation}")
            except Exception as e:
                print(f"⚠ Could not select sexual orientation: {e}")
        
        # Disabled
        disabled = demographic.get('disabled', '')
        if disabled:
            try:
                await asyncio.sleep(0.3)
                print(f"⚠ Disabled field needs manual selection: {disabled}")
            except Exception as e:
                print(f"⚠ Could not select disabled: {e}")
        
        # Household earner occupation
        occupation = demographic.get('main_household_earner_occupation', '')
        if occupation:
            try:
                await asyncio.sleep(0.3)
                print(f"⚠ Household occupation needs manual selection: {occupation}")
            except Exception as e:
                print(f"⚠ Could not select household occupation: {e}")
        
        # School type
        school = demographic.get('school_type', '')
        if school:
            try:
                await asyncio.sleep(0.3)
                print(f"⚠ School type needs manual selection: {school}")
            except Exception as e:
                print(f"⚠ Could not select school type: {e}")
        
        # Free school meals
        meals = demographic.get('free_school_meals_eligible', '')
        if meals:
            try:
                await asyncio.sleep(0.3)
                print(f"⚠ Free school meals needs manual selection: {meals}")
            except Exception as e:
                print(f"⚠ Could not select free school meals: {e}")
        
        print("\n✅ Form filling completed!")
        print("\n⚠️  Note: Some demographic dropdown fields may need manual verification")
        print("    as they don't have unique identifiers in the HTML.")
        print("\n🔍 Review the form before submitting.")
        print("⏸️  Browser will stay open for 30 seconds for you to review...")
        
        # Keep browser open for review
        await asyncio.sleep(30)
        
        # Uncomment the line below to auto-submit (NOT RECOMMENDED without review)
        # await page.click('button[type="submit"]')
        # print("📤 Application submitted!")
        
        await browser.close()
        print("\n✓ Browser closed.")


async def main():
    """Main function to run the application filler"""
    
    # Configuration
    JOB_URL = "https://job-boards.greenhouse.io/omguk/jobs/4885567007"
    
    # Get the current script directory
    script_dir = Path(__file__).parent
    data_file = script_dir / "application_data_schema.json"
    
    if not data_file.exists():
        print(f"❌ Error: Application data file not found at {data_file}")
        print("Please create the application_data_schema.json file with your information.")
        return
    
    print("=" * 70)
    print("🤖 GREENHOUSE JOB APPLICATION FORM FILLER")
    print("=" * 70)
    print(f"\nJob URL: {JOB_URL}")
    print(f"Data File: {data_file}")
    print("\nStarting in 3 seconds...")
    await asyncio.sleep(3)
    
    try:
        await fill_greenhouse_application(
            url=JOB_URL,
            application_data_path=str(data_file),
            headless=False  # Set to True to run without UI
        )
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
