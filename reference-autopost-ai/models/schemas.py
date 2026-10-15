from pydantic import BaseModel
from typing import List, Optional

class TrendTopic(BaseModel):
    topic_name : str
    relevance_score : float
    source : str

class ContentSlot(BaseModel):
    platform : str
    day : str
    topic : str
    angle : str
    content_type : str

class DraftPost(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    platform : str
    copy : str
    hashtags : List[str]
    image_query : str

class FinalPost(BaseModel):
    model_config = {"arbitrary_types_allowed": True}
    platform : str
    copy : str
    hashtags : List[str]
    image_url : Optional[str]
    image_credit : Optional[str]

class ScheduledPost(FinalPost):
    date : str

class WeeklyReport(BaseModel):
    week_of : str
    total_posts : int
    platforms_covered : List[str]
    scheduled_posts : List[ScheduledPost]