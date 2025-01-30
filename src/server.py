
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from src.leetcode_agent import LeetCodeThinkingAgent
from fastapi.middleware.cors import CORSMiddleware
from src.redis_manager import RedisManager
from src.auth import verify_google_token
from urllib.parse import unquote


class PseudocodeRequest(BaseModel):
    problem_id: str
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
redis_manager = RedisManager()

@app.post("/session/start")
async def start_practice_session(
    problem_count: int = 20,
    user_id: str = Depends(verify_google_token)):
    # Check if user already has assigned problems
    existing_problems = redis_manager.get_user_problems(user_id)
    current_index = redis_manager.get_current_index(user_id)
    next_index = current_index + 1
    if next_index >= len(existing_problems):
        # If user has already completed all problems, reset the index
        redis_manager.set_current_index(user_id, 0)
        existing_problems = redis_manager.get_user_problems(user_id)
        current_index = redis_manager.get_current_index(user_id)
        current_problem = existing_problems[current_index]
    else:
        current_problem = existing_problems[current_index]

    if existing_problems:
        current_problem = existing_problems[current_index]
    else:
        # Get new problems and store them
        problems = agent.get_daily_problems(problem_count)
        redis_manager.store_user_problems(user_id, problems)
        current_problem = problems[0]
    
    session_id = f"{user_id}:{datetime.now().strftime('%Y%m%d%H%M%S')}"
    active_sessions[session_id] = {
        "user_id": user_id,
        "current_index": 0,
        "attempts": {},
    }
    
    return {
        "session_id": session_id,
        "current_problem": current_problem,
        "total_problems": problem_count,
    }



@app.post("/session/{session_id}/submit-pseudocode")
async def submit_pseudocode(
    session_id: str,
    pseudocode: PseudocodeRequest,
    user_id: str = Depends(verify_google_token),
):
    print(f"Endpoint called with session_id: {session_id}")
    def is_solution_complete(solution: str) -> bool:
        completion_triggers = set(
            [
                "solution is complete",
                "approach is correct",
                "logic is sound",
                "well structured",
                "handles all cases",
            ]
        )
        return any(trigger in solution.lower() for trigger in completion_triggers)

    decoded_session_id = unquote(session_id)
    print("Decoded Session ID:", decoded_session_id)
    if decoded_session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get user's problem set from Redis
    user_problems = redis_manager.get_user_problems(user_id)
    if not user_problems:
        raise HTTPException(status_code=404, detail="No problems assigned to user")

    # Get current problem index from Redis
    current_index = redis_manager.get_current_index(user_id)
    current_problem = user_problems[current_index]

    analysis = agent.analyze_pseudocode(current_problem, pseudocode.pseudocode)

    # Track attempts in Redis
    if not redis_manager.get_problem_attempts(user_id, current_problem.id):
        redis_manager.set_problem_attempts(user_id, current_problem.id, 1)
    else:
        redis_manager.increment_problem_attempts(user_id, current_problem.id)

    iterations = redis_manager.get_problem_attempts(user_id, current_problem.id)

    # Mark problem as solved if solution is complete
    if is_solution_complete(analysis):
        redis_manager.mark_problem_solved(user_id, current_problem.id)

    return {
        "analysis": analysis,
        "iterations": iterations,
        "problem_solved": redis_manager.is_problem_solved(user_id, current_problem.id),
    }

@app.get("/session/{session_id}/next-problem")
async def get_next_problem(
    session_id: str, user_id: str = Depends(verify_google_token)
):
    print("Sessions:", active_sessions)
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    user_problems = redis_manager.get_user_problems(user_id)
    current_index = redis_manager.get_current_index(user_id)

    # Increment the index
    next_index = current_index + 1

    # Check if we've reached the end of problems
    if next_index >= len(user_problems):
        return {
            "status": "completed",
            "message": "All problems completed",
            "problem": None,
        }

    # Update current index in Redis
    redis_manager.set_current_index(user_id, next_index)
    next_problem = user_problems[next_index]

    return {
        "status": "success",
        "problem": next_problem,
        "remaining_problems": len(user_problems) - next_index - 1,
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
