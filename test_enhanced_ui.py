#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced UI.
"""

import os
from groq_agent.config import ConfigurationManager
from groq_agent.api_client import GroqAPIClient
from groq_agent.intelligent_agent import IntelligentAgent


def test_enhanced_ui():
    """Test the enhanced UI features."""
    
    print("🎨 Testing Enhanced UI")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ Please set GROQ_API_KEY environment variable")
        return
    
    try:
        # Initialize components
        config = ConfigurationManager()
        api_client = GroqAPIClient(config)
        agent = IntelligentAgent(config, api_client)
        
        print("✅ Agent initialized successfully")
        
        # Test the enhanced welcome message
        print("\n🎨 Testing Enhanced Welcome Message:")
        agent._show_welcome()
        
        # Test help command
        print("\n🎨 Testing Help Command:")
        agent._show_help()
        
        # Test model info
        print("\n🎨 Testing Model Info:")
        agent._show_model_info()
        
        # Test status
        print("\n🎨 Testing Status:")
        agent._show_status()
        
        # Test file listing
        print("\n🎨 Testing Enhanced File Listing:")
        agent._list_files()
        
        # Test structure
        print("\n🎨 Testing Enhanced Structure:")
        agent._show_structure()
        
        print("\n✅ Enhanced UI Testing Complete!")
        print("🎯 New UI Features:")
        print("  ✅ Beautiful welcome message with panels")
        print("  ✅ Enhanced input prompts with styling")
        print("  ✅ Organized file listing by type")
        print("  ✅ Detailed project structure analysis")
        print("  ✅ Help system with commands")
        print("  ✅ Model information display")
        print("  ✅ Status overview")
        print("  ✅ Goodbye message")
        
        print("\n🚀 To see the full enhanced UI:")
        print("groq-agent")
        print("Then try: /help, /files, /structure, /model, /status")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_enhanced_ui()


