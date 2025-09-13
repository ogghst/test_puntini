#!/usr/bin/env python3
"""Example of Langfuse integration with LangGraph as per documentation.

This example shows how to properly integrate Langfuse callbacks with LangGraph
following the official documentation patterns.
"""

import os
from langfuse import Langfuse
from langfuse.langchain import CallbackHandler
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate

# Example of how to use Langfuse with LangGraph
def create_langfuse_callback():
    """Create a Langfuse callback handler as per documentation."""
    # Initialize Langfuse client
    langfuse = Langfuse(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "your_public_key_here"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY", "your_secret_key_here"),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    )
    
    # Create callback handler
    callback_handler = CallbackHandler(
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY", "your_public_key_here"),
        secret_key=os.getenv("LANGFUSE_SECRET_KEY", "your_secret_key_here"),
        host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    )
    
    return callback_handler

def example_langgraph_with_langfuse():
    """Example of using Langfuse with LangGraph."""
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import ToolNode
    from langchain_core.tools import tool
    from langchain_openai import ChatOpenAI
    
    # Create Langfuse callback
    callback_handler = create_langfuse_callback()
    
    # Define a simple tool
    @tool
    def get_weather(city: str) -> str:
        """Get the current weather in a given city."""
        return f"The weather in {city} is sunny and 72°F"
    
    # Create LLM
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Create tools
    tools = [get_weather]
    tool_node = ToolNode(tools)
    
    # Define the graph
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
    
    # Run with Langfuse tracing
    result = app.invoke(
        {"messages": [HumanMessage(content="What's the weather in San Francisco?")]},
        config={"callbacks": [callback_handler]}
    )
    
    return result

if __name__ == "__main__":
    print("🚀 Langfuse + LangGraph Integration Example")
    print("=" * 50)
    
    # Check if Langfuse credentials are set
    if not os.getenv("LANGFUSE_PUBLIC_KEY") or not os.getenv("LANGFUSE_SECRET_KEY"):
        print("⚠️  Langfuse credentials not set. Using placeholder values.")
        print("   Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables")
        print("   for real Langfuse tracing.")
    
    try:
        result = example_langgraph_with_langfuse()
        print("✅ Example completed successfully!")
        print(f"📋 Result: {result}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
