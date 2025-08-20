#!/usr/bin/env python3
"""
Example demonstrating enhanced file analysis capabilities of Groq CLI Agent.

This script shows how the agent can read, analyze, and work with file contents.
"""

import os
import tempfile
from groq_agent.config import ConfigurationManager
from groq_agent.api_client import GroqAPIClient
from groq_agent.file_operations import FileOperations


def create_sample_files():
    """Create sample files for demonstration."""
    
    # Sample Python file with some issues
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
    
    # Sample JavaScript file
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
    
    # Create temporary files
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(python_code)
        python_file = f.name
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
        f.write(js_code)
        js_file = f.name
    
    return python_file, js_file


def demonstrate_file_analysis():
    """Demonstrate file analysis capabilities."""
    
    print("=== Groq CLI Agent - Enhanced File Analysis Demo ===\n")
    
    # Check API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Please set GROQ_API_KEY environment variable")
        print("export GROQ_API_KEY='your-api-key-here'")
        return
    
    # Initialize components
    config = ConfigurationManager()
    api_client = GroqAPIClient(config)
    file_ops = FileOperations(api_client)
    
    # Create sample files
    python_file, js_file = create_sample_files()
    
    try:
        print("1. Comprehensive Analysis of Python File")
        print("=" * 50)
        print(f"Analyzing: {python_file}")
        print()
        
        # Analyze Python file comprehensively
        success = file_ops.analyze_file(python_file, "llama-2-70B", "comprehensive")
        
        if success:
            print("\n✅ Analysis completed successfully!")
        else:
            print("\n❌ Analysis failed!")
        
        print("\n" + "=" * 50)
        print("2. Security Analysis of JavaScript File")
        print("=" * 50)
        print(f"Analyzing: {js_file}")
        print()
        
        # Analyze JavaScript file for security
        success = file_ops.analyze_file(js_file, "llama-2-70B", "security")
        
        if success:
            print("\n✅ Security analysis completed successfully!")
        else:
            print("\n❌ Security analysis failed!")
        
        print("\n" + "=" * 50)
        print("3. Performance Analysis of Python File")
        print("=" * 50)
        print(f"Analyzing: {python_file}")
        print()
        
        # Analyze Python file for performance
        success = file_ops.analyze_file(python_file, "llama-2-70B", "performance")
        
        if success:
            print("\n✅ Performance analysis completed successfully!")
        else:
            print("\n❌ Performance analysis failed!")
        
        print("\n" + "=" * 50)
        print("4. File Review with Improvements")
        print("=" * 50)
        print(f"Reviewing: {python_file}")
        print()
        
        # Review and suggest improvements
        success = file_ops.review_file(python_file, "llama-2-70B", auto_apply=False)
        
        if success:
            print("\n✅ File review completed successfully!")
        else:
            print("\n❌ File review failed!")
        
        print("\n" + "=" * 50)
        print("5. CLI Commands to Try")
        print("=" * 50)
        print("You can also use these CLI commands:")
        print()
        print(f"# Analyze files")
        print(f"groq-agent analyze {python_file}")
        print(f"groq-agent analyze {js_file} --type security")
        print(f"groq-agent analyze {python_file} --type performance")
        print()
        print(f"# Review and suggest improvements")
        print(f"groq-agent review {python_file}")
        print(f"groq-agent review {js_file} --improvement security")
        print(f"groq-agent review {python_file} --improvement performance")
        print()
        print(f"# Interactive chat with file context")
        print(f"groq-agent")
        print(f"# Then in chat: /file load {python_file}")
        print(f"# Then ask: 'What are the main issues with this code?'")
        
    finally:
        # Clean up temporary files
        try:
            os.unlink(python_file)
            os.unlink(js_file)
            print(f"\n🧹 Cleaned up temporary files")
        except OSError:
            pass
    
    print("\n=== Demo completed ===")
    print("\nKey Features Demonstrated:")
    print("✅ Complete file content reading and analysis")
    print("✅ File metadata extraction (size, lines, permissions)")
    print("✅ Multiple analysis types (comprehensive, security, performance)")
    print("✅ Context-aware AI responses")
    print("✅ Interactive file review with diff")
    print("✅ File context in chat sessions")


if __name__ == "__main__":
    demonstrate_file_analysis()


