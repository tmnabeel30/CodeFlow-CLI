#!/usr/bin/env python3
"""
Test script for the new confirmation system.

This script demonstrates how the intelligent agent now:
1. Shows a preview of all proposed changes
2. Asks for user confirmation before applying changes
3. Allows reviewing changes file by file
4. Shows detailed diffs with green (+) and red (-) lines
"""

import os
import tempfile
from pathlib import Path
from groq_agent.config import ConfigurationManager
from groq_agent.api_client import GroqAPIClient
from groq_agent.intelligent_agent import IntelligentAgent


def create_test_files():
    """Create test files to demonstrate the confirmation system."""
    
    # Create a simple Python file with multiple issues
    python_code = '''def calculate_total(items):
    """Calculate total price of items."""
    total = 0
    for item in items:
        # Bug: not checking if item has price
        total += item['price']
    return total

def validate_user(user_data):
    """Validate user data."""
    # Missing validation
    return True

def save_to_database(data):
    """Save data to database."""
    # Missing database connection
    print("Data saved!")
'''
    
    # Create test files
    with open("calculator.py", "w") as f:
        f.write(python_code)
    
    with open("config.py", "w") as f:
        f.write("# Configuration file\n\nDEBUG = True\n")
    
    print("✅ Created test files: calculator.py, config.py")


def test_confirmation_system():
    """Test the new confirmation system."""
    
    print("🔐 Testing Confirmation System")
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
        
        # Test with a multi-file fix request
        print("\n🧠 Testing multi-file bug fix with confirmation...")
        
        test_query = "Fix the bugs in the calculator: add proper validation for item prices, add user validation, and implement proper database saving"
        
        print(f"\n📝 Test Query: {test_query}")
        print("\n🤖 Processing with intelligent agent...")
        print("(This will show preview and ask for confirmation)")
        
        # Process the request
        response = agent.process_request(test_query)
        
        print("\n📋 Response:")
        print(response)
        
        print("\n🔐 New Confirmation Features:")
        print("✅ Preview of all proposed changes")
        print("✅ Option to apply ALL changes at once")
        print("✅ Option to review and apply changes one by one")
        print("✅ Option to cancel all changes")
        print("✅ Detailed diff view for each file")
        print("✅ Green (+) lines for added code")
        print("✅ Red (-) lines for removed code")
        print("✅ File-by-file confirmation prompts")
        
        print("\n🚀 To test the confirmation system:")
        print("groq-agent")
        print("Then describe any bug or feature request!")
        print("You'll see:")
        print("1. Preview of all changes")
        print("2. Choose: Apply all / Review one by one / Cancel")
        print("3. For each file: see diff and confirm")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up test files
        for file in ["calculator.py", "config.py"]:
            try:
                os.remove(file)
                print(f"🧹 Cleaned up {file}")
            except OSError:
                pass


if __name__ == "__main__":
    test_confirmation_system()
