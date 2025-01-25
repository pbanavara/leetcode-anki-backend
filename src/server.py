from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from src.leetcode_agent import LeetCodeThinkingAgent
from fastapi.middleware.cors import CORSMiddleware

class PseudocodeRequest(BaseModel):
    pseudocode: str

class WalkthroughRequest(BaseModel):
    walkthrough: str


app = FastAPI(title="LeetCode Practice API")
agent = LeetCodeThinkingAgent()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PracticeSession(BaseModel):
    problem_id: int
    pseudocode: str
    iterations: int = 0
    is_completed: bool = False


# Store active practice sessions
active_sessions = {}

@app.post("/session/start")
async def start_practice_session(problem_count: int):
    problems = agent.get_daily_problems(problem_count)
    session_id = datetime.now().strftime("%Y%m%d%H%M%S")
    active_sessions[session_id] = {
        "problems": problems,
        "current_index": 0,
        "attempts": {},
    }
    return {
        "session_id": session_id,
        "current_problem": problems[0],
        "total_problems": len(problems),
    }


@app.post("/session/{session_id}/submit-pseudocode")
async def submit_pseudocode(session_id: str, pseudocode: PseudocodeRequest):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]
    current_problem = session["problems"][session["current_index"]]

    analysis = agent.analyze_pseudocode(current_problem, pseudocode.pseudocode)

    # Track iterations
    if current_problem.id not in session["attempts"]:
        session["attempts"][current_problem.id] = {"iterations": 1}
    else:
        session["attempts"][current_problem.id]["iterations"] += 1

    return {
        "analysis": analysis,
        "iterations": session["attempts"][current_problem.id]["iterations"],
    }


@app.post("/session/{session_id}/submit-walkthrough")
async def submit_walkthrough(session_id: str, walkthrough: WalkthroughRequest):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]
    current_problem = session["problems"][session["current_index"]]

    verification = agent.verify_walkthrough(current_problem, 
                                            walkthrough.walkthrough)
    iterations = session["attempts"][current_problem.id]["iterations"]

    # Record the attempt
    agent.record_attempt(current_problem.id, iterations)

    # Move to next problem
    session["current_index"] += 1

    next_problem = None
    if session["current_index"] < len(session["problems"]):
        next_problem = session["problems"][session["current_index"]]

    return {
        "verification": verification,
        "next_problem": next_problem,
        "session_completed": next_problem is None,
    }


@app.get("/session/{session_id}/status")
async def get_session_status(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    session = active_sessions[session_id]
    return {
        "total_problems": len(session["problems"]),
        "completed_problems": session["current_index"],
        "current_problem": session["problems"][session["current_index"]]
        if session["current_index"] < len(session["problems"])
        else None,
    }


@app.delete("/session/{session_id}")
async def end_session(session_id: str):
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del active_sessions[session_id]
    return {"message": "Session ended successfully"}
