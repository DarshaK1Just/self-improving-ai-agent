# Self-Improving Research Agent

A production-ready AI agent that learns from its mistakes to improve performance over time.

## 🎯 What This Agent Does

**Agent Type:** Research Agent

**Purpose:** Answer queries by intelligently using web search and web fetch tools to gather information.

**Tools Available:**
1. **web_search** - Searches the web for information (required for current events/data)
2. **web_fetch** - Fetches detailed content from URLs (should be used AFTER search)

**When to Use Tools:**
- `web_search`: REQUIRED for queries about current events, recent data, or topics needing verification
- `web_fetch`: OPTIONAL but recommended after searching, to get detailed information

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Research Agent                           │
│  (Executes queries using tools based on learned constraints) │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Execution Trace                           │
│         (Records all tool calls and final answer)            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Evaluator                               │
│   (LLM-based + rule-based mistake identification)           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Agent Memory                               │
│  (Stores executions, evaluations, learned patterns)         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Learning Engine                             │
│  (Detects patterns, generates constraints)                   │
└─────────────────────────────────────────────────────────────┘
```

## 🚨 Types of Mistakes Handled

1. **no_search** - Not using web_search when required
2. **wrong_tool_order** - Calling web_fetch before web_search
3. **skipped_fetch** - Not fetching detailed content after searching
4. **premature_answer** - Answering without gathering information
5. **wrong_tool** - Using incorrect tool for the task

## 🧠 Learning Mechanism

### 1. Execution Phase
- Agent receives query
- Executes tools based on reasoning + learned constraints
- Records complete execution trace

### 2. Evaluation Phase
- **Primary:** LLM-based evaluation (nuanced, context-aware)
- **Fallback:** Rule-based evaluation (fast, deterministic)
- Identifies specific mistakes with descriptions

### 3. Pattern Detection
- Analyzes last 10 evaluations
- Counts mistake type occurrences
- Triggers learning when mistake appears 2+ times

### 4. Constraint Generation
- Creates specific behavioral constraint
- Adds to agent's system prompt
- Influences future executions

### 5. Improvement Loop
```
Run 1: No constraints → Makes mistakes
Run 2: No constraints → Repeats mistakes
Run 3: Pattern detected → Constraint learned
Run 4: With constraint → Fewer mistakes
Run 5: With constraint → Better performance
```

## 📦 Installation

```bash
# Install dependencies
pip install anthropic

# Set API key
export ANTHROPIC_API_KEY='your-anthropic-api-key'

# Run demonstration
python research_agent.py
```

## 💻 Usage

### Basic Usage
```python
from research_agent import AgentMemory, ResearchAgent, Evaluator, LearningEngine

# Initialize
memory = AgentMemory("agent_memory.json")
agent = ResearchAgent(api_key, memory)
evaluator = Evaluator(api_key)
learning_engine = LearningEngine(memory)

# Execute query
trace = agent.execute("What is the current population of Tokyo?")

# Evaluate
evaluation = evaluator.evaluate_execution(trace, query_requires_search=True)
memory.add_evaluation(evaluation)

# Learn from patterns
new_pattern = learning_engine.analyze_and_learn()
if new_pattern:
    memory.add_learned_pattern(new_pattern)
```

### Running Full Demonstration
```python
python research_agent.py
```

## 📊 Expected Output Examples

### Early Run (No Learning Yet)
```
RUN #1: What is the current population of Tokyo?
📋 Tools used: []
💬 Answer: Tokyo has approximately 14 million people...

⚖️  Evaluation: ❌ FAILED
   Reason: Found 1 mistake(s)

🔍 Mistakes identified:
   • no_search: Agent did not search the web for current information
     Expected: Should have used web_search before answering
```

### After Learning
```
RUN #4: What happened in the 2024 Olympics?
📋 Tools used: ['web_search', 'web_fetch']
💬 Answer: Based on search results, the 2024 Olympics...

⚖️  Evaluation: ✅ SUCCESS
   Reason: Agent correctly used tools in proper sequence

📚 Active Learned Constraints: 2
```

### Learning Summary
```
LEARNING SUMMARY
================================================================================

Success Rate (first 3 runs): 33%
Success Rate (last 3 runs): 100%
Improvement: +67%

