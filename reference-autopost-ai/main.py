from agents.content_planner import ContentPlannerAgent
from agents.image_sourcer import ImageSourcerAgent
from agents.reporter import ReporterAgent
from agents.scheduler import SchedulerAgent
from agents.trend_researcher import TrendResearcherAgent
from agents.writer import WriterAgent
from memory.content_store import load_posts,save_posts
from tools.gmail_tool import send_report_email
from langgraph.graph import StateGraph,START,END
from typing import TypedDict,Optional
from models.schemas import TrendTopic, ContentSlot, DraftPost, FinalPost, ScheduledPost, WeeklyReport


class AgentState(TypedDict):
    history : list[dict]
    trend_topics : list[TrendTopic]
    content_slots : list[ContentSlot]
    draft_posts : list[DraftPost]
    final_posts : list[FinalPost]
    scheduled_posts : list[ScheduledPost]
    weekly_report : WeeklyReport
    subject : str
    body : str

def load_history_node(state: AgentState):
    history=load_posts()
    return {"history": history}

def trend_researcher_node(state : AgentState):
    trend_reseacher=TrendResearcherAgent()
    trend_topics=trend_reseacher.run(state["history"])
    return {"trend_topics" : trend_topics}

def content_planner_node(state : AgentState):
    content_planner=ContentPlannerAgent()
    content_slots=content_planner.run(state["trend_topics"])
    return {"content_slots" : content_slots}

def writer_node(state : AgentState):
    writer=WriterAgent()
    draft_posts=writer.run(state["content_slots"])
    return {"draft_posts": draft_posts}

def image_sourcer_node(state : AgentState):
    image_sourcer=ImageSourcerAgent()
    final_posts=image_sourcer.run(state["draft_posts"])
    return {"final_posts": final_posts}

def schedular_node(state : AgentState):
    schedular=SchedulerAgent()
    scheduled_posts=schedular.run(state["final_posts"])
    return {"scheduled_posts": scheduled_posts}

def save_history_node(state: AgentState):
    save=save_posts(state["scheduled_posts"])
    return {}

def reporter_node(state : AgentState):
    repoter=ReporterAgent()
    weekly_report,subject,body=repoter.run(state["scheduled_posts"])
    return {"weekly_report" : weekly_report,
            "subject" : subject,
            "body" : body}

def send_email_node(state : AgentState):
    send=send_report_email(state["subject"],state["body"])
    print("---email sent succesfully---")
    return {}


graph=StateGraph(AgentState)
graph.add_node("load_history" , load_history_node)
graph.add_node("trend_researcher" , trend_researcher_node)
graph.add_node("content_planner" , content_planner_node)
graph.add_node("writer" , writer_node)
graph.add_node("image_sourcer" , image_sourcer_node)
graph.add_node("schedular" , schedular_node)
graph.add_node("save_history" , save_history_node)
graph.add_node("reporter" , reporter_node)
graph.add_node("send_email" , send_email_node)

graph.add_edge(START,"load_history")
graph.add_edge("load_history","trend_researcher")
graph.add_edge("trend_researcher","content_planner")
graph.add_edge("content_planner","writer")
graph.add_edge("writer","image_sourcer")
graph.add_edge("image_sourcer","schedular")
graph.add_edge("schedular","save_history")
graph.add_edge("save_history","reporter")
graph.add_edge("reporter","send_email")
graph.add_edge("send_email",END)

start=graph.compile()

while True:
    begin=input("Helloo, this is the social media manager agent, type 'start' to begin the project:\n-")
    if begin=="start":
          start.invoke({
                        "history": [],
                        "trend_topics": [],
                        "content_slots": [],
                        "draft_posts": [],
                        "final_posts": [],
                        "scheduled_posts": [],
                        "weekly_report": None,
                        "subject": "",
                        "body": ""})
    else :
        print("type 'start'!!!!")
