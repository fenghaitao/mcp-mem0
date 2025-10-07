#!/usr/bin/env python3
"""
Test MCP Server using the official MCP client library
"""
import asyncio
import os
import subprocess
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def test_mcp_server_with_client():
    """Test the MCP server using the official MCP client"""
    print("🧪 Testing MCP Mem0 Server with Official Client")
    print("=" * 60)
    
    # Set up server parameters
    server_params = StdioServerParameters(
        command=".venv/bin/python3",
        args=["./src/main.py"],
        env={"TRANSPORT": "stdio"}
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Connected to MCP server")
                
                # Initialize the session
                await session.initialize()
                print("✅ Session initialized")
                
                # Test 1: List tools
                print("\n1. Listing tools...")
                tools = await session.list_tools()
                print(f"✅ Found {len(tools.tools)} tools:")
                for tool in tools.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
                # Test 2: Call save_memory tool
                print("\n2. Testing save_memory tool...")
                try:
                    result = await session.call_tool(
                        "save_memory",
                        {"text": "User loves working with GitHub Copilot and MCP servers"}
                    )
                    print(f"✅ Save memory result: {result.content}")
                except Exception as e:
                    print(f"❌ Save memory failed: {e}")
                
                # Test 3: Call search_memories tool
                print("\n3. Testing search_memories tool...")
                try:
                    result = await session.call_tool(
                        "search_memories",
                        {"query": "GitHub Copilot", "limit": 2}
                    )
                    print(f"✅ Search memories result: {result.content}")
                except Exception as e:
                    print(f"❌ Search memories failed: {e}")
                
                # Test 4: Call get_all_memories tool
                print("\n4. Testing get_all_memories tool...")
                try:
                    result = await session.call_tool(
                        "get_all_memories",
                        {}
                    )
                    print(f"✅ Get all memories result: {result.content}")
                except Exception as e:
                    print(f"❌ Get all memories failed: {e}")
                    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("🏁 MCP Client Test completed!")

if __name__ == "__main__":
    asyncio.run(test_mcp_server_with_client())