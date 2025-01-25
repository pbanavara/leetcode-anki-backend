from dataclasses import dataclass
from typing import List, Dict


@dataclass
class LeetcodeProblem:
    id: int
    title: str
    description: str
    difficulty: str
    acceptance_rate: float
    frequency: float
    related_topics: List[str]
    asked_by_faang: bool
