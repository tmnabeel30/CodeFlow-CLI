#!/usr/bin/env python3
"""
Test script for the Intelligent Groq CLI Agent.

This script demonstrates the intelligent agent's ability to:
1. Read and understand the entire codebase
2. Identify bugs and issues
3. Apply fixes automatically
4. Modify multiple files as needed
"""

import os
from groq_agent.config import ConfigurationManager
from groq_agent.api_client import GroqAPIClient
from groq_agent.intelligent_agent import IntelligentAgent


def test_intelligent_agent():
    """Test the intelligent agent capabilities."""
    
    print("🧠 Testing Intelligent Groq CLI Agent")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ Please set GROQ_API_KEY environment variable")
        print("export GROQ_API_KEY='your-api-key-here'")
        return
    
    try:
        # Initialize components
        config = ConfigurationManager()
        api_client = GroqAPIClient(config)
        
        # Create intelligent agent
        agent = IntelligentAgent(config, api_client)
        
        print("\n✅ Intelligent agent initialized successfully!")
        print(f"📁 Workspace: {agent.workspace_path}")
        print(f"📄 Files found: {len(agent.accessible_files)}")
        print(f"🧠 Project type: {agent.project_structure['type']}")
        
        # Show project structure
        print("\n📊 Project Structure:")
        print(f"• Main files: {len(agent.project_structure['main_files'])}")
        print(f"• Config files: {len(agent.project_structure['config_files'])}")
        print(f"• Source files: {len(agent.project_structure['source_files'])}")
        print(f"• Test files: {len(agent.project_structure['test_files'])}")
        
        # Test intelligent processing
        print("\n🧠 Testing intelligent processing...")
        
        # Test with a sample query
        test_query = "there is bug when A employer adds task for employee it doesn't show in the task page of employee who's is it assigned"
        
        print(f"\n📝 Test Query: {test_query}")
        print("\n🤖 Processing with intelligent agent...")
        
        # Process the request
        response = agent.process_request(test_query)
        
        print("\n📋 Response:")
        print(response)
        
        print("\n🎯 Intelligent Agent Features:")
        print("✅ Automatic file scanning and analysis")
        print("✅ Intelligent context building")
        print("✅ Bug identification and analysis")
        print("✅ Automatic file modifications")
        print("✅ Multi-file changes support")
        print("✅ Project structure understanding")
        
        print("\n🚀 To start the intelligent agent, run:")
        print("groq-agent")
        
        print("\n💡 The agent will now:")
        print("• Read all your files automatically")
        print("• Understand your project structure")
        print("• Identify relevant files for your queries")
        print("• Apply fixes and modifications automatically")
        print("• Handle complex multi-file changes")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_intelligent_agent()



