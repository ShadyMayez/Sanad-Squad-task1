from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from tools.serper_tool import search_trending_topics
from models.schemas import TrendTopic
from config import GROQ_API, GROQ_MODEL,BRAND
from utils import groq_retry
class TrendResearcherAgent():
    def __init__(self):
       self.llm=ChatGroq(api_key=GROQ_API,model=GROQ_MODEL)
       self.parser=JsonOutputParser()
       self.prompt = ChatPromptTemplate.from_template("""
            You are a Trend Research Agent.

            Your job is to analyze provided search results and extract trending topics.
            Your task:

                Identify topics that:

                    Are currently gaining attention

                    Are highly relevant to the brand's industry

                    Are valuable to the brand's audience

                    Are specific (not generic or broad)

                Rules:

                    Do not invent trends.

                    Avoid topics that were already covered in the posts history.

                    Only use information from the search results.

                    Ignore unrelated trending topics.

                    Avoid generic themes.

                    Only return strong, actionable topics.

                    If nothing relevant is found, return an empty list.
            Industry: {industry}
            Search Results: {search_results}
            posts_history: {posts_history}

            Return ONLY a JSON array like this:
            [
            {{"topic_name": "...", "relevance_score": 0.0, "source": "..."}}
            ]""")
    
    def run(self,posts_history:list)->list[TrendTopic]:

        query = f"search for trending topics about {BRAND['industry']} in the context of {BRAND['pillars']}"
        results=search_trending_topics(query)
        formatted="\n\n".join([f"trend_name:{r['title']}\ntrend_link:{r['link']}\ntrend_snippet:{r['snippet']}" for r in results])
        chain=self.prompt|self.llm|self.parser
        invoke_with_retry = groq_retry(chain.invoke)
        recent_posts_history=posts_history[-5:] if len(posts_history)>5 else posts_history
        json_formmatted_response=invoke_with_retry({"industry": BRAND["industry"], "search_results": formatted, "posts_history":recent_posts_history})
        topics=[TrendTopic(**topic) for topic in json_formmatted_response]
        return topics
