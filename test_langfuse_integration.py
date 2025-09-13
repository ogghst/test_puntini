#!/usr/bin/env python3
"""Test script for Langfuse integration with actual credentials."""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from puntini.settings import Settings
from puntini.observability.tracer_factory import make_tracer, TracerConfig


def test_langfuse_with_real_credentials():
    """Test Langfuse integration with real credentials from config.json."""
    print("Testing Langfuse integration with real credentials...")
    
    try:
        # Load settings from config.json
        settings = Settings("config.json")
        print("✓ Settings loaded from config.json")
        
        # Show configuration
        tracer_config = settings.get_tracer_config()
        langfuse_config = tracer_config["langfuse"]
        print(f"✓ Langfuse configuration:")
        print(f"  - Host: {langfuse_config['host']}")
        print(f"  - Public Key: {langfuse_config['public_key'][:20]}...")
        print(f"  - Debug: {langfuse_config['debug']}")
        print(f"  - Environment: {langfuse_config['environment']}")
        print(f"  - Release: {langfuse_config['release']}")
        
        # Create tracer using settings
        tracer_cfg = TracerConfig("langfuse")
        tracer = make_tracer(tracer_cfg, settings)
        print("✓ LangfuseTracer created using settings")
        
        # Test trace creation with real Langfuse
        with tracer.start_trace("test-real-langfuse-integration") as trace:
            print("✓ Trace started with real Langfuse")
            
            # Test span creation
            with tracer.start_span("test-span") as span:
                print("✓ Span created successfully")
                
                # Test logging
                tracer.log_io(
                    {"test": "input", "timestamp": "2025-01-13"},
                    {"test": "output", "status": "success"}
                )
                print("✓ I/O logging successful")
                
                tracer.log_decision(
                    "test_decision", 
                    {"context": "integration_test", "confidence": 0.95}
                )
                print("✓ Decision logging successful")
                
                # Test span-level logging
                span.log_io(
                    {"span_input": "test_data"},
                    {"span_output": "processed_data"}
                )
                print("✓ Span I/O logging successful")
                
                span.log_decision(
                    "span_decision",
                    {"span_context": "test_context"}
                )
                print("✓ Span decision logging successful")
        
        print("✓ Trace completed successfully")
        
        # Test flush
        tracer.flush()
        print("✓ Flush completed successfully")
        
        print("\n🎉 Langfuse integration test passed! Check your Langfuse dashboard for the trace.")
        
    except ImportError as e:
        print(f"⚠️  Langfuse not installed: {e}")
        print("Install it with: pip install langfuse>=3.0.0")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_langfuse_with_real_credentials()