#!/usr/bin/env python3
"""Example script demonstrating the Puntini Agent.

This script shows how to use the agent to perform graph operations
with natural language goals.
"""

import asyncio
from puntini import create_simple_agent, create_langfuse_tracer


async def main():
    """Main example function."""
    print("🚀 Starting Puntini Agent Example")
    
    # Create agent and tracer
    agent = create_simple_agent()
    tracer = create_langfuse_tracer()
    
    # Define a simple goal
    goal = "Create a node called 'Example' with a property 'type' set to 'demo'"
    
    # Prepare initial state
    initial_state = {
        "goal": goal,
        "plan": [],
        "progress": [],
        "failures": [],
        "retry_count": 0,
        "max_retries": 3,
        "messages": [],
        "current_step": "parse_goal",
        "current_attempt": 1,
        "artifacts": [],
        "result": {},
        "_tool_signature": {},
        "_error_context": {},
        "_escalation_context": {}
    }
    
    print(f"🎯 Goal: {goal}")
    print("🔄 Running agent...")
    
    try:
        # Run the agent with tracing and proper configuration
        config = {"configurable": {"thread_id": "example-thread"}}
        with tracer.start_trace("example-execution") as trace:
            result = agent.invoke(initial_state, config)
            
            print("✅ Agent completed successfully!")
            print(f"📊 Final result: {result.get('result', {})}")
            print(f"📈 Progress: {result.get('progress', [])}")
            
    except Exception as e:
        print(f"❌ Agent failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        tracer.flush()


if __name__ == "__main__":
    asyncio.run(main())
