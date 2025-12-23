"""
Unit tests for the self-improving agent system.
Run with: python test_agent.py
"""

import os
import tempfile
from datetime import datetime

from core.models import (
    ToolCall, ExecutionTrace, Mistake, 
    Evaluation, LearnedPattern
)
from services.memory import AgentMemory
from services.learning import LearningEngine
from services.tools import ToolRegistry


def test_agent_memory():
    """Test memory persistence"""
    print("Testing AgentMemory...")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        memory = AgentMemory(temp_file)
        
        trace = ExecutionTrace(
            query="test query",
            tool_calls=[
                ToolCall("web_search", {"query": "test"}, "result", datetime.now().isoformat())
            ],
            final_answer="test answer",
            timestamp=datetime.now().isoformat(),
            run_id=1
        )
        memory.add_execution(trace)
        
        memory2 = AgentMemory(temp_file)
        assert len(memory2.execution_history) == 1
        assert memory2.execution_history[0].query == "test query"
        
        print("  Memory persistence works")
        
    finally:
        os.unlink(temp_file)


def test_learning_engine():
    """Test pattern detection"""
    print("Testing LearningEngine...")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        memory = AgentMemory(temp_file)
        learning_engine = LearningEngine(memory)
        
        for i in range(3):
            eval = Evaluation(
                run_id=i,
                query=f"query {i}",
                success=False,
                mistakes=[
                    Mistake(
                        mistake_type="no_search",
                        description="Skipped search",
                        expected_behavior="Should search",
                        step_number=None
                    )
                ],
                evaluation_reason="Failed",
                timestamp=datetime.now().isoformat()
            )
            memory.add_evaluation(eval)
        
        pattern = learning_engine.analyze_and_learn()
        assert pattern is not None
        assert pattern.mistake_type == "no_search"
        assert pattern.occurrences >= 2
        
        print("  Pattern detection works")
        
    finally:
        os.unlink(temp_file)


def test_constraint_generation():
    """Test constraint generation"""
    print("Testing constraint generation...")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        memory = AgentMemory(temp_file)
        
        pattern = LearnedPattern(
            pattern_id="test_1",
            mistake_type="no_search",
            occurrences=2,
            queries_affected=["q1", "q2"],
            learned_constraint="Always search first",
            created_at=datetime.now().isoformat()
        )
        memory.add_learned_pattern(pattern)
        
        constraints = memory.get_active_constraints()
        assert "Always search first" in constraints
        
        print("  Constraint generation works")
        
    finally:
        os.unlink(temp_file)


def test_tool_registry():
    """Test tool registry"""
    print("Testing ToolRegistry...")
    
    tools = ToolRegistry()
    
    result = tools.web_search("test query")
    assert "test query" in result
    assert "SEARCH RESULTS" in result
    
    result = tools.web_fetch("http://example.com")
    assert "example.com" in result
    assert "WEBPAGE CONTENT" in result
    
    descriptions = tools.get_tool_descriptions()
    assert len(descriptions) == 2
    assert any(d['name'] == 'web_search' for d in descriptions)
    
    print("  Tool registry works")


def test_evaluation_logic():
    """Test evaluation logic"""
    print("Testing evaluation logic...")
    
    trace = ExecutionTrace(
        query="What is the current weather?",
        tool_calls=[],
        final_answer="It's sunny",
        timestamp=datetime.now().isoformat(),
        run_id=1
    )
    
    from services.evaluator import Evaluator
    from openai import OpenAI
    
    class MockClient:
        pass
    
    evaluator = Evaluator(MockClient())
    evaluation = evaluator._rule_based_evaluation(trace, query_requires_search=True)
    
    assert not evaluation.success
    assert len(evaluation.mistakes) == 1
    assert evaluation.mistakes[0].mistake_type == "no_search"
    
    print("  Evaluation logic works")


def test_mistake_patterns():
    """Test different mistake types"""
    print("Testing mistake patterns...")
    
    trace = ExecutionTrace(
        query="test",
        tool_calls=[
            ToolCall("web_fetch", {}, "result", datetime.now().isoformat()),
            ToolCall("web_search", {}, "result", datetime.now().isoformat())
        ],
        final_answer="answer",
        timestamp=datetime.now().isoformat(),
        run_id=1
    )
    
    tools_used = [tc.tool_name for tc in trace.tool_calls]
    assert tools_used.index('web_fetch') < tools_used.index('web_search')
    
    print("  Mistake pattern detection works")

def test_session_management():
    """Test session management functionality"""
    print("Testing session management...")
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        temp_file = f.name
    
    try:
        # Test with new session
        memory = AgentMemory(temp_file)
        memory.add_execution(create_test_trace())
        assert len(memory.execution_history) == 1
        
        # Clear history
        memory.clear_execution_history()
        assert len(memory.execution_history) == 0
        assert len(memory.evaluation_history) == 0
        
        # Verify patterns are preserved
        pattern = create_test_pattern()
        memory.add_learned_pattern(pattern)
        memory.clear_execution_history()
        assert len(memory.learned_patterns) == 1
        
        print("  Session management works")
        
    finally:
        os.unlink(temp_file)

def create_test_trace():
    """Helper to create a test execution trace"""
    return ExecutionTrace(
        query="test query",
        tool_calls=[ToolCall("web_search", {"query": "test"}, "result", datetime.now().isoformat())],
        final_answer="test answer",
        timestamp=datetime.now().isoformat(),
        run_id=1
    )

def create_test_pattern():
    """Helper to create a test learned pattern"""
    return LearnedPattern(
        pattern_id="test_pattern",
        mistake_type="test_mistake",
        occurrences=1,
        queries_affected=["test_query"],
        learned_constraint="Test constraint",
        created_at=datetime.now().isoformat()
    )

def run_all_tests():
    """Run all tests"""
    print("\nRunning Self-Improving Agent Tests\n")
    
    tests = [
        test_agent_memory,
        test_learning_engine,
        test_constraint_generation,
        test_tool_registry,
        test_evaluation_logic,
        test_mistake_patterns,
        test_session_management
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  Test failed: {e}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
