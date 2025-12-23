"""
Evaluation service for assessing agent execution quality.
"""

import json
from datetime import datetime
from typing import List

from openai import OpenAI

from core.models import ExecutionTrace, Evaluation, Mistake
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class Evaluator:
    """Evaluates agent executions and identifies mistakes."""
    
    def __init__(self, client: OpenAI):
        self.client = client
    
    def evaluate_execution(
        self, 
        trace: ExecutionTrace, 
        query_requires_search: bool = True
    ) -> Evaluation:
        """Evaluate execution and identify mistakes."""
        logger.debug(f"Evaluating execution for run {trace.run_id}")
        
        tools_used = [tc.tool_name for tc in trace.tool_calls]
        execution_summary = f"""
Query: {trace.query}
Tools called: {tools_used}
Number of tool calls: {len(trace.tool_calls)}
Final answer: {trace.final_answer[:200]}...

Tool call sequence:
"""
        for i, tc in enumerate(trace.tool_calls, 1):
            execution_summary += f"{i}. {tc.tool_name}({list(tc.arguments.keys())})\n"
        
        evaluation_prompt = f"""You are evaluating an AI agent's execution. The agent is a research agent that should:
1. Use web_search to find information when needed
2. Use web_fetch to get detailed content AFTER searching
3. Provide well-researched answers based on tool outputs

Execution to evaluate:
{execution_summary}

Evaluate this execution and respond in JSON format:
{{
    "success": true/false,
    "evaluation_reason": "brief explanation",
    "mistakes": [
        {{
            "mistake_type": "no_search|wrong_tool_order|skipped_fetch|premature_answer|other",
            "description": "what went wrong",
            "expected_behavior": "what should have happened",
            "step_number": step_number or null
        }}
    ]
}}

Common mistakes to check:
- Did the agent skip web_search for a query that needs current information?
- Did the agent call web_fetch before web_search?
- Did the agent provide an answer without gathering sufficient information?
- Did the agent use the wrong tool for the task?

Respond ONLY with valid JSON, no markdown formatting."""

        try:
            response = self.client.chat.completions.create(
                model=settings.TOGETHER_MODEL,
                messages=[{"role": "user", "content": evaluation_prompt}],
                max_tokens=settings.EVALUATOR_MAX_TOKENS,
                temperature=settings.EVALUATOR_TEMPERATURE,
                timeout=settings.EVALUATOR_TIMEOUT
            )
            
            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith("```"):
                result_text = result_text.split("```")[1]
                if result_text.startswith("json"):
                    result_text = result_text[4:]
                result_text = result_text.strip()
            
            result = json.loads(result_text)
            
            mistakes = [
                Mistake(
                    mistake_type=m['mistake_type'],
                    description=m['description'],
                    expected_behavior=m['expected_behavior'],
                    step_number=m.get('step_number')
                ) for m in result.get('mistakes', [])
            ]
            
            evaluation = Evaluation(
                run_id=trace.run_id,
                query=trace.query,
                success=result['success'],
                mistakes=mistakes,
                evaluation_reason=result['evaluation_reason'],
                timestamp=datetime.now().isoformat()
            )
            
            if evaluation.success:
                logger.info(f"[EVALUATION] Run {trace.run_id}: SUCCESS")
            else:
                logger.warning(f"[EVALUATION] Run {trace.run_id}: FAILED - {evaluation.evaluation_reason}")
                for mistake in evaluation.mistakes:
                    logger.warning(f"[MISTAKE] Type: {mistake.mistake_type} | Step: {mistake.step_number} | {mistake.description}")
            
            return evaluation
            
        except Exception as e:
            logger.warning(f"LLM evaluation failed ({e}), using rule-based fallback")
            return self._rule_based_evaluation(trace, query_requires_search)
    
    def _rule_based_evaluation(
        self, 
        trace: ExecutionTrace, 
        query_requires_search: bool
    ) -> Evaluation:
        """Simple rule-based fallback evaluation."""
        logger.debug("Using rule-based evaluation")
        mistakes = []
        success = True
        
        tools_used = [tc.tool_name for tc in trace.tool_calls]
        
        if query_requires_search and 'web_search' not in tools_used:
            mistakes.append(Mistake(
                mistake_type="no_search",
                description="Agent did not search the web for a query requiring current information",
                expected_behavior="Should have used web_search before answering",
                step_number=0
            ))
            success = False
        
        if 'web_fetch' in tools_used and 'web_search' in tools_used:
            search_idx = tools_used.index('web_search')
            fetch_idx = tools_used.index('web_fetch')
            if fetch_idx < search_idx:
                mistakes.append(Mistake(
                    mistake_type="wrong_tool_order",
                    description="Agent called web_fetch before web_search",
                    expected_behavior="Should search first, then fetch specific URLs",
                    step_number=fetch_idx
                ))
                success = False
        
        if 'web_search' in tools_used and 'web_fetch' not in tools_used:
            mistakes.append(Mistake(
                mistake_type="skipped_fetch",
                description="Agent called web_search but did not call web_fetch to gather detailed content",
                expected_behavior="Should call web_fetch after web_search to get detailed information from sources",
                step_number=None
            ))
            success = False
        
        if len(trace.final_answer) < 50 and len(tools_used) == 0:
            mistakes.append(Mistake(
                mistake_type="premature_answer",
                description="Agent provided a very short answer without using any tools",
                expected_behavior="Should gather information using tools before answering",
                step_number=None
            ))
            success = False
        
        reason = "Execution completed successfully" if success else f"Found {len(mistakes)} mistake(s)"
        
        evaluation = Evaluation(
            run_id=trace.run_id,
            query=trace.query,
            success=success,
            mistakes=mistakes,
            evaluation_reason=reason,
            timestamp=datetime.now().isoformat()
        )
        
        if evaluation.success:
            logger.info(f"[EVALUATION] Run {trace.run_id}: SUCCESS")
        else:
            logger.warning(f"[EVALUATION] Run {trace.run_id}: FAILED - {reason}")
            for mistake in evaluation.mistakes:
                logger.warning(f"[MISTAKE] Type: {mistake.mistake_type} | Step: {mistake.step_number} | {mistake.description}")
        
        return evaluation