Total Patterns Learned: 2

  • no_search (occurred 3 times)
    Constraint: ALWAYS use web_search for queries about current events...

  • wrong_tool_order (occurred 2 times)
    Constraint: ALWAYS call web_search BEFORE web_fetch...
```

## 🎯 Key Design Decisions

### 1. Hybrid Evaluation (LLM + Rules)
- **Why:** LLM provides nuanced understanding, rules provide reliability
- **How:** Try LLM evaluation first, fallback to rules on failure
- **Benefit:** Best of both worlds - accuracy and robustness

### 2. Persistent Memory
- **Why:** Agent needs to remember across sessions
- **How:** JSON file storage with dataclasses
- **Benefit:** True long-term learning capability

### 3. Threshold-Based Learning
- **Why:** Avoid learning from one-off mistakes
- **How:** Require 2+ occurrences before creating constraint
- **Benefit:** Filters noise, focuses on real patterns

### 4. Explicit Constraint Injection
- **Why:** Agent needs clear guidance, not implicit learning
- **How:** Add constraints to system prompt
- **Benefit:** Transparent, debuggable, effective

### 5. Structured Data Models
- **Why:** Type safety, clarity, maintainability
- **How:** Python dataclasses with serialization
- **Benefit:** Production-ready code quality

## ⚠️ Known Limitations

1. **Mock Tools:** Current implementation uses simulated web_search/web_fetch
   - **Fix:** Replace with real API calls (e.g., Serper API, requests library)

2. **Simple Pattern Detection:** Only counts occurrences
   - **Improvement:** Could use clustering, similarity metrics for related mistakes

3. **Fixed Constraint Templates:** Pre-defined constraint messages
   - **Improvement:** LLM-generated constraints for each specific case

4. **No Constraint Refinement:** Once learned, constraints don't evolve
   - **Improvement:** Add constraint effectiveness tracking and refinement

5. **Limited Context Window:** Only looks at last 10 evaluations
   - **Improvement:** Implement sliding window or weighted history

6. **No Multi-Agent Scenarios:** Single agent learning
   - **Improvement:** Could share patterns across agent instances

## 🚀 Production Enhancements

For production deployment, consider:

1. **Real Tool Integration**
   ```python
   import requests
   from serpapi import GoogleSearch
   
   def web_search(query: str) -> str:
       search = GoogleSearch({"q": query, "api_key": API_KEY})
       return search.get_dict()
   ```

2. **Database Backend**
   - Replace JSON with PostgreSQL/MongoDB
   - Add indexing for fast pattern queries
   - Enable concurrent access

3. **Monitoring & Observability**
   - Add logging (structured logs with trace IDs)
   - Metrics dashboard (success rate, latency)
   - Alert on degraded performance

4. **A/B Testing Framework**
   - Test new constraints before full rollout
   - Compare constrained vs unconstrained performance

5. **Constraint Management UI**
   - View all learned patterns
   - Enable/disable specific constraints
   - Manual constraint addition

## 📝 Code Quality Features

- ✅ Type hints throughout
- ✅ Docstrings for all classes/methods
- ✅ Error handling with try/catch
- ✅ Dataclasses for structure
- ✅ Separation of concerns
- ✅ Persistent storage
- ✅ Modular design
- ✅ Clear naming conventions

## 🧪 Testing Strategy

```python
# Unit tests
def test_evaluator_identifies_no_search():
    trace = create_trace_without_search()
    eval = evaluator.evaluate_execution(trace)
    assert not eval.success
    assert any(m.mistake_type == 'no_search' for m in eval.mistakes)

# Integration tests
def test_learning_loop():
    # Run agent multiple times
    # Verify mistake count decreases
    # Verify constraints are generated
    
# End-to-end tests
def test_full_improvement_cycle():
    # Fresh memory
    # Run through test queries
    # Assert improvement metrics
```

## 📈 Success Metrics

- **Primary:** Success rate improvement over time (target: +50% after 5 runs)
- **Secondary:** Average mistakes per run decrease
- **Tertiary:** Constraint effectiveness (% of runs where constraint prevents mistake)

## 🤝 Contributing

This is an interview assignment, but the architecture supports:
- Adding new mistake types
- Implementing new tool types
- Alternative learning algorithms
- Enhanced evaluation logic

## 📄 License

This is assignment code for VE.AI interview process.

---

**Author:** AI Engineer Candidate  
**Date:** December 2025  
**Purpose:** Technical Assessment for AI Engineer Role at VE.AI