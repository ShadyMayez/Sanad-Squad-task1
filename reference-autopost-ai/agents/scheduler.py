from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from models.schemas import FinalPost,ScheduledPost
from config import GROQ_API, GROQ_MODEL_SMALL ,POSTING_SCHEDULE
from typing import List
from utils import groq_retry
class SchedulerAgent():
    def __init__(self):
        self.llm=ChatGroq(api_key=GROQ_API,model=GROQ_MODEL_SMALL)
        self.parser=JsonOutputParser()
        self.prompt=ChatPromptTemplate.from_template("""You are a Scheduler Agent. You ONLY return JSON. Never write code. Never explain anything.

                                                        Your job is to assign the exact day and time when each post should be published.

                                                        Your task:

                                                            For each post in the content schedule:

                                                                Choose the appropriate day.

                                                                Choose the best time to publish the post.

                                                        Rules:

                                                            Follow the posting schedule when selecting days and times.

                                                            Do not modify the post content.

                                                            Do not invent new posts.

                                                            Only schedule the posts that are provided.

                                                            Ensure the selected day and time exist in the posting schedule.

                                                        Posting Schedule: {posting_schedule}

                                                        Content Schedule: {content_schedule}

                                                        Return ONLY a JSON array like this:
                                                        [{{
                                                        "date": "..."
                                                    }}] """)

    def run(self,final_posts)->list[ScheduledPost]:
     formatted_final_posts="\n\n".join([f"platform : {p.platform}\ncopy : {p.copy}\nhashtags : {p.hashtags}\nimage_url : {p.image_url}\nimage_credit : {p.image_credit}" for p in final_posts])
     chain=self.prompt|self.llm|self.parser  
     invoke_with_retry = groq_retry(chain.invoke) 
     json_formatted_response=invoke_with_retry({"posting_schedule":POSTING_SCHEDULE,"content_schedule":formatted_final_posts})
     if isinstance(json_formatted_response,list):
        if len(json_formatted_response)>0 and isinstance(json_formatted_response[0],str):
            print("[Scheduler] LLM returned unexpected format")
            return []
        else:
            scheduled_posts = [
                                ScheduledPost(platform=p.platform, copy=p.copy, hashtags=p.hashtags,
                                            image_url=p.image_url, image_credit=p.image_credit,
                                            date=d["date"])
                                for p, d in zip(final_posts, json_formatted_response)]
        return scheduled_posts
     else:
        print("[SCHEDULAR] : the llm  did not returne a list")