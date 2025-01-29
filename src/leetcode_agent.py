import pandas as pd
from datetime import datetime
from src.config import anthropic
from src.problem import LeetcodeProblem
from src.schema import init_database
import sqlite3


class LeetCodeThinkingAgent:
    def __init__(self):
        self.client = anthropic
        init_database()

    def import_from_csv(self, csv_path: str):
        df = pd.read_csv(csv_path)
        conn = sqlite3.connect("leetcode_training.db")
        c = conn.cursor()

        for _, row in df.iterrows():
            c.execute(
                """INSERT INTO problems 
                        (id, title, description, difficulty, acceptance_rate,
                         frequency, related_topics, asked_by_faang)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    row["id"],
                    row["title"],
                    row["description"],
                    row["difficulty"],
                    row["acceptance_rate"],
                    row["frequency"],
                    row["related_topics"],
                    row["asked_by_faang"],
                ),
            )

        conn.commit()
        conn.close()
        return f"Imported {len(df)} problems successfully"

    def get_daily_problems(self, count: int) -> list[LeetcodeProblem]:
        conn = sqlite3.connect("leetcode_training.db")
        c = conn.cursor()
        problems = c.execute(
            """SELECT * FROM problems 
                               ORDER BY RANDOM() LIMIT ?""",
            (count,),
        ).fetchall()
        conn.close()
        return [LeetcodeProblem(*problem) for problem in problems]

    def analyze_pseudocode(self, problem: LeetcodeProblem, pseudocode: str) -> str:
        prompt = f"""
        Problem: {problem.title}
        Description: {problem.description}
        
        User's Pseudocode:
        {pseudocode}
        
        Please provide your analysis in markdown format covering:

        Logical Completeness

        Is the solution logically sound?
        Are all steps clearly defined?
        Edge Cases

        What edge cases are handled?
        What edge cases are missing?
        Efficiency Analysis

        Time complexity
        Space complexity
        Performance considerations
        Suggested Improvements

        Specific code improvements
        Alternative approaches
        Format your response in clear markdown sections. 
        """
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def verify_walkthrough(self, problem: LeetcodeProblem, walkthrough: str) -> str:
        prompt = f"""
        Problem: {problem.title}
        User's Solution Walkthrough:
        {walkthrough}
        
        Verify if the walkthrough:
        1. Correctly handles all cases
        2. Shows clear understanding
        3. Identify any missed edge cases
        """
        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content

    def calculate_difficulty(self, iterations: int) -> str:
        if iterations <= 2:
            return "Easy"
        elif iterations <= 4:
            return "Medium"
        return "Hard"

    def record_attempt(self, user_id: str, problem_id: int, iterations: int):
        user_difficulty = self.calculate_difficulty(iterations)
        conn = sqlite3.connect("leetcode_training.db")
        c = conn.cursor()
        
        leetcode_difficulty = c.execute(
            "SELECT difficulty FROM problems WHERE id = ?", (problem_id,)
        ).fetchone()[0]
        
        c.execute(
            """INSERT INTO user_attempts 
            (user_id, problem_id, iterations, user_difficulty, 
            leetcode_difficulty, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                problem_id,
                iterations,
                user_difficulty,
                leetcode_difficulty,
                datetime.now(),
            ),
        )
        
        conn.commit()
        conn.close()
        
        comparison_message = (
        "✅ Your experience matches LeetCode's rating!"
        if user_difficulty == leetcode_difficulty
        else f"📊 Interesting! You found this {user_difficulty.lower()} while LeetCode rates it as {leetcode_difficulty.lower()}")
    
        return {
            "user_difficulty": user_difficulty,
            "leetcode_difficulty": leetcode_difficulty,
            "comparison_message": comparison_message
        }

    

    def generate_python_solution(self, problem: LeetcodeProblem) -> str:
        prompt = f"""
        Problem: {problem.title}
        Description: {problem.description}
        
        Generate a complete, efficient Python solution for this problem.
        Include:
        1. Time and space complexity analysis
        2. Clear variable names and comments
        3. Edge case handling
        4. Example test cases
        
        Format the response as:
        ```python
        # Solution explanation and complexity analysis
        
        def solution_function():
            # Implementation
        
        # Test cases
        ```
        """
        
        response = self.client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=2000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content

