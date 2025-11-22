import asyncio
import json
import os
from typing import Dict
from browser_use import Agent, Browser, ChatOpenAI, Tools
from browser_use.tools.views import UploadFileAction
from pydantic import BaseModel


class ApplyToJobPostingAutomationParams(BaseModel):
    """Request model for triggering job application automation"""

    headless: bool = False


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
    - Your goal is to fill out and submit a job application form with the provided information.
    - Navigate into {url} and locate the job application form you may need to click on a button to land on the form.
    - Scroll through the entire application and use extract_structured_data action to extract all the relevant information needed to fill out the job application form. use this information and return a structured output that can be used to fill out the entire form: {params.info}. Use the done action to finish the task. Fill out the job application form with the following information.
        - Before completing every step, refer to this information for accuracy. It is structured in a way to help you fill out the form and is the source of truth.
    - Follow these instructions carefully:
        - if anything pops up that blocks the form, close it out and continue filling out the form.
        - Do not skip any fields, even if they are optional. If you do not have the information, make your best guess based on the information provided.
        Fill out the form from top to bottom, never skip a field unless you are missing the information or file, then skip and continue but never submit incomplete forms. When filling out a field, only focus on one field per step. For each of these steps, scroll to the related text. These are the steps:
            1) Match the fields as best as you can with the provided candidate information
            2) Do not submit the form until every field is filled out, for now we are testing so do not submit the form.
    - Before you start, create a step-by-step plan to complete the entire task. make sure the delegate a step for each field to be filled out.
    *** IMPORTANT ***:
        - You are not done until you have filled out every field of the form.
        - When you have completed the entire form, DO NOT press the submit button to submit the application.
        - At the end of the task, structure your final_result as 1) a human-readable summary of all detections and actions performed on the page with 2) a list with all questions encountered in the page. Do not say "see above." Include a fully written out, human-readable summary at the very end.
    
    """

    browser = Browser(
        cross_origin_iframes=True,
        headless=automation_params.headless,
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
