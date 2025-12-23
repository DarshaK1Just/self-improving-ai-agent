"""
Core data models for the research agent system.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional


@dataclass
class ToolCall:
    """Represents a single tool invocation."""
    tool_name: str
    arguments: Dict[str, Any]
    result: str
    timestamp: str


@dataclass
class ExecutionTrace:
    """Records what happened during agent execution."""
    query: str
    tool_calls: List[ToolCall]
    final_answer: str
    timestamp: str
    run_id: int


@dataclass
class Mistake:
    """Represents an identified mistake."""
    mistake_type: str
    description: str
    expected_behavior: str
    step_number: Optional[int]


@dataclass
class Evaluation:
    """Evaluation of a single run."""
    run_id: int
    query: str
    success: bool
    mistakes: List[Mistake]
    evaluation_reason: str
    timestamp: str


@dataclass
class LearnedPattern:
    """A pattern learned from repeated mistakes."""
    pattern_id: str
    mistake_type: str
    occurrences: int
    queries_affected: List[str]
    learned_constraint: str
    created_at: str

