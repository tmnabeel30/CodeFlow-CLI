#!/usr/bin/env python3
"""
Test script for the enhanced diff functionality.

This script demonstrates how the intelligent agent shows:
1. Green (+) lines for added code
2. Red (-) lines for removed code
3. Detailed diff output for all changes
4. Summary statistics
"""

import os
import tempfile
from pathlib import Path
from groq_agent.config import ConfigurationManager
from groq_agent.api_client import GroqAPIClient
from groq_agent.intelligent_agent import IntelligentAgent


def create_test_files():
    """Create test files to demonstrate diff functionality."""
    
    # Create a simple Python file with a bug
    python_code = '''def add_task(employer_id, employee_id, task_description):
    """Add a task for an employee."""
    # Bug: task is not being saved to the database
    task = {
        "employer_id": employer_id,
        "employee_id": employee_id,
        "description": task_description,
        "status": "pending"
    }
    
    # Missing: database.save(task)
    print("Task created but not saved!")
    return task

def get_employee_tasks(employee_id):
    """Get tasks for an employee."""
    # This will return empty because tasks are not saved
    return []
'''
    
    # Create test files
    with open("task_manager.py", "w") as f:
        f.write(python_code)
    
    with open("database.py", "w") as f:
        f.write("# Database module\n\nclass Database:\n    pass\n")
    
    print("✅ Created test files: task_manager.py, database.py")


def test_diff_functionality():
    """Test the enhanced diff functionality."""
    
    print("🎨 Testing Enhanced Diff Functionality")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ Please set GROQ_API_KEY environment variable")
        print("export GROQ_API_KEY='your-api-key-here'")
        return
    
    # Create test files
    create_test_files()
    
    try:
        # Initialize components
        config = ConfigurationManager()
        api_client = GroqAPIClient(config)
        
        # Create intelligent agent
        agent = IntelligentAgent(config, api_client)
        
        print("\n✅ Intelligent agent initialized successfully!")
        print(f"📁 Workspace: {agent.workspace_path}")
        print(f"📄 Files found: {len(agent.accessible_files)}")
        
        # Test with a bug fix request
        print("\n🧠 Testing bug fix with diff output...")
        
        test_query = "Fix the bug where tasks are not being saved to the database when an employer adds a task for an employee"
        
        print(f"\n📝 Test Query: {test_query}")
        print("\n🤖 Processing with intelligent agent...")
        print("(This will show green + for added lines and red - for removed lines)")
        
        # Process the request
        response = agent.process_request(test_query)
        
        print("\n📋 Response:")
        print(response)
        
        print("\n🎨 Enhanced Diff Features:")
        print("✅ Green (+) lines for added code")
        print("✅ Red (-) lines for removed code")
        print("✅ Blue (@) lines for diff headers")
        print("✅ Detailed file-by-file diff output")
        print("✅ Summary statistics table")
        print("✅ Change statistics panel")
        
        print("\n🚀 To test the enhanced diff functionality:")
        print("groq-agent")
        print("Then describe any bug or feature request!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test files
        for file in ["task_manager.py", "database.py"]:
            try:
                os.remove(file)
                print(f"🧹 Cleaned up {file}")
            except OSError:
                pass


if __name__ == "__main__":
    test_diff_functionality()



