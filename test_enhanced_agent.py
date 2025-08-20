#!/usr/bin/env python3
"""
Test script for the enhanced Groq CLI Agent.

This script demonstrates the new features:
1. Better UI with rich formatting
2. Automatic file access
3. File modification capabilities
"""

import os
import tempfile
from pathlib import Path
from groq_agent.config import ConfigurationManager
from groq_agent.api_client import GroqAPIClient
from groq_agent.enhanced_chat import EnhancedChatSession


def create_test_files():
    """Create test files to demonstrate file access."""
    
    # Create a test Python file
    python_code = '''def calculate_fibonacci(n):
    """Calculate fibonacci number."""
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

def process_data(data):
    # Missing docstring
    result = []
    for item in data:
        if item > 0:  # No error handling
            result.append(item * 2)
    return result

class UserManager:
    def __init__(self):
        self.users = []
    
    def add_user(self, name, email):
        # No validation
        user = {"name": name, "email": email}
        self.users.append(user)
    
    def get_user(self, email):
        # Inefficient linear search
        for user in self.users:
            if user["email"] == email:
                return user
        return None

# Global variable without clear purpose
config = {}

if __name__ == "__main__":
    print("Hello World")
'''
    
    # Create a test JavaScript file
    js_code = '''function processUserData(userData) {
    // No input validation
    let result = [];
    
    for (let i = 0; i < userData.length; i++) {
        let user = userData[i];
        if (user.active) {
            result.push({
                name: user.name,
                email: user.email,
                id: user.id
            });
        }
    }
    
    return result;
}

class DataProcessor {
    constructor() {
        this.data = [];
    }
    
    addData(item) {
        // No validation
        this.data.push(item);
    }
    
    processData() {
        // Synchronous processing - could be async
        return this.data.map(item => item * 2);
    }
}

// Global variable
var globalConfig = {};

// Callback hell example
function fetchUserData(userId, callback) {
    fetch('/api/users/' + userId)
        .then(response => response.json())
        .then(data => {
            processUserData(data);
            callback(data);
        })
        .catch(error => {
            console.log('Error:', error);
        });
}
'''
    
    # Create test files in current directory
    with open("test_app.py", "w") as f:
        f.write(python_code)
    
    with open("test_app.js", "w") as f:
        f.write(js_code)
    
    with open("README.md", "w") as f:
        f.write("# Test Project\n\nThis is a test project to demonstrate the enhanced Groq CLI Agent.\n")
    
    print("✅ Created test files: test_app.py, test_app.js, README.md")


def test_enhanced_agent():
    """Test the enhanced agent features."""
    
    print("🚀 Testing Enhanced Groq CLI Agent")
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
        
        # Create enhanced chat session
        chat_session = EnhancedChatSession(config, api_client)
        
        print("\n✅ Enhanced agent initialized successfully!")
        print(f"📁 Workspace: {chat_session.workspace_path}")
        print(f"📄 Files found: {len(chat_session.accessible_files)}")
        
        # Show accessible files
        print("\n📁 Accessible files:")
        for i, file_path in enumerate(sorted(chat_session.accessible_files), 1):
            print(f"  {i}. {file_path}")
        
        print("\n🎯 Enhanced Features Available:")
        print("✅ Beautiful UI with rich formatting")
        print("✅ Automatic file scanning and access")
        print("✅ File reading and analysis")
        print("✅ File modification capabilities")
        print("✅ Workspace context awareness")
        
        print("\n🚀 To start the enhanced agent, run:")
        print("groq-agent")
        
        print("\n💡 Try these commands in the chat:")
        print("• /files - List all accessible files")
        print("• /read test_app.py - Read and analyze the Python file")
        print("• /edit test_app.py - Edit the Python file")
        print("• 'What are the issues in test_app.py?' - Ask about files")
        print("• 'Improve the performance of the fibonacci function' - Request improvements")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up test files
        for file in ["test_app.py", "test_app.js", "README.md"]:
            try:
                os.remove(file)
                print(f"🧹 Cleaned up {file}")
            except OSError:
                pass


if __name__ == "__main__":
    test_enhanced_agent()


