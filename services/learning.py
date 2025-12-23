"""
Learning engine for pattern detection and constraint generation.
"""

from datetime import datetime
from typing import Optional, List
from collections import defaultdict

from core.models import LearnedPattern
from services.memory import AgentMemory
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class LearningEngine:
    """Analyzes patterns in mistakes and generates learned constraints."""
    
    def __init__(self, memory: AgentMemory):
        self.memory = memory
    
    def analyze_and_learn(self) -> Optional[LearnedPattern]:
        """Analyze recent evaluations to find patterns and generate constraints."""
        if len(self.memory.evaluation_history) < 2:
            logger.debug("Insufficient evaluation history for pattern analysis")
            return None
        
        mistake_counts = defaultdict(lambda: {'count': 0, 'queries': []})
        window_size = settings.LEARNING_WINDOW_SIZE
        recent_evals = self.memory.evaluation_history[-window_size:]
        
        logger.debug(f"Analyzing {len(recent_evals)} recent evaluations for patterns")
        
        for eval_record in recent_evals:
            for mistake in eval_record.mistakes:
                mistake_counts[mistake.mistake_type]['count'] += 1
                mistake_counts[mistake.mistake_type]['queries'].append(eval_record.query)
        
        existing_patterns = {p.mistake_type for p in self.memory.learned_patterns}
        threshold = settings.LEARNING_THRESHOLD
        
        for mistake_type, data in mistake_counts.items():
            if data['count'] >= threshold and mistake_type not in existing_patterns:
                constraint = self._generate_constraint(mistake_type, data['queries'])
                
                pattern = LearnedPattern(
                    pattern_id=f"pattern_{len(self.memory.learned_patterns) + 1}",
                    mistake_type=mistake_type,
                    occurrences=data['count'],
                    queries_affected=data['queries'][:3],
                    learned_constraint=constraint,
                    created_at=datetime.now().isoformat()
                )
                
                logger.warning(f"[PATTERN DETECTED] Mistake type: {mistake_type} (occurred {data['count']} times)")
                logger.warning(f"[NEW CONSTRAINT] {constraint}")
                return pattern
        
        return None
    
    def _generate_constraint(self, mistake_type: str, queries: List[str]) -> str:
        """Generate constraint based on mistake type."""
        constraints = {
            'no_search': "ALWAYS use web_search for queries about current events, recent information, or topics requiring verification. Never answer without searching first.",
            'wrong_tool_order': "ALWAYS call web_search BEFORE web_fetch. You must search to find relevant URLs before you can fetch them.",
            'skipped_fetch': "After using web_search, ALWAYS use web_fetch to get detailed information from at least one relevant source before answering.",
            'premature_answer': "NEVER provide a final answer without first using tools to gather information. Always search and fetch before synthesizing an answer.",
            'wrong_tool': "Verify you are using the correct tool for the task. Read tool descriptions carefully before choosing."
        }
        
        return constraints.get(
            mistake_type, 
            f"Be careful to avoid mistakes of type: {mistake_type}"
        )
