import asyncio
import json
import os
from typing import Dict
from browser_use import Agent, Browser, ChatOpenAI, Tools
from browser_use.tools.views import UploadFileAction
from pydantic import BaseModel

SPEED_OPTIMIZATION_PROMPT = """
Speed optimization instructions:
- Be extremely concise and direct in your responses
- Get to the goal as quickly as possible
- Use multi-action sequences whenever possible to reduce steps
"""


class ApplyToJobPostingAutomationParams(BaseModel):
    """Request model for triggering job application automation"""

    headless: bool = False
    flash_mode: bool = False  # Disabled for more reliable form filling
    extend_system_message: str = SPEED_OPTIMIZATION_PROMPT


class ApplyToJobPostingParams(BaseModel):
    """Parameters for applying to a job posting"""

    info: Dict
    resume_file_path: str
    url_to_apply: str = (
        "https://careers.deliveroo.co.uk/role/head-of-smb-deliveroo-for-work-632de4408c2e/"
    )


async def apply_to_job_posting(
    params: ApplyToJobPostingParams,
    automation_params: ApplyToJobPostingAutomationParams,
):

    # url = "https://job-boards.greenhouse.io/omguk/jobs/4885567007"
    url = params.url_to_apply
    task = f"""
Fill job application at {url} with data from {params.info}. DO NOT SUBMIT.

== STRATEGY ==
TWO-PASS APPROACH:
1. Navigate to {url}, click to reach form if needed
2. If iframe detected (grnhse_iframe, lever-frame, application-frame) → IMMEDIATELY switch into it
3. PASS 1: Scroll through form, fill ALL text fields (name, email, phone, address, essays). Batch multiple per step.
4. PASS 2: Scroll through form again, fill ALL complex fields (dropdowns, radios, checkboxes, file uploads). One per step.
5. Close popups/modals if they block form
6. Max 2 attempts per field, then mark incomplete and move on

== IFRAME HANDLING ==
When you see <iframe>: IMMEDIATELY switch context (don't waste steps observing)
Common IDs: grnhse_iframe, greenhouse_iframe, lever-frame, application-frame

== DROPDOWN HANDLING ==
🚨 DROPDOWNS REQUIRE 2 SEPARATE STEPS - NEVER TRY TO DO BOTH IN ONE STEP

STEP 1 - OPEN DROPDOWN:
- Use click action on dropdown element (<select>, role="combobox", or element with ▼)
- End step after clicking
- Wait for page to update

STEP 2 - SELECT OPTION:
- Use get_clickable_elements to see NEW div/menu with options that appeared
- Options are NEW elements: <li>, <div role="option">, or <option> with DIFFERENT indices
- Look for new container divs (often with classes like "select_menu", "dropdown-menu", "options-list")
- Click specific option element from this NEW list
- Verify selection shows in dropdown

Example:
STEP 1: Click Element 42 ("Select Gender" dropdown)
STEP 2: After get_clickable_elements, NEW elements appear:
  Element 55 = "she/her" ← click this
  Element 56 = "him/he"  
  Element 57 = "other"

For searchable dropdowns (100+ options):
STEP 1: Click dropdown to open
STEP 2: Type in search field to filter, then click filtered option

⛔ NEVER combine opening and selecting in one step
⛔ NEVER type directly into closed dropdown
⛔ ALWAYS use get_clickable_elements between opening and selecting
⛔ ALWAYS wait for new div/menu with options to appear on screen

If dropdown won't open after 2 attempts: mark incomplete, move on

== OTHER FIELDS ==
- TEXT (<input>, <textarea>): Type directly using input_text action
- RADIO: Use click action on button
- CHECKBOX: Use click action to toggle
- FILE UPLOAD: Use available_file_paths for resume

== ERROR HANDLING ==
- "Element index not available": Use get_clickable_elements to refresh page state
- Field fails after 2 attempts: Document as incomplete, continue to next field
- NEVER scroll while dropdown is open

== OUTPUT ==
Final summary must include:
1. All actions performed
2. All fields attempted (success status)
3. Fields that failed after 2 attempts
4. Complete written summary
    """

    browser = Browser(
        headless=automation_params.headless,
        wait_between_actions=1,  # Longer wait time for dropdowns to fully expand and stabilize
        disable_security=True,  # Help with some sites that have strict security
    )
    tools = Tools()

    @tools.action(description="Upload resume file")
    async def upload_resume(browser_session):
        params = UploadFileAction(path=params.resume_file_path, index=0)
        return "Ready to upload resume"

    llm = ChatOpenAI(model="gpt-4.1-mini")
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        tools=tools,
        calculate_cost=True,
        generate_gif=True,
        available_file_paths=[params.resume_file_path],
        flash_mode=automation_params.flash_mode,
        extend_system_message=automation_params.extend_system_message,
        max_failures=2,
        retry_delay=2.0,
    )

    history = await agent.run()
    usage = history.usage()
    print(
        f"Total Tokens Used: {usage.total_tokens}, Total Cost: ${usage.total_cost:.4f}"
    )
    return history.final_result()


async def main(
    test_data_path: str = "./integrations/bots/application_data_schema.json",
):
    # Verify files exist
    if not os.path.exists(test_data_path):
        raise FileNotFoundError(f"Test data file not found at: {test_data_path}")

    with open(test_data_path) as f:  # noqa: ASYNC230
        mock_info = json.load(f)

    automation_params = ApplyToJobPostingAutomationParams(
        headless=False,
    )

    params = ApplyToJobPostingParams(
        info=mock_info,
        resume_file_path="./integrations/bots/sample_resume.pdf",
    )

    result = await apply_to_job_posting(params, automation_params)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
