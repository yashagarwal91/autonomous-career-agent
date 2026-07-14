"""
API Layer — Autonomous Career Intelligence Agent
"""

import os
import sys
import uuid
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langgraph.types import Command

from agent.graph import graph
from db.database import init_db
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Autonomous Career Intelligence Agent", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/start")
async def start_agent(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files supported.")

    session_id = str(uuid.uuid4())
    pdf_bytes  = await file.read()
    config     = {"configurable": {"thread_id": session_id}}

    graph.invoke(
        {
            "messages"       : [],
            "resume_text"    : pdf_bytes,
            "reasoning_trace": [],
            "session_id"     : session_id
        },
        config=config
    )

    interrupt_data = {}
    for task in graph.get_state(config).tasks:
        if hasattr(task, "interrupts") and task.interrupts:
            interrupt_data = task.interrupts[0].value
            break

    return {"session_id": session_id, "status": "waiting_for_human", "interrupt": interrupt_data}


class HumanResponse(BaseModel):
    human_response: dict


@app.post("/resume/{session_id}")
def resume_agent(session_id: str, body: HumanResponse):
    config = {"configurable": {"thread_id": session_id}}

    graph.invoke(Command(resume=body.human_response), config=config)

    state       = graph.get_state(config)
    is_complete = len(state.next) == 0

    if is_complete:
        return {
            "status"       : "completed",
            "eval_score"   : state.values.get("eval_score"),
            "learning_plan": state.values.get("learning_plan")
        }

    interrupt_data = {}
    for task in state.tasks:
        if hasattr(task, "interrupts") and task.interrupts:
            interrupt_data = task.interrupts[0].value
            break

    return {"status": "waiting_for_human", "interrupt": interrupt_data}


@app.get("/status/{session_id}")
def get_status(session_id: str):
    config = {"configurable": {"thread_id": session_id}}
    state  = graph.get_state(config)

    return {
        "current_node"   : state.values.get("current_node"),
        "reasoning_trace": state.values.get("reasoning_trace", []),
        "is_complete"    : len(state.next) == 0
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)