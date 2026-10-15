from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from models.schemas import ContentSlot,TrendTopic
from config import GROQ_API, GROQ_MODEL,BRAND,POSTING_SCHEDULE
from typing import List
from utils import groq_retry
 
class ContentPlannerAgent():
    def __init__(self):
        self.llm=ChatGroq(api_key=GROQ_API,model=GROQ_MODEL)
        self.parser=JsonOutputParser()
        self.prompt=ChatPromptTemplate.from_template("""You are a Content Planner Agent.

                                                        Your job is to analyze provided trending topics and create a content posting plan.

                                                        Your task:

                                                            For each topic:

                                                                Decide the best platform to publish it on.

                                                                Choose the best day to post it based on the posting schedule.

                                                                Define the angle (how the topic should be approached).

                                                                Choose the most appropriate content type.

                                                        Rules:

                                                            Do not invent new topics.

                                                            Only use the topics provided.

                                                            Follow the posting schedule when choosing platforms and days.

                                                            Ensure the topic and angle are relevant to the brand.

                                                            Choose a clear and specific angle.

                                                            Avoid vague angles like "general discussion".

                                                            Ensure the content type fits the platform.

                                                            Return one plan for each topic.

                                                        Brand Info: {brand_info}

                                                        Posting Schedule: {posting_schedule}

                                                        Topics: {topics}

                                                        Return ONLY a JSON array like this:
                                                        [
                                                        {{"platform": "...", "day": "...", "topic": "...", "angle": "...", "content_type": "..."}}
                                                        ]""")
    def run(self,topics)->list[ContentSlot]:
        chain=self.prompt|self.llm|self.parser
        fromatted_topics="\n\n".join([f"topic_name:{t.topic_name}\nrelevance_score:{t.relevance_score}\nsource:{t.source}" for t in topics])
        invoke_with_retry = groq_retry(chain.invoke)
        json_formatted_response=invoke_with_retry({"brand_info":BRAND,"posting_schedule":POSTING_SCHEDULE,"topics":fromatted_topics})
        planned_programs=[ContentSlot(**program) for program in json_formatted_response]
        return planned_programs
