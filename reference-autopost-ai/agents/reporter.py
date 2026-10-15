from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from models.schemas import WeeklyReport,ScheduledPost
from config import GROQ_API, GROQ_MODEL_SMALL 
from typing import List
from utils import groq_retry

class ReporterAgent():
    def __init__(self):
        self.llm=ChatGroq(api_key=GROQ_API,model=GROQ_MODEL_SMALL )
        self.parser=JsonOutputParser()
        self.prompt=ChatPromptTemplate.from_template("""You are a Reporter Agent.

                                                        Your job is to analyze the scheduled posts and generate a weekly posting report.

                                                        Your task:

                                                            From the scheduled posts:

                                                                Identify the week the posts belong to.

                                                                Count the total number of posts.

                                                                Identify which platforms are covered.

                                                                List all the scheduled posts.

                                                        Rules:

                                                            Only use the information provided in the scheduled posts.

                                                            Do not invent posts.

                                                            Do not modify the posts.

                                                            Extract the platforms directly from the scheduled posts.

                                                            The week should be clearly identified (example: "Week 1 of January", "Week 4 of February").

                                                        Scheduled Posts: {scheduled_posts}

                                                        You ONLY return valid JSON. No notes. No explanations. No text before or after the JSON.

                                                        Return ONLY this exact format:
                                                        {{
                                                        "week_of": "...",
                                                        "total_posts": 0,
                                                        "platforms_covered": ["..."],
                                                        "scheduled_posts": [
                                                            {{"platform": "...", "day": "...", "time": "...", "topic": "..."}}
                                                        ]
                                                        }} """)
    def run(self,scheduled_posts)-> WeeklyReport:
        formatted_scheduled_posts="\n\n".join([f"platform : {p.platform}\ncopy : {p.copy}\nhashtags : {p.hashtags}\nimage_url : {p.image_url}\nimage_credit : {p.image_credit}\ndate : {p.date}" for p in scheduled_posts])
        chain=self.prompt|self.llm|self.parser  
        invoke_with_retry = groq_retry(chain.invoke)
        json_formatted_response=invoke_with_retry({"scheduled_posts":formatted_scheduled_posts})
        weekly_report=WeeklyReport(week_of=json_formatted_response["week_of"],
                                   total_posts=json_formatted_response["total_posts"],
                                   platforms_covered=json_formatted_response["platforms_covered"],
                                   scheduled_posts=scheduled_posts)
        fromatted_weekly_report=f"week of : {weekly_report.week_of}\ntotal posts : {weekly_report.total_posts}\nplatforms covered  : {weekly_report.platforms_covered}\nscheduled posts  : {weekly_report.scheduled_posts}"
        prompt_2="""You are an AI assistant responsible for converting a **weekly social media trend report** into an **email subject and HTML body**.

                    INPUT
                    You will receive a weekly report produced by internal analysis agents. The report may contain:

                    * trending topics
                    * engagement metrics
                    * content themes covered
                    * insights from external sources
                    * performance observations
                    * recommendations

                    TASK
                    Analyze the report and generate:

                    1. **Email Subject**

                    * Short and professional
                    * Reflects the main insight or dominant trend of the week

                    2. **Email Body**

                    * Written in **clean HTML**
                    * Analytical and concise
                    * Structured as a weekly report

                    EMAIL BODY STRUCTURE

                    The HTML body should include:

                    <h1>Weekly Social Media Trend Report</h1>

                    <h2>Executive Summary</h2>
                    - 3–5 sentences summarizing the most important insights.

                    <h2>What Performed Well</h2>
                    - Bullet list of strong-performing trends, topics, or formats.

                    <h2>Topics Covered</h2>
                    - Bullet list of the key topics analyzed during the week.

                    <h2>Key Insights</h2>
                    - Brief explanation of why certain topics performed well.

                    <h2>Recommendations for Next Week</h2>
                    - Actionable suggestions for content strategy.

                    FORMAT RULES

                    * Output **ONLY valid JSON**
                    * Do not include explanations
                    * Do not include markdown
                    * Do not wrap the JSON in code blocks
                    * The HTML must be inside the `"body"` field
                    * Use only simple HTML tags: `<html> <body> <h1> <h2> <p> <ul> <li>`

                    OUTPUT FORMAT

                    {{
                    "subject": "string",
                    "body": "<html><body>...</body></html>"
                    }}

                    INPUT REPORT:
                    {weekly_report}
                    """
        prompt_2_template=ChatPromptTemplate.from_template(prompt_2)
        chain_2=prompt_2_template|self.llm|self.parser   
        json_formatted_response_2=chain_2.invoke({"weekly_report":fromatted_weekly_report})
        subject=json_formatted_response_2["subject"]
        body=json_formatted_response_2["body"]
        return weekly_report,subject,body