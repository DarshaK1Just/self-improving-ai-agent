"""
Agent memory management for storing executions, evaluations, and learned patterns.
"""

import json
import os
from typing import List
from dataclasses import asdict

from core.models import ExecutionTrace, Evaluation, LearnedPattern
from utils.logger import get_logger

logger = get_logger(__name__)


class AgentMemory:
    """Manages learned patterns and constraints."""
    
    def __init__(self, memory_file: str = "agent_memory.json"):
        self.memory_file = memory_file
        self.learned_patterns: List[LearnedPattern] = []
        self.execution_history: List[ExecutionTrace] = []
        self.evaluation_history: List[Evaluation] = []
        self.load_memory()
    
    def load_memory(self) -> None:
        """Load memory from disk."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                    self.learned_patterns = [
                        LearnedPattern(**p) for p in data.get('learned_patterns', [])
                    ]
                    self.execution_history = [
                        ExecutionTrace(
                            query=e['query'],
                            tool_calls=[self._load_tool_call(tc) for tc in e['tool_calls']],
                            final_answer=e['final_answer'],
                            timestamp=e['timestamp'],
                            run_id=e['run_id']
                        ) for e in data.get('execution_history', [])
                    ]
                    self.evaluation_history = [
                        Evaluation(
                            run_id=ev['run_id'],
                            query=ev['query'],
                            success=ev['success'],
                            mistakes=[self._load_mistake(m) for m in ev['mistakes']],
                            evaluation_reason=ev['evaluation_reason'],
                            timestamp=ev['timestamp']
                        ) for ev in data.get('evaluation_history', [])
                    ]
                logger.debug(f"Loaded memory from {self.memory_file}: {len(self.execution_history)} executions, {len(self.evaluation_history)} evaluations, {len(self.learned_patterns)} patterns")
            except Exception as e:
                logger.warning(f"Could not load existing memory: {e}")
    
    def _load_tool_call(self, data: dict):
        """Load ToolCall from dict."""
        from core.models import ToolCall
        return ToolCall(**data)
    
    def _load_mistake(self, data: dict):
        """Load Mistake from dict."""
        from core.models import Mistake
        return Mistake(**data)
    
    def save_memory(self) -> None:
        """Save memory to disk."""
        try:
            data = {
                'learned_patterns': [asdict(p) for p in self.learned_patterns],
                'execution_history': [
                    {
                        'query': e.query,
                        'tool_calls': [asdict(tc) for tc in e.tool_calls],
                        'final_answer': e.final_answer,
                        'timestamp': e.timestamp,
                        'run_id': e.run_id
                    } for e in self.execution_history
                ],
                'evaluation_history': [
                    {
                        'run_id': ev.run_id,
                        'query': ev.query,
                        'success': ev.success,
                        'mistakes': [asdict(m) for m in ev.mistakes],
                        'evaluation_reason': ev.evaluation_reason,
                        'timestamp': ev.timestamp
                    } for ev in self.evaluation_history
                ]
            }
            with open(self.memory_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Saved memory to {self.memory_file}")
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")
    
    def add_execution(self, trace: ExecutionTrace) -> None:
        """Record an execution."""
        self.execution_history.append(trace)
        self.save_memory()
        logger.debug(f"Recorded execution trace for run {trace.run_id}")
    
    def add_evaluation(self, evaluation: Evaluation) -> None:
        """Record an evaluation."""
        self.evaluation_history.append(evaluation)
        self.save_memory()
        status = "SUCCESS" if evaluation.success else "FAILED"
        logger.debug(f"Recorded evaluation for run {evaluation.run_id}: {status}")
    
    def add_learned_pattern(self, pattern: LearnedPattern) -> None:
        """Record a learned pattern."""
        self.learned_patterns.append(pattern)
        self.save_memory()
        logger.debug(f"Recorded learned pattern: {pattern.mistake_type} (occurred {pattern.occurrences} times)")
    
    def get_active_constraints(self) -> str:
        """Get current learned constraints as a string for the agent."""
        if not self.learned_patterns:
            return "No learned constraints yet."
        
        constraints = "LEARNED CONSTRAINTS (from past mistakes):\n"
        for pattern in self.learned_patterns:
            constraints += f"- {pattern.learned_constraint}\n"
        return constraints

    def clear_execution_history(self) -> None:
        """Clear execution history while preserving learned patterns."""
        self.execution_history = []
        self.evaluation_history = []
        self.save_memory()  # Changed to use the correct method name
        logger.info("Cleared execution history while preserving learned patterns")
