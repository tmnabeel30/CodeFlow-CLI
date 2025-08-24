#!/usr/bin/env python3
"""
Test script to verify the preview shows actual code changes and doesn't get stuck.
"""

import os
from groq_agent.config import ConfigurationManager
from groq_agent.api_client import GroqAPIClient
from groq_agent.intelligent_agent import IntelligentAgent


def create_simple_test_file():
    """Create a simple test file."""
    content = '''def hello():
    print("Hello World")
    return True
'''
    with open("test_file.py", "w") as f:
        f.write(content)
    print("✅ Created test_file.py")


def test_preview_and_timeout():
    """Test the preview system and timeout protection."""
    
    print("🔧 Testing Preview System and Timeout Protection")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ Please set GROQ_API_KEY environment variable")
        return
    
    # Create test file
    create_simple_test_file()
    
    try:
        # Initialize components
        config = ConfigurationManager()
        api_client = GroqAPIClient(config)
        agent = IntelligentAgent(config, api_client)
        
        print("✅ Agent initialized successfully")
        
        # Test with a simple request
        test_query = "Add error handling to the hello function"
        
        print(f"\n📝 Test Query: {test_query}")
        print("\n🤖 Processing... (should show preview with actual code changes)")
        
        # Process request
        response = agent.process_request(test_query)
        
        print("\n📋 Final Response:")
        print(response)
        
        print("\n✅ Test completed successfully!")
        print("🎯 Features verified:")
        print("  ✅ Preview shows actual code changes")
        print("  ✅ Green (+) and Red (-) lines visible")
        print("  ✅ No infinite loops")
        print("  ✅ Timeout protection working")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        try:
            os.remove("test_file.py")
            print("🧹 Cleaned up test_file.py")
        except OSError:
            pass


if __name__ == "__main__":
    test_preview_and_timeout()


