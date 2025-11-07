#!/usr/bin/env python3
"""
mem0 Memory Manager

A comprehensive tool for managing mem0 memories in your database.
Provides listing, filtering, cleanup, and maintenance operations.
Uses the mem0 API methods for safe memory operations.

Features:
    - List and filter memories by user, agent, or run
    - Delete specific memories or bulk operations
    - Interactive mode for guided operations
    - Complete database reset capabilities
    - Safe operations with confirmation prompts

Configuration:
    Create a .env file with DATABASE_URL or set it as an environment variable.
    Example .env:
        DATABASE_URL=postgresql://user:pass@host:port/db

Usage:
    python scripts/mem0_memory_manager.py --help
    python scripts/mem0_memory_manager.py --interactive
    python scripts/mem0_memory_manager.py --list-all
    python scripts/mem0_memory_manager.py --delete-user-memories --user-id "user123"
    python scripts/mem0_memory_manager.py --delete-agent-memories --agent-id "agent456"
    python scripts/mem0_memory_manager.py --delete-memory --memory-id "mem789"
    python scripts/mem0_memory_manager.py --reset-all
"""

import argparse
import os
import sys
from typing import Optional
import json

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not found. Install with: pip install python-dotenv")
    print("   Continuing with system environment variables only...")
except Exception as e:
    print(f"⚠️  Could not load .env file: {e}")
    print("   Continuing with system environment variables only...")

try:
    from mem0 import Memory
except ImportError:
    print("❌ Error: mem0 package not found. Please install it first:")
    print("   pip install mem0ai")
    sys.exit(1)


def get_mem0_client():
    """Initialize mem0 client using the same approach as the MCP server"""
    # Get LLM provider and configuration
    llm_provider = os.getenv('LLM_PROVIDER')
    llm_api_key = os.getenv('LLM_API_KEY')
    llm_model = os.getenv('LLM_CHOICE')
    embedding_model = os.getenv('EMBEDDING_MODEL_CHOICE')
    
    # Initialize config dictionary
    config = {}
    
    # Configure LLM based on provider
    if llm_provider == 'openai' or llm_provider == 'openrouter':
        config["llm"] = {
            "provider": "openai",
            "config": {
                "model": llm_model,
                "temperature": 0.2,
                "max_tokens": 2000,
            }
        }
        
        # Set API key in environment if not already set
        if llm_api_key and not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = llm_api_key
            
        # For OpenRouter, set the specific API key
        if llm_provider == 'openrouter' and llm_api_key:
            os.environ["OPENROUTER_API_KEY"] = llm_api_key
    
    elif llm_provider == 'github_copilot':
        config["llm"] = {
            "provider": "litellm",
            "config": {
                "model": llm_model or "github_copilot/gpt-4o",
                "temperature": 0.2,
                "max_tokens": 2000,
            }
        }
    
    elif llm_provider == 'ollama':
        config["llm"] = {
            "provider": "ollama",
            "config": {
                "model": llm_model,
                "temperature": 0.2,
                "max_tokens": 2000,
            }
        }
        
        # Set base URL for Ollama if provided
        llm_base_url = os.getenv('LLM_BASE_URL')
        if llm_base_url:
            config["llm"]["config"]["ollama_base_url"] = llm_base_url
    
    # Configure embedder based on provider
    if llm_provider == 'openai':
        config["embedder"] = {
            "provider": "openai",
            "config": {
                "model": embedding_model or "text-embedding-3-small",
                "embedding_dims": 1536  # Default for text-embedding-3-small
            }
        }
        
        # Set API key in environment if not already set
        if llm_api_key and not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = llm_api_key
    
    elif llm_provider == 'github_copilot':
        config["embedder"] = {
            "provider": "github_copilot",
            "config": {
                "model": embedding_model or "github_copilot/text-embedding-3-small",
                "embedding_dims": 1536,  # Default for text-embedding-3-small
            }
        }
    
    elif llm_provider == 'ollama':
        config["embedder"] = {
            "provider": "ollama",
            "config": {
                "model": embedding_model or "nomic-embed-text",
                "embedding_dims": 768  # Default for nomic-embed-text
            }
        }
        
        # Set base URL for Ollama if provided
        embedding_base_url = os.getenv('LLM_BASE_URL')
        if embedding_base_url:
            config["embedder"]["config"]["ollama_base_url"] = embedding_base_url
    
    # Configure Supabase vector store
    embedding_dims = 1536  # Default
    if llm_provider == "openai" or llm_provider == "github_copilot":
        embedding_dims = 1536
    elif llm_provider == "ollama":
        embedding_dims = 768
    
    config["vector_store"] = {
        "provider": "supabase",
        "config": {
            "connection_string": os.environ.get('DATABASE_URL', ''),
            "collection_name": "mem0_memories",
            "embedding_model_dims": embedding_dims
        }
    }
    
    # Create and return the Memory client
    return Memory.from_config(config)


