"""
Main entry point for the self-improving research agent.
"""

import os
import sys
from openai import OpenAI

from config.settings import settings
from services.memory import AgentMemory
from services.agent import ResearchAgent
from services.evaluator import Evaluator
from services.learning import LearningEngine
from utils.logger import configure_from_env, get_logger

logger = get_logger(__name__)


def demonstrate_learning(new_session: bool = False) -> None:
    """Demonstrate the learning system.
    
    Args:
        new_session: If True, clears execution history before starting
    """
    configure_from_env()
    logger.info("=" * 80)
    logger.info("SELF-IMPROVING RESEARCH AGENT - DEMONSTRATION")
    logger.info("=" * 80)
    
    if not settings.TOGETHER_API_KEY:
        logger.error("TOGETHER_API_KEY environment variable not set")
        logger.info("Get your free API key at: https://api.together.xyz/")
        logger.info("Then run: export TOGETHER_API_KEY='your-key-here'")
        sys.exit(1)
    
    client = OpenAI(
        api_key=settings.TOGETHER_API_KEY,
        base_url=settings.TOGETHER_BASE_URL,
        timeout=settings.TOGETHER_TIMEOUT
    )
    
    memory = AgentMemory(settings.MEMORY_FILE)
    
    if new_session:
        memory.clear_execution_history()
        logger.info("Started new session - execution history cleared")
    
    agent = ResearchAgent(client, memory)
    evaluator = Evaluator(client)
    learning_engine = LearningEngine(memory)
    
    existing_runs = len(memory.execution_history)
    existing_patterns = len(memory.learned_patterns)
    
    if existing_runs > 0:
        logger.info(f"Loaded {existing_runs} previous executions and {existing_patterns} learned patterns")
    else:
        logger.info("Starting fresh - no previous executions found")
    
    test_queries = [
        "What is the current population of Tokyo?",
        "Tell me about recent AI developments",
        "What happened in the 2024 Olympics?",
        "What is the latest news about climate change?",
        "Who won the Nobel Prize in Physics in 2024?",
    ]
    
    logger.info(f"\nProcessing {len(test_queries)} test queries...")
    logger.info("-" * 80)
    
    for i, query in enumerate(test_queries, 1):
        try:
            logger.info(f"\n[RUN {agent.run_counter + 1}] Query: {query}")
            
            trace = agent.execute(query)
            
            tools_used = [tc.tool_name for tc in trace.tool_calls]
            logger.info(f"[EXECUTION] Tools used: {tools_used} | Answer length: {len(trace.final_answer)} chars")
            
            try:
                evaluation = evaluator.evaluate_execution(trace, query_requires_search=True)
                memory.add_evaluation(evaluation)
            except Exception as eval_error:
                logger.error(f"Evaluation error for run {trace.run_id}: {eval_error}", exc_info=True)
                evaluation = evaluator._rule_based_evaluation(trace, query_requires_search=True)
                memory.add_evaluation(evaluation)
            
            new_pattern = learning_engine.analyze_and_learn()
            if new_pattern:
                memory.add_learned_pattern(new_pattern)
                logger.warning(f"[LEARNING] New pattern learned after {new_pattern.occurrences} occurrences")
                
        except Exception as run_error:
            logger.error(f"Error in run {agent.run_counter}: {run_error}", exc_info=True)
            continue
    
    logger.info("\n" + "=" * 80)
    logger.info("DEMONSTRATION SUMMARY")
    logger.info("=" * 80)
    _print_summary(memory)


def _print_summary(memory: AgentMemory) -> None:
    """Print learning summary to console."""
    total_runs = len(memory.evaluation_history)
    
    if total_runs >= 3:
        early_runs = memory.evaluation_history[:3]
        late_runs = memory.evaluation_history[-3:]
        
        success_rate_early = sum(1 for e in early_runs if e.success) / len(early_runs) * 100
        success_rate_late = sum(1 for e in late_runs if e.success) / len(late_runs) * 100
        improvement = success_rate_late - success_rate_early
        
        logger.info(f"\nSUCCESS RATE ANALYSIS:")
        logger.info(f"  Early runs (first 3): {success_rate_early:.0f}%")
        logger.info(f"  Recent runs (last 3):  {success_rate_late:.0f}%")
        logger.info(f"  Improvement:          {improvement:+.0f}%")
    
    logger.info(f"\nPATTERNS LEARNED: {len(memory.learned_patterns)}")
    if memory.learned_patterns:
        for pattern in memory.learned_patterns:
            logger.info(f"\n  Pattern: {pattern.mistake_type}")
            logger.info(f"    Occurrences: {pattern.occurrences}")
            logger.info(f"    Constraint: {pattern.learned_constraint}")
    
    logger.info("\n" + "=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run the self-improving research agent.')
    parser.add_argument('--new-session', action='store_true',
                      help='Start a new session (clears execution history)')
    args = parser.parse_args()
    
    demonstrate_learning(new_session=args.new_session)
