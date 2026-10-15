# AutoPost AI 🤖
### Autonomous Social Media Operations Pipeline

An end-to-end multi-agent system that autonomously researches trending topics, plans content, writes platform-specific posts, sources images, schedules everything, and emails you a weekly report — with zero human involvement after setup.

Built with **LangChain**, **LangGraph**, and **Python**, powered by **Groq's free LLM API**.

---

## What It Does

You run one command. The system does the rest:

1. **Searches the internet** for trending topics in your industry (via Serper API)
2. **Plans a full week of content** across LinkedIn, Instagram, and Twitter/X
3. **Writes platform-specific copy** for every post — tone, length, and style adapted per platform
4. **Sources relevant images** from Unsplash for each post
5. **Schedules everything** with exact posting dates and times
6. **Emails a professional weekly report** with executive summary, insights, and recommendations

---

## Architecture

AutoPost AI uses a **LangGraph StateGraph** to orchestrate 6 specialized agents through a shared pipeline state.

```
START
  │
  ▼
load_history ──► trend_researcher ──► content_planner ──► writer
                                                              │
                                                              ▼
send_email ◄── reporter ◄── save_posts ◄── scheduler ◄── image_sourcer
  │
  ▼
END
```

### Agents

| Agent | Role | Input | Output |
|---|---|---|---|
| Trend Researcher | Searches Google for trending topics in your industry | Posts history | List of TrendTopic objects |
| Content Planner | Assigns topics to platforms, days, and angles | TrendTopics | List of ContentSlot objects |
| Writer | Writes platform-optimized copy and hashtags | ContentSlots | List of DraftPost objects |
| Image Sourcer | Fetches relevant images from Unsplash | DraftPosts | List of FinalPost objects |
| Scheduler | Assigns exact posting dates and times | FinalPosts | List of ScheduledPost objects |
| Reporter | Generates weekly report and email | ScheduledPosts | WeeklyReport + email |

### Tools

| Tool | Purpose | API |
|---|---|---|
| `serper_tool.py` | Web search for trending topics | Serper.dev (free) |
| `unsplash_tool.py` | Image fetching | Unsplash (free) |
| `gmail_tool.py` | Weekly report delivery | Gmail SMTP (free) |

### Inter-Agent Communication

All agents communicate through typed **Pydantic schemas** defined in `models/schemas.py`. This ensures structured, validated data flows between every step of the pipeline — preventing silent failures from malformed data.

---

## Project Structure

```
autopost_ai/
├── main.py                    # LangGraph orchestrator
├── config.py                  # Brand config, API keys, posting schedule
├── utils.py                   # Retry logic (tenacity)
├── agents/
│   ├── trend_researcher.py
│   ├── content_planner.py
│   ├── writer.py
│   ├── image_sourcer.py
│   ├── scheduler.py
│   └── reporter.py
├── tools/
│   ├── serper_tool.py
│   ├── unsplash_tool.py
│   └── gmail_tool.py
├── models/
│   └── schemas.py             # Pydantic data models
├── memory/
│   └── content_store.py       # JSON-based post history
├── requirements.txt
└── .env                       # API keys (not committed)
```

---

## Setup

### Prerequisites

- Python 3.9+
- A Gmail account with 2FA enabled
- Free API accounts for: Groq, Serper, Unsplash

### 1. Clone the repository

```bash
git clone https://github.com/your-username/autopost-ai.git
cd autopost-ai
```

### 2. Create a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Mac/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up API keys

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
SERPER_API_KEY=your_serper_api_key
UNSPLASH_ACCESS_KEY=your_unsplash_access_key
GMAIL_SENDER=your_gmail@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
GMAIL_RECIPIENT=recipient@gmail.com
```

**Getting your API keys:**
- **Groq** (free): console.groq.com → Create API Key
- **Serper** (free, 100 searches/month): serper.dev → Get API Key
- **Unsplash** (free, 50 req/hour): unsplash.com/developers → New Application
- **Gmail App Password**: Google Account → Security → 2FA → App Passwords

### 5. Configure your brand

Edit `config.py` to set your brand name, industry, tone, content pillars, target audience, and posting schedule.

```python
BRAND = {
    "name": "Your Brand Name",
    "industry": "Your industry description",
    "tone": "your brand tone",
    "pillars": ["pillar 1", "pillar 2", "pillar 3"],
    "avoid_topics": ["topic 1", "topic 2"],
    "target_audience": "description of your audience",
    "cta": "Your call to action"
}
```

---

## Running the Agent

```bash
python main.py
```

Type `start` when prompted. The full pipeline takes approximately 3-5 minutes to complete.

---

## Sample Output

**Weekly Report Email:**

```
Weekly Social Media Trend Report

Executive Summary
This week, 5 posts were scheduled across LinkedIn, Instagram, and Twitter/X,
focusing on AI-driven social media automation and business productivity...

What Performed Well
- AI automation content
- Founder-focused productivity tips

Recommendations for Next Week
- Explore case study content format
- Increase LinkedIn posting frequency
```

**Scheduled Posts Example (LinkedIn):**

> "Most founders waste 10 hours a week on social media — not because they're 
> lazy, but because they're doing it manually. Here's how AI automation changes 
> that completely. [Thread]"
> 
> #AIAutomation #SocialMediaStrategy #FounderTips

---

## Key Design Decisions

**Why LangGraph?** The pipeline requires stateful, sequential agent execution where each agent's output becomes the next agent's input. LangGraph's StateGraph makes this explicit, debuggable, and extensible.

**Why Pydantic schemas?** Typed inter-agent communication prevents silent data failures. If an agent produces malformed output, Pydantic catches it immediately with a clear error.

**Why Groq?** Free tier with fast inference (Llama 3.3 70B). Capable enough for content generation without any API costs.

**Why separate tools from agents?** Tools handle external API communication. Agents handle reasoning and decision-making. Keeping them separate makes each component independently testable.

---

## Error Handling

The pipeline uses `tenacity` for automatic retry with exponential backoff on:
- Groq API rate limit errors (429)
- Network request failures

Failed image fetches are handled gracefully — posts continue without images rather than crashing the pipeline.

---

## Limitations

- Does not publish posts directly (scheduling output saved to `memory/content_store.json`)
- Image selection based on text descriptions only (Groq cannot see images)
- Subject to Groq's 100k daily token limit on free tier

---

## Tech Stack

- **LangChain** — LLM chains, prompt templates, output parsers
- **LangGraph** — Multi-agent orchestration via StateGraph
- **Groq API** — LLM inference (Llama 3.3 70B Versatile)
- **Pydantic** — Data validation and inter-agent schemas
- **Tenacity** — Retry logic with exponential backoff
- **Serper API** — Google Search results
- **Unsplash API** — Stock image fetching
- **Gmail SMTP** — Report delivery
