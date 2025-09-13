#!/usr/bin/env python3
"""Test script to verify the parse_goal implementation works correctly.

This script tests the parse_goal node with a simple goal to ensure
the LLM integration and structured output parsing works as expected.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from puntini.nodes.parse_goal import parse_goal
from puntini.models.goal_schemas import GoalSpec, GoalComplexity


async def test_parse_goal_implementation():
    """Test the parse_goal implementation with a real goal."""
    print("🧪 Testing parse_goal implementation...")
    
    # Test goal
    test_goal = "Create a person node called John with age 30 and city New York"
    
    print(f"🎯 Test goal: {test_goal}")
    
    # Prepare initial state
    initial_state = {
        "goal": test_goal,
        "current_attempt": 1,
        "plan": [],
        "progress": [],
        "failures": [],
        "retry_count": 0,
        "max_retries": 3,
        "messages": [],
        "current_step": "parse_goal",
        "artifacts": [],
        "result": {},
        "_tool_signature": {},
        "_error_context": {},
        "_escalation_context": {}
    }
    
    try:
        # Call parse_goal
        result = parse_goal(initial_state)
        
        print("✅ parse_goal executed successfully!")
        print(f"📊 Result status: {result['result']['status']}")
        print(f"🔄 Next step: {result['current_step']}")
        
        if result['result']['status'] == 'success':
            parsed_goal = result['result']['parsed_goal']
            print(f"🎯 Intent: {parsed_goal.get('intent', 'N/A')}")
            print(f"📈 Complexity: {parsed_goal.get('complexity', 'N/A')}")
            print(f"🔗 Entities found: {len(parsed_goal.get('entities', []))}")
            print(f"⚠️ Constraints found: {len(parsed_goal.get('constraints', []))}")
            print(f"💡 Domain hints: {len(parsed_goal.get('domain_hints', []))}")
            
            # Show entities
            entities = parsed_goal.get('entities', [])
            if entities:
                print("\n📋 Extracted entities:")
                for i, entity in enumerate(entities, 1):
                    print(f"  {i}. {entity.get('name', 'N/A')} ({entity.get('type', 'N/A')})")
                    if entity.get('label'):
                        print(f"     Label: {entity['label']}")
                    if entity.get('properties'):
                        print(f"     Properties: {entity['properties']}")
            
            # Show constraints
            constraints = parsed_goal.get('constraints', [])
            if constraints:
                print("\n⚠️ Extracted constraints:")
                for i, constraint in enumerate(constraints, 1):
                    print(f"  {i}. {constraint.get('type', 'N/A')}: {constraint.get('description', 'N/A')}")
            
            # Show domain hints
            domain_hints = parsed_goal.get('domain_hints', [])
            if domain_hints:
                print("\n💡 Domain hints:")
                for i, hint in enumerate(domain_hints, 1):
                    print(f"  {i}. {hint.get('domain', 'N/A')}: {hint.get('hint', 'N/A')}")
            
            print(f"\n🎯 Goal requires graph operations: {result['result']['requires_graph_ops']}")
            print(f"🎯 Is simple goal: {result['result']['is_simple']}")
            
        else:
            print(f"❌ Error: {result['result'].get('error', 'Unknown error')}")
            print(f"🔍 Error type: {result['result'].get('error_type', 'N/A')}")
        
        return result['result']['status'] == 'success'
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_goal_schema_validation():
    """Test the GoalSpec schema validation."""
    print("\n🧪 Testing GoalSpec schema validation...")
    
    try:
        # Test valid goal spec
        valid_goal = GoalSpec(
            original_goal="Create a person node",
            intent="Create a person entity",
            complexity=GoalComplexity.SIMPLE,
            entities=[],
            constraints=[],
            domain_hints=[],
            estimated_steps=1,
            requires_human_input=False,
            priority="medium",
            confidence=0.9,
            parsing_notes=["Test goal"]
        )
        
        print("✅ Valid GoalSpec created successfully")
        print(f"   Intent: {valid_goal.intent}")
        print(f"   Complexity: {valid_goal.complexity}")
        print(f"   Is simple: {valid_goal.is_simple_goal()}")
        print(f"   Requires graph ops: {valid_goal.requires_graph_operations()}")
        
        # Test schema validation
        goal_dict = valid_goal.model_dump()
        reconstructed = GoalSpec(**goal_dict)
        
        print("✅ GoalSpec serialization/deserialization works")
        
        return True
        
    except Exception as e:
        print(f"❌ GoalSpec validation failed: {e}")
        return False


async def main():
    """Main test function."""
    print("🚀 Starting parse_goal implementation tests...\n")
    
    # Test 1: Schema validation
    schema_test_passed = await test_goal_schema_validation()
    
    # Test 2: LLM integration (only if API key is available)
    llm_test_passed = await test_parse_goal_implementation()
    
    print(f"\n📊 Test Results:")
    print(f"   Schema validation: {'✅ PASSED' if schema_test_passed else '❌ FAILED'}")
    print(f"   LLM integration: {'✅ PASSED' if llm_test_passed else '❌ FAILED'}")
    
    if schema_test_passed and llm_test_passed:
        print("\n🎉 All tests passed! parse_goal implementation is working correctly.")
        return True
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    asyncio.run(main())
