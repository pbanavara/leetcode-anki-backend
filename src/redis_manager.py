import redis
import json
from typing import List
from src.problem import LeetcodeProblem


class RedisManager:
    def __init__(self):
        self.redis_client = redis.Redis(host="localhost", port=6379, db=0)

    def store_user_problems(self, user_id: str, problems: List[LeetcodeProblem]):
        problems_data = [vars(problem) for problem in problems]
        self.redis_client.set(f"user:{user_id}:problems", json.dumps(problems_data))
        self.redis_client.set(f"user:{user_id}:current_index", 0)

    def get_user_problems(self, user_id: str) -> List[LeetcodeProblem]:
        problems_data = self.redis_client.get(f"user:{user_id}:problems")
        if not problems_data:
            return None
        problems_list = json.loads(problems_data)
        return [LeetcodeProblem(**p) for p in problems_list]
    
    def get_current_index(self, user_id: str) -> int:
        return int(self.redis_client.get(f"user:{user_id}:current_index") or 0)

    def get_problem_attempts(self, user_id: str, problem_id: int) -> int:
        return int(self.redis_client.get(f"user:{user_id}:problem:{problem_id}:attempts") or 0)

    def set_problem_attempts(self, user_id: str, problem_id: int, attempts: int):
        self.redis_client.set(f"user:{user_id}:problem:{problem_id}:attempts", attempts)

    def increment_problem_attempts(self, user_id: str, problem_id: int):
        self.redis_client.incr(f"user:{user_id}:problem:{problem_id}:attempts")

    def mark_problem_solved(self, user_id: str, problem_id: int):
        self.redis_client.set(f"user:{user_id}:problem:{problem_id}:solved", 1)

    def is_problem_solved(self, user_id: str, problem_id: int) -> bool:
        return bool(self.redis_client.get(f"user:{user_id}:problem:{problem_id}:solved"))
    
    def set_current_index(self, user_id: str, index: int):
        self.redis_client.set(f"user:{user_id}:current_index", index)

