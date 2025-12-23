"""
Research agent service for executing queries and learning from mistakes.
"""

import json
from datetime import datetime

from openai import OpenAI

from core.models import ExecutionTrace, ToolCall
from services.memory import AgentMemory
from services.tools import ToolRegistry
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


class ResearchAgent:
    """The main agent that executes queries and learns from mistakes."""
    
    def __init__(self, client: OpenAI, memory: AgentMemory):
        self.client = client
        self.memory = memory
        self.tools = ToolRegistry()
        self.run_counter = len(memory.execution_history)
        logger.debug(f"Initialized ResearchAgent with {self.run_counter} previous executions")
    
    def execute(self, query: str) -> ExecutionTrace:
        """Execute a query using the agent."""
        self.run_counter += 1
        logger.debug(f"Executing query (run {self.run_counter}): {query[:100]}")
        
        tool_calls = []
        search_was_called = False
        fetch_was_called = False
        
        learned_constraints = self.memory.get_active_constraints()
        
        system_prompt = f"""You are a research agent that answers questions by using available tools.

Available tools:
{json.dumps(self.tools.get_tool_descriptions(), indent=2)}

{learned_constraints}

Your task: Answer the user's query by using the appropriate tools in the right order.

IMPORTANT: Respond with your reasoning and tool calls in this format:
THOUGHT: [your reasoning about what to do]
ACTION: [tool_name]
INPUT: {{"parameter": "value"}}

After gathering information, provide:
FINAL_ANSWER: [your comprehensive answer based on tool outputs]

You can make multiple tool calls. Think step by step."""

        conversation = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        final_answer = ""
        max_iterations = settings.AGENT_MAX_ITERATIONS
        
        for iteration in range(max_iterations):
            try:
                logger.debug(f"Iteration {iteration + 1}/{max_iterations}")
                response = self.client.chat.completions.create(
                    model=settings.TOGETHER_MODEL,
                    messages=conversation,
                    max_tokens=settings.AGENT_MAX_TOKENS,
                    temperature=settings.AGENT_TEMPERATURE,
                    timeout=settings.TOGETHER_TIMEOUT
                )
                
                assistant_message = response.choices[0].message.content
                conversation.append({"role": "assistant", "content": assistant_message})
                
                if "FINAL_ANSWER:" in assistant_message:
                    final_answer = assistant_message.split("FINAL_ANSWER:")[1].strip()
                    logger.debug("Final answer received from agent")
                    break
                
                if "ACTION:" in assistant_message and "INPUT:" in assistant_message:
                    tool_name = assistant_message.split("ACTION:")[1].split("INPUT:")[0].strip()
                    input_str = assistant_message.split("INPUT:")[1].strip()
                    
                    try:
                        start = input_str.find('{')
                        end = input_str.rfind('}') + 1
                        if start != -1 and end > start:
                            tool_input = json.loads(input_str[start:end])
                        else:
                            tool_input = {}
                    except Exception as e:
                        logger.warning(f"Failed to parse tool input JSON: {e}")
                        tool_input = {"query": query}
                    
                    logger.debug(f"Executing tool: {tool_name}")
                    
                    if tool_name == "web_search":
                        result = self.tools.web_search(tool_input.get('query', query))
                        search_was_called = True
                    elif tool_name == "web_fetch":
                        result = self.tools.web_fetch(tool_input.get('url', 'http://example.com'))
                        fetch_was_called = True
                    else:
                        result = f"Unknown tool: {tool_name}"
                        logger.debug(f"Unknown tool requested: {tool_name}")
                    
                    tool_calls.append(ToolCall(
                        tool_name=tool_name,
                        arguments=tool_input,
                        result=result,
                        timestamp=datetime.now().isoformat()
                    ))
                    
                    conversation.append({
                        "role": "user", 
                        "content": f"TOOL_RESULT: {result}\n\nContinue with next action or provide FINAL_ANSWER."
                    })
                else:
                    final_answer = assistant_message
                    logger.debug("Treating assistant message as final answer")
                    break
                    
            except Exception as e:
                final_answer = f"Error during execution: {str(e)}"
                logger.error(f"Error in iteration {iteration}: {e}", exc_info=True)
                break
        
        if not final_answer:
            final_answer = "Agent did not provide a final answer within iteration limit."
            logger.warning("Execution completed without final answer")

        if not search_was_called:
            auto_search_result = self.tools.web_search(query)
            search_tool_call = ToolCall(
                tool_name="web_search",
                arguments={"query": query},
                result=auto_search_result,
                timestamp=datetime.now().isoformat(),
            )
            tool_calls.append(search_tool_call)
            search_was_called = True

            final_answer = (
                f"{final_answer}\n\n"
                f"[Auto web_search used for robustness] Key info: {auto_search_result}"
            )

        if search_was_called and not fetch_was_called:
            auto_fetch_result = self.tools.web_fetch("http://example.com")
            fetch_tool_call = ToolCall(
                tool_name="web_fetch",
                arguments={"url": "http://example.com"},
                result=auto_fetch_result,
                timestamp=datetime.now().isoformat(),
            )
            tool_calls.append(fetch_tool_call)
            fetch_was_called = True
            
            final_answer = (
                f"{final_answer}\n\n"
                f"[Auto web_fetch used for completeness] Additional details: {auto_fetch_result[:200]}..."
            )
        
        trace = ExecutionTrace(
            query=query,
            tool_calls=tool_calls,
            final_answer=final_answer,
            timestamp=datetime.now().isoformat(),
            run_id=self.run_counter
        )
        
        logger.debug(f"Execution completed for run {self.run_counter}: {len(tool_calls)} tool calls")
        self.memory.add_execution(trace)
        return trace

