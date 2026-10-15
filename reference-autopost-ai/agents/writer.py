from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from models.schemas import ContentSlot,DraftPost
from config import GROQ_API, GROQ_MODEL,BRAND
from typing import List
from utils import groq_retry

class WriterAgent():
    def __init__(self):
        self.llm=ChatGroq(api_key=GROQ_API, model= GROQ_MODEL)
        self.parser=JsonOutputParser()
        self.prompt=ChatPromptTemplate.from_template("""You are a Content Writer Agent.

                                                            Your job is to create high-quality social media content AND a **precise image search query** that ensures the **first result from Unsplash is highly relevant**.

                                                            INPUTS

                                                            * Brand Dictionary: {brand_dictionary}
                                                            * Content Plan: {content_plan}

                                                            TASK

                                                            For each item in the content plan:

                                                            1. Write the post copy
                                                            2. If the content is a video, write a short video script
                                                            3. Generate relevant hashtags
                                                            4. Generate a **highly specific image_query optimized for Unsplash search**

                                                            ---

                                                            CRITICAL: IMAGE QUERY RULES (MOST IMPORTANT PART)

                                                            The image_query must be written as if you are trying to get the **perfect image on the first search result**.

                                                            You MUST:

                                                            * Use **5–12 highly descriptive keywords**

                                                            * Include:

                                                            * **Main subject** (who/what)
                                                            * **Action** (what is happening)
                                                            * **Context/environment** (where)
                                                            * **Style or mood** (e.g. modern, minimal, professional, cinematic)
                                                            * **Visual details** (lighting, angle, composition, colors if relevant)

                                                            * Be **concrete and visual**, NOT abstract

                                                            ---

                                                            BAD image_query examples (FORBIDDEN):

                                                            * "marketing"
                                                            * "business growth"
                                                            * "AI automation"
                                                            * "success mindset"

                                                            GOOD image_query examples:

                                                            * "young entrepreneur working on laptop in modern office startup environment natural light"
                                                            * "robotic hand typing on keyboard close up futuristic automation concept dark background"
                                                            * "person analyzing social media analytics dashboard on laptop clean workspace top view"
                                                            * "content creator filming video with smartphone tripod indoor studio lighting"

                                                            ---

                                                            ADDITIONAL RULES

                                                            * Prefer **real-world scenes** over abstract concepts
                                                            * Avoid vague or metaphorical terms
                                                            * Avoid single-word or short queries
                                                            * Avoid repeating the exact post text
                                                            * Think: “What would a photographer type to find this image?”

                                                            ---

                                                            WRITING RULES

                                                            * Follow the brand voice and style
                                                            * Adapt to the platform
                                                            * Keep content clear, engaging, and concise
                                                            * Do not change the content plan
                                                            * Do not invent new topics

                                                            ---

                                                            OUTPUT FORMAT

                                                            Return ONLY a JSON array:


                                                            IMPORTANT: Return ONLY a single JSON object, NOT an array. No square brackets.
                                                            {{
                                                            "platform": "...",
                                                            "copy": "...",
                                                            "hashtags": ["...", "..."],
                                                            "image_query": "..."
                                                            }}


                                                        """)
    def run(self,content_programs)->list[DraftPost]:
        chain=self.prompt|self.llm|self.parser
        draft_posts=[]
        for i,p in enumerate(content_programs):
            print(f"[WriterAgent] Processing post {i+1}/{len(content_programs)}...")
            formatted_program=f"platform : {p.platform}\nday : {p.day}\ntopic : {p.topic}\nangle : {p.angle}\ncontent_type : {p.content_type}"
            invoke_with_retry = groq_retry(chain.invoke)
            json_formatted_response=invoke_with_retry({"brand_dictionary":BRAND,"content_plan":formatted_program})
            if isinstance(json_formatted_response,list):
                json_formatted_response=json_formatted_response[0]
            draft_post=DraftPost(**json_formatted_response)
            draft_posts.append(draft_post)
        return draft_posts
