#!/usr/bin/env python3
"""
Test script to verify the bug fix workflow works properly.
"""

import os
from groq_agent.config import ConfigurationManager
from groq_agent.api_client import GroqAPIClient
from groq_agent.intelligent_agent import IntelligentAgent


def create_test_files():
    """Create test files to simulate the bug."""
    
    # Create a simple task management system
    task_code = '''// Simple task management
function addTask(task) {
    // This function adds a task but doesn't filter by employee
    return firestore.collection('tasks').add(task);
}

function getTasks() {
    // This function gets all tasks without filtering by employee
    return firestore.collection('tasks').get();
}
'''
    
    with open("taskManager.js", "w") as f:
        f.write(task_code)
    
    print("✅ Created test files: taskManager.js")


def test_bug_fix_workflow():
    """Test the bug fix workflow."""
    
    print("🐛 Testing Bug Fix Workflow")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ Please set GROQ_API_KEY environment variable")
        return
    
    # Create test files
    create_test_files()
    
    try:
        # Initialize components
        config = ConfigurationManager()
        api_client = GroqAPIClient(config)
        agent = IntelligentAgent(config, api_client)
        
        print("✅ Agent initialized successfully")
        
        # Test with a simple bug report
        test_query = "Fix the bug where getTasks() doesn't filter by employee"
        
        print(f"\n📝 Test Query: {test_query}")
        print("\n🤖 Processing... (should show preview with confirmation options)")
        
        # Process request
        response = agent.process_request(test_query)
        
        print("\n📋 Final Response:")
        print(response)
        
        print("\n✅ Test completed!")
        print("🎯 Expected behavior:")
        print("  ✅ Should show preview of changes")
        print("  ✅ Should ask for confirmation")
        print("  ✅ Should show green (+) and red (-) lines")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        try:
            os.remove("taskManager.js")
            print("🧹 Cleaned up taskManager.js")
        except OSError:
            pass


if __name__ == "__main__":
    test_bug_fix_workflow()


