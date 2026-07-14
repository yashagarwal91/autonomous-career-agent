# Autonomous Career Intelligence Agent

I built this after getting tired of manually checking job postings, comparing them to my resume, and then not knowing what to actually learn next. Wanted something that does that whole loop automatically but still asks me before making decisions.

It's a LangGraph agent with 5 tools — web search, local job DB, gap analyzer, resource finder, and market trends. You upload your resume, it figures out where you stand against current job market demand, and generates a learning plan. At 4 points in the flow it stops and asks you to confirm before continuing.

Not trying to make this production-ready. Just wanted to get hands-on with stateful agents and HITL after spending most of my time at work on RAG pipelines.

---

## Screenshots

| Upload Resume | Skill Confirmation | Target Role | Learning Plan |
|---|---|---|
| ![upload](screenshots/upload.png) | ![skills](screenshots/skills.png) | ![target](screenshots/target.png) | ![plan](screenshots/plan.png) |

---

## What I Learned / What Didn't Work

**HITL is trickier than it looks.** The concept is simple — pause, wait, resume. But getting `interrupt()` and `Command(resume=...)` working correctly with FastAPI took longer than expected. The graph state needs to be serializable at every interrupt point, which broke a few times when I was passing raw PDF bytes through state instead of converting them earlier.

**LLaMA 3.3 70B isn't GPT-4 reliable on structured output.** When asking it to return JSON inside a ReAct loop with active tool calls, it occasionally wrapped the output in markdown fences or added extra text before the JSON. Added `.replace("```json", "")` cleanup and fallback defaults in two nodes. Not a dealbreaker but worth knowing upfront.

**Tool docstrings matter more than I expected.** The LLM picks which tool to call entirely based on the docstring. Early version of `analyze_skill_gaps` had a vague description and the agent kept calling `search_job_postings` instead. Rewrote the docstring to be more specific and it fixed immediately — didn't touch any other code.

**MemorySaver loses everything on restart.** Restarting the API mid-session wipes all state. Kept it anyway since this is single-user and restarting mid-flow is rare in practice. `SqliteSaver` is the fix if this needs persistence.

---

## Stack

| | Choice | Why |
|---|---|---|
| Agent | LangGraph | Needed real state management, not just chains |
| LLM | Groq / LLaMA 3.3 70B | Free, fast, supports tool calling |
| Search | Tavily | Cleaner than scraping, built for this use case |
| DB | SQLite + SQLAlchemy | Didn't need anything heavier |
| PDF | PyMuPDF | Just works, handles multi-page fine |
| API | FastAPI | Standard, auto docs |
| UI | Streamlit | Didn't want to build a full frontend for this |
| Tracing | LangSmith | Two env vars and you get full trace visibility |

Chose Groq over OpenAI mostly to save cost on the project. The speed is actually better too.

---

## Why LangGraph and not just LangChain

At work I've mostly used LangChain chains which are stateless — each call is independent. LangGraph gives you a proper state machine where the graph can pause mid-execution, save its state, and resume later. That's the only way human-in-the-loop actually works across multiple steps.

Without checkpointing, you'd have to re-run the entire pipeline from scratch each time the user responds. With it, the graph just picks up from the exact node where it paused.

---

## Project structure

```
autonomous-career-agent/
├── agent/
│   ├── state.py          # AgentState TypedDict
│   ├── tools.py          # 5 tools
│   └── graph.py          # Graph definition + HITL nodes
├── api/
│   └── main.py           # 3 FastAPI endpoints
├── ui/
│   └── app.py            # Streamlit UI
├── db/
│   ├── database.py       # SQLite setup
│   └── seed_data.py      # Sample job postings (AI/ML, India)
├── utils/
│   ├── resume_parser.py  # PDF parsing + skill extraction
│   └── evaluator.py      # Basic plan quality scoring
├── .env.example
└── requirements.txt
```

---

## Setup

```bash
git clone https://github.com/yashagarwal91/autonomous-career-agent
cd autonomous-career-agent

python -m venv career-agent-env
source career-agent-env/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

Three API keys needed — all free tier:

```
GROQ_API_KEY=        # console.groq.com
TAVILY_API_KEY=      # app.tavily.com
LANGCHAIN_API_KEY=   # smith.langchain.com
```

```bash
python db/seed_data.py
```

---

## Running

```bash
# Terminal 1
python api/main.py

# Terminal 2
streamlit run ui/app.py
```
---

## Author
**Yash** — GenAI / LLM Engineer  
Built this to get hands-on with stateful agents and HITL after spending most of my work on RAG pipelines.
