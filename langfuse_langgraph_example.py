#!/usr/bin/env python3
"""Example of proper Langfuse integration with LangGraph.

This example shows the correct way to integrate Langfuse callbacks with LangGraph
following the official documentation patterns.
"""

import os
from langfuse.langchain import CallbackHandler
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import TypedDict, Annotated
from operator import add

# Define the state
class State(TypedDict):
    messages: Annotated[list, add]

def create_agent_with_langfuse():
    """Create a simple agent with Langfuse integration."""
    
    # Create Langfuse callback handler
    callback_handler = CallbackHandler()
    
    # Create LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Define a simple tool
    @tool
    def get_weather(city: str) -> str:
        """Get the current weather in a given city."""
        return f"The weather in {city} is sunny and 72°F"
    
    # Create tools
    tools = [get_weather]
    tool_node = ToolNode(tools)
    
    # Define the agent function
    def call_model(state):
        messages = state["messages"]
        response = llm.invoke(messages, config={"callbacks": [callback_handler]})
        return {"messages": [response]}
    
    def should_continue(state):
        messages = state["messages"]
        last_message = messages[-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        return END
    
    # Build the graph
    workflow = StateGraph({"messages": list})
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    workflow.add_edge("agent", should_continue)
    workflow.add_edge("tools", "agent")
    workflow.set_entry_point("agent")
    
    # Compile the graph
    app = workflow.compile()
    
    return app, callback_handler

def run_example():
    """Run the example with Langfuse tracing."""
    print("🚀 Langfuse + LangGraph Integration Example")
    print("=" * 50)
    
    # Check if Langfuse credentials are set
    if not os.getenv("LANGFUSE_PUBLIC_KEY") or not os.getenv("LANGFUSE_SECRET_KEY"):
        print("⚠️  Langfuse credentials not set.")
        print("   Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables")
        print("   for real Langfuse tracing.")
        print("   Continuing with example anyway...")
    
    try:
        # Create the agent
        app, callback_handler = create_agent_with_langfuse()
        
        # Run with Langfuse tracing
        result = app.invoke(
            {"messages": [("user", "What's the weather in San Francisco?")]},
            config={"callbacks": [callback_handler]}
        )
        
        print("✅ Example completed successfully!")
        print(f"📋 Result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_example()