# Default user ID for memory operations (same as MCP server)
DEFAULT_USER_ID = "user"


class MemoryManager:
    def __init__(self, database_url: Optional[str] = None):
        """Initialize the Memory manager utility"""
        
        # Use provided database URL or environment variable
        if database_url:
            os.environ['DATABASE_URL'] = database_url
            print(f"🔗 Using provided database URL: {database_url[:50]}...")
        elif os.getenv('DATABASE_URL'):
            print(f"🔗 Using DATABASE_URL from environment: {os.getenv('DATABASE_URL')[:50]}...")
        else:
            print("⚠️  Warning: No DATABASE_URL found in .env or environment.")
        
        try:
            # Use the same initialization approach as the MCP server
            self.memory = get_mem0_client()
            print("✅ Connected to mem0 successfully")
            
            # Print configuration info
            llm_provider = os.getenv('LLM_PROVIDER', 'not set')
            llm_model = os.getenv('LLM_CHOICE', 'not set')
            print(f"🤖 LLM Provider: {llm_provider}")
            print(f"📝 LLM Model: {llm_model}")
            
        except Exception as e:
            print(f"❌ Failed to initialize mem0: {e}")
            print("💡 Check your .env file and ensure all required environment variables are set:")
            print("   - DATABASE_URL (required)")
            print("   - LLM_PROVIDER (openai, github_copilot, ollama)")
            print("   - LLM_CHOICE (model name)")
            print("   - LLM_API_KEY (if using OpenAI/OpenRouter)")
            print("   - EMBEDDING_MODEL_CHOICE (optional)")
            sys.exit(1)
    
    def list_memories(self, user_id: Optional[str] = None, agent_id: Optional[str] = None, 
                     run_id: Optional[str] = None) -> list:
        """List all memories with optional filtering"""
        try:
            # Use default user ID if none provided
            if not user_id and not agent_id and not run_id:
                user_id = DEFAULT_USER_ID
                print(f"🔍 Fetching memories for default user: {user_id}")
            else:
                print("🔍 Fetching memories...")
            
            memories = self.memory.get_all(user_id=user_id, agent_id=agent_id, run_id=run_id)
            
            # Handle different response formats
            if isinstance(memories, dict) and 'results' in memories:
                memories_list = memories['results']
            elif isinstance(memories, list):
                memories_list = memories
            else:
                memories_list = []
            
            print(f"📋 Found {len(memories_list)} memories")
            
            for i, memory in enumerate(memories_list, 1):
                print(f"   {i}. ID: {memory.get('id', 'unknown')}")
                print(f"      Memory: {memory.get('memory', 'N/A')[:100]}...")
                print(f"      User ID: {memory.get('user_id', 'N/A')}")
                print(f"      Agent ID: {memory.get('agent_id', 'N/A')}")
                print(f"      Created: {memory.get('created_at', 'N/A')}")
                print()
            
            return memories_list
            
        except Exception as e:
            print(f"❌ Error listing memories: {e}")
            return []
    
    def delete_memory_by_id(self, memory_id: str) -> bool:
        """Delete a specific memory by ID"""
        try:
            print(f"🗑️  Deleting memory with ID: {memory_id}")
            self.memory.delete(memory_id)
            print("✅ Memory deleted successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting memory {memory_id}: {e}")
            return False
    
    def delete_user_memories(self, user_id: str) -> bool:
        """Delete all memories for a specific user"""
        try:
            print(f"🗑️  Deleting all memories for user: {user_id}")
            self.memory.delete_all(user_id=user_id)
            print("✅ All user memories deleted successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting user memories: {e}")
            return False
    
    def delete_agent_memories(self, agent_id: str) -> bool:
        """Delete all memories for a specific agent"""
        try:
            print(f"🗑️  Deleting all memories for agent: {agent_id}")
            self.memory.delete_all(agent_id=agent_id)
            print("✅ All agent memories deleted successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting agent memories: {e}")
            return False
    
    def delete_run_memories(self, run_id: str) -> bool:
        """Delete all memories for a specific run"""
        try:
            print(f"🗑️  Deleting all memories for run: {run_id}")
            self.memory.delete_all(run_id=run_id)
            print("✅ All run memories deleted successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting run memories: {e}")
            return False
    
    
    def safe_delete_all_memories(self) -> bool:
        """Safely delete all memories without affecting database structure"""
        try:
            print("🗑️  Safely deleting all mem0 memories...")
            print("💡 This deletes memory data but preserves database structure")
            
            # Get all memories first to show what will be deleted
            all_memories = self.memory.get_all(user_id=DEFAULT_USER_ID)
            if isinstance(all_memories, dict) and 'results' in all_memories:
                memories_list = all_memories['results']
            else:
                memories_list = all_memories if isinstance(all_memories, list) else []
            
            if not memories_list:
                print("📭 No memories found to delete")
                return True
            
            print(f"📋 Found {len(memories_list)} memories to delete")
            confirmation = input("Type 'DELETE' to proceed: ")
            
            if confirmation != 'DELETE':
                print("❌ Operation cancelled")
                return False
            
            # Delete all memories individually (safer approach)
            deleted_count = 0
            for memory in memories_list:
                try:
                    memory_id = memory.get('id')
                    if memory_id:
                        self.memory.delete(memory_id)
                        deleted_count += 1
                except Exception as e:
                    print(f"⚠️  Could not delete memory {memory_id}: {e}")
            
            print(f"✅ Successfully deleted {deleted_count} memories")
            return True
            
        except Exception as e:
            print(f"❌ Error deleting memories: {e}")
            return False
    
    def interactive_mode(self):
        """Interactive memory management mode"""
        print("\n🧠 mem0 Interactive Memory Manager")
        print("=" * 50)
        
        while True:
            print("\nAvailable actions:")
            print("1. List all memories")
            print("2. List memories by user ID")
            print("3. List memories by agent ID")
            print("4. Delete specific memory by ID")
            print("5. Delete all memories for a user")
            print("6. Delete all memories for an agent")
            print("7. Delete all memories for a run")
            print("8. Safe delete all memories (recommended)")
            print("9. Exit")
            
            choice = input("\nEnter your choice (1-9): ").strip()
            
            if choice == '1':
                self.list_memories()
            elif choice == '2':
                user_id = input("Enter user ID: ").strip()
                if user_id:
                    self.list_memories(user_id=user_id)
            elif choice == '3':
                agent_id = input("Enter agent ID: ").strip()
                if agent_id:
                    self.list_memories(agent_id=agent_id)
            elif choice == '4':
                memory_id = input("Enter memory ID: ").strip()
                if memory_id:
                    self.delete_memory_by_id(memory_id)
            elif choice == '5':
                user_id = input("Enter user ID: ").strip()
                if user_id:
                    self.delete_user_memories(user_id)
            elif choice == '6':
                agent_id = input("Enter agent ID: ").strip()
                if agent_id:
                    self.delete_agent_memories(agent_id)
            elif choice == '7':
                run_id = input("Enter run ID: ").strip()
                if run_id:
                    self.delete_run_memories(run_id)
            elif choice == '8':
                self.safe_delete_all_memories()
            elif choice == '9':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")


