#!/usr/bin/env python3
"""
Simple test to validate mem0 configuration and GitHub Copilot integration
"""

import os
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import get_mem0_client

load_dotenv()

def test_mem0_config():
    """Test if mem0 client can be created with GitHub Copilot configuration"""
    print("🧪 Testing mem0 configuration with GitHub Copilot")
    print("=" * 60)
    
    try:
        # Test mem0 client creation
        print("1. Creating mem0 client...")
        mem0_client = get_mem0_client()
        print("✅ mem0 client created successfully!")
        
        # Test basic memory operations
        print("\n2. Testing memory save...")
        messages = [{"role": "user", "content": "This is a test memory for GitHub Copilot integration."}]
        result = mem0_client.add(messages, user_id="test_user")
        print(f"✅ Memory saved: {result}")
        
        print("\n3. Testing memory search...")
        search_result = mem0_client.search("GitHub Copilot", user_id="test_user", limit=1)
        print(f"✅ Search result: {search_result}")
        
        print("\n4. Testing get all memories...")
        all_memories = mem0_client.get_all(user_id="test_user")
        print(f"✅ All memories: {all_memories}")
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed! GitHub Copilot integration is working!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    # Show current configuration
    print("Current configuration:")
    print(f"LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
    print(f"LLM_CHOICE: {os.getenv('LLM_CHOICE')}")
    print(f"EMBEDDING_MODEL_CHOICE: {os.getenv('EMBEDDING_MODEL_CHOICE')}")
    print(f"DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')[:50]}...")
    print()
    
    test_mem0_config()