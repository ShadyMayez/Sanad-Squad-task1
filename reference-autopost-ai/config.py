import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API=os.getenv("GROQ_API_KEY")
SERPER_API=os.getenv("SERPER_API_KEY")
UNSPLASH_API=os.getenv("UNSPLASH_ACCESS_KEY")
GMAIL_APP_PASSWORD=os.getenv("GMAIL_APP_PASSWORD")
GMAIL_SENDER=os.getenv("GMAIL_SENDER")
GMAIL_RECIPIENT=os.getenv("GMAIL_RECIPIENT")
GROQ_MODEL="Llama-3.3-70B-Versatile"
GROQ_MODEL_SMALL = "llama-3.1-8b-instant"

BRAND = {
    "name": "SM-AI Agent",
    "industry": "AI SaaS for social media automation",
    "tone": "confident, direct, clear, future-focused",
    "pillars": ["social media growth", "AI automation", "business leverage"],
    "avoid_topics": ["politics", "religion", "get rich quick"],
    "target_audience": "startup founders and small business owners who want to automate growth",
    "cta": "Book a free demo at sm-ai.com"
}

POSTING_SCHEDULE = {
    "linkedin": {
        "frequency": 4,
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday"],
        "best_times": ["08:30", "12:30"]
    },

    "twitter_x": {
        "frequency": 7,
        "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        "best_times": ["09:00", "17:00", "21:00"]
    },

    "instagram": {
        "frequency": 3,
        "days": ["Tuesday", "Thursday", "Saturday"],
        "best_times": ["18:30", "20:30"]
    }
}