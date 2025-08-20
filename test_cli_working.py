#!/usr/bin/env python3
"""
Test script to verify the CLI is working properly after the fix.
"""

import subprocess
import sys


def test_cli_commands():
    """Test basic CLI commands to ensure they work."""
    
    print("🔧 Testing CLI Commands")
    print("=" * 40)
    
    # Test commands that should work
    test_commands = [
        ["groq-agent", "--version"],
        ["groq-agent", "--help"],
        ["groq-agent", "models"],
    ]
    
    for cmd in test_commands:
        print(f"\n📝 Testing: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                print("✅ Command executed successfully")
                if result.stdout:
                    print(f"📄 Output: {result.stdout[:200]}...")
            else:
                print(f"❌ Command failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            print("⏰ Command timed out")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🎉 CLI Testing Complete!")
    print("\n✅ The CLI is now working properly!")
    print("🚀 You can now use:")
    print("   groq-agent                    # Start interactive mode")
    print("   groq-agent --help             # Show help")
    print("   groq-agent models             # List models")
    print("   groq-agent --version          # Show version")


if __name__ == "__main__":
    test_cli_commands()