def main():
    parser = argparse.ArgumentParser(
        description="mem0 Memory Manager - Comprehensive memory management tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --interactive
  %(prog)s --list-all
  %(prog)s --list-memories --user-id "user123"
  %(prog)s --delete-user-memories --user-id "user123"
  %(prog)s --delete-memory --memory-id "mem789"
  %(prog)s --reset-all
        """
    )
    
    # Database connection
    parser.add_argument('--database-url', type=str,
                       help='Database URL (defaults to DATABASE_URL env var)')
    
    # List operations
    parser.add_argument('--interactive', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--list-all', action='store_true',
                       help='List all memories')
    parser.add_argument('--list-memories', action='store_true',
                       help='List memories (can be filtered with --user-id, --agent-id, --run-id)')
    
    # Delete operations
    parser.add_argument('--delete-memory', action='store_true',
                       help='Delete a specific memory by ID (requires --memory-id)')
    parser.add_argument('--delete-user-memories', action='store_true',
                       help='Delete all memories for a user (requires --user-id)')
    parser.add_argument('--delete-agent-memories', action='store_true',
                       help='Delete all memories for an agent (requires --agent-id)')
    parser.add_argument('--delete-run-memories', action='store_true',
                       help='Delete all memories for a run (requires --run-id)')
    parser.add_argument('--safe-delete-all', action='store_true',
                       help='Safely delete all memories (preserves database structure)')
    
    # Filter parameters
    parser.add_argument('--user-id', type=str, help='User ID for filtering')
    parser.add_argument('--agent-id', type=str, help='Agent ID for filtering')
    parser.add_argument('--run-id', type=str, help='Run ID for filtering')
    parser.add_argument('--memory-id', type=str, help='Memory ID for deletion')
    
    args = parser.parse_args()
    
    # Initialize memory manager
    manager = MemoryManager(database_url=args.database_url)
    
    # Execute commands
    if args.interactive:
        manager.interactive_mode()
    elif args.list_all or args.list_memories:
        manager.list_memories(user_id=args.user_id, agent_id=args.agent_id, run_id=args.run_id)
    elif args.delete_memory:
        if not args.memory_id:
            print("❌ Error: --memory-id is required for --delete-memory")
            sys.exit(1)
        manager.delete_memory_by_id(args.memory_id)
    elif args.delete_user_memories:
        if not args.user_id:
            print("❌ Error: --user-id is required for --delete-user-memories")
            sys.exit(1)
        manager.delete_user_memories(args.user_id)
    elif args.delete_agent_memories:
        if not args.agent_id:
            print("❌ Error: --agent-id is required for --delete-agent-memories")
            sys.exit(1)
        manager.delete_agent_memories(args.agent_id)
    elif args.delete_run_memories:
        if not args.run_id:
            print("❌ Error: --run-id is required for --delete-run-memories")
            sys.exit(1)
        manager.delete_run_memories(args.run_id)
    elif args.safe_delete_all:
        manager.safe_delete_all_memories()
    else:
        print("🧠 mem0 Memory Manager")
        print("=" * 40)
        print("Use --help for usage information")
        print("Use --interactive for interactive mode")
        print("\nQuick examples:")
        print("  python scripts/mem0_memory_manager.py --interactive")
        print("  python scripts/mem0_memory_manager.py --list-all")
        print("  python scripts/mem0_memory_manager.py --safe-delete-all")


if __name__ == "__main__":
    main()