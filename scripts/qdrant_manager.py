#!/usr/bin/env python3
"""
Qdrant Database Management Script for MCP-Mem0

This script provides utilities to manage Qdrant collections for the Mem0 MCP server.
Similar functionality to Supabase management but for Qdrant Cloud.

Usage:
    python qdrant_manager.py --help
    python qdrant_manager.py create-collection
    python qdrant_manager.py list-collections
    python qdrant_manager.py delete-collection --collection-name mem0_memories
    python qdrant_manager.py collection-info --collection-name mem0_memories
    python qdrant_manager.py count-vectors --collection-name mem0_memories
    python qdrant_manager.py clear-collection --collection-name mem0_memories
    python qdrant_manager.py get-all-memories --format json
    python qdrant_manager.py test-connection
"""

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http import models
import json

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent / "src"))

def load_env_config():
    """Load environment configuration from .env file."""
    # Try to load from multiple possible locations
    env_paths = [
        Path(__file__).parent.parent / ".env",
        Path(__file__).parent.parent.parent / ".env",
        Path.cwd() / ".env"
    ]
    
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path, override=True)
            print(f"Loaded environment from: {env_path}")
            break
    else:
        print("Warning: No .env file found")
    
    return {
        'url': os.getenv('QDRANT_URL'),
        'api_key': os.getenv('QDRANT_API_KEY'),
        'collection_name': os.getenv('QDRANT_COLLECTION_NAME', 'mem0_memories'),
        'embedding_dims': int(os.getenv('EMBEDDING_DIMS', '1536')),  # Default for OpenAI/GitHub Copilot
        'llm_provider': os.getenv('LLM_PROVIDER', 'github_copilot')
    }

def get_qdrant_client(config):
    """Create and return a Qdrant client."""
    if not config['url'] or not config['api_key']:
        raise ValueError("QDRANT_URL and QDRANT_API_KEY must be set in environment")
    
    return QdrantClient(
        url=config['url'],
        api_key=config['api_key']
    )

def get_embedding_dimensions(llm_provider):
    """Get the correct embedding dimensions based on LLM provider."""
    if llm_provider in ['openai', 'github_copilot']:
        return 1536  # text-embedding-3-small/large
    elif llm_provider == 'ollama':
        return 768   # nomic-embed-text
    else:
        return 1536  # default

def create_collection(args):
    """Create a new Qdrant collection for Mem0."""
    config = load_env_config()
    client = get_qdrant_client(config)
    
    collection_name = args.collection_name or config['collection_name']
    embedding_dims = get_embedding_dimensions(config['llm_provider'])
    
    try:
        # Check if collection already exists
        collections = client.get_collections().collections
        existing = [c for c in collections if c.name == collection_name]
        
        if existing:
            if not args.force:
                print(f"Collection '{collection_name}' already exists. Use --force to recreate.")
                return
            else:
                print(f"Deleting existing collection '{collection_name}'...")
                client.delete_collection(collection_name)
        
        print(f"Creating collection '{collection_name}' with {embedding_dims} dimensions...")
        
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=embedding_dims,
                distance=Distance.COSINE
            )
        )
        
        print(f"✅ Collection '{collection_name}' created successfully!")
        print(f"   - Dimensions: {embedding_dims}")
        print(f"   - Distance: COSINE")
        print(f"   - Provider: {config['llm_provider']}")
        
    except Exception as e:
        print(f"❌ Error creating collection: {e}")

def list_collections(args):
    """List all collections in the Qdrant instance."""
    config = load_env_config()
    client = get_qdrant_client(config)
    
    try:
        collections = client.get_collections()
        
        if not collections.collections:
            print("No collections found.")
            return
        
        print("Available collections:")
        print("-" * 50)
        for collection in collections.collections:
            info = client.get_collection(collection.name)
            print(f"📁 {collection.name}")
            print(f"   - Vectors: {info.points_count}")
            print(f"   - Status: {info.status}")
            if hasattr(info.config, 'params') and hasattr(info.config.params, 'vectors'):
                vectors_config = info.config.params.vectors
                if hasattr(vectors_config, 'size'):
                    print(f"   - Dimensions: {vectors_config.size}")
                    print(f"   - Distance: {vectors_config.distance}")
            print()
            
    except Exception as e:
        print(f"❌ Error listing collections: {e}")

def delete_collection(args):
    """Delete a Qdrant collection."""
    if not args.collection_name:
        print("❌ Collection name is required for deletion")
        return
    
    config = load_env_config()
    client = get_qdrant_client(config)
    
    if not args.force:
        confirm = input(f"Are you sure you want to delete collection '{args.collection_name}'? (y/N): ")
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return
    
    try:
        client.delete_collection(args.collection_name)
        print(f"✅ Collection '{args.collection_name}' deleted successfully!")
        
    except Exception as e:
        print(f"❌ Error deleting collection: {e}")

def collection_info(args):
    """Get detailed information about a specific collection."""
    collection_name = args.collection_name or load_env_config()['collection_name']
    config = load_env_config()
    client = get_qdrant_client(config)
    
    try:
        info = client.get_collection(collection_name)
        
        print(f"Collection Information: {collection_name}")
        print("=" * 50)
        print(f"Status: {info.status}")
        print(f"Points Count: {info.points_count}")
        print(f"Indexed Vectors Count: {info.indexed_vectors_count}")
        
        if hasattr(info.config, 'params') and hasattr(info.config.params, 'vectors'):
            vectors_config = info.config.params.vectors
            print(f"Vector Size: {vectors_config.size}")
            print(f"Distance Function: {vectors_config.distance}")
        
        if hasattr(info, 'payload_schema') and info.payload_schema:
            try:
                # Convert payload schema to dict for JSON serialization
                schema_dict = {}
                for key, value in info.payload_schema.items():
                    schema_dict[key] = str(value)
                print(f"Payload Schema: {json.dumps(schema_dict, indent=2)}")
            except Exception as e:
                print(f"Payload Schema: {info.payload_schema} (raw format)")
            
    except Exception as e:
        print(f"❌ Error getting collection info: {e}")

def count_vectors(args):
    """Count vectors in a collection."""
    collection_name = args.collection_name or load_env_config()['collection_name']
    config = load_env_config()
    client = get_qdrant_client(config)
    
    try:
        result = client.count(collection_name)
        print(f"Collection '{collection_name}' contains {result.count} vectors")
        
    except Exception as e:
        print(f"❌ Error counting vectors: {e}")

def clear_collection(args):
    """Clear all vectors from a collection without deleting the collection."""
    collection_name = args.collection_name or load_env_config()['collection_name']
    config = load_env_config()
    client = get_qdrant_client(config)
    
    if not args.force:
        confirm = input(f"Are you sure you want to clear all vectors from '{collection_name}'? (y/N): ")
        if confirm.lower() != 'y':
            print("Operation cancelled.")
            return
    
    try:
        # Get all point IDs and delete them
        points = client.scroll(collection_name, limit=10000)[0]  # Get first 10k points
        if points:
            point_ids = [point.id for point in points]
            client.delete(collection_name, point_ids)
            print(f"✅ Cleared {len(point_ids)} vectors from collection '{collection_name}'")
        else:
            print(f"Collection '{collection_name}' is already empty")
            
    except Exception as e:
        print(f"❌ Error clearing collection: {e}")

def get_all_memories(args):
    """Get all stored memories from mem0.
    
    This function retrieves all memories for the default user and displays them
    in JSON format. It uses the mem0 client configured with Qdrant backend.
    """
    config = load_env_config()
    
    # Import here to avoid circular imports
    try:
        from utils import get_mem0_client
    except ImportError:
        print("❌ Error: Could not import utils module. Make sure you're running from the correct directory.")
        return
    
    # Default user ID for memory operations (same as main.py)
    DEFAULT_USER_ID = "user"
    
    print("Retrieving all memories from mem0...")
    print(f"Collection: {config['collection_name']}")
    print(f"LLM Provider: {config['llm_provider']}")
    
    try:
        # Create mem0 client using the same configuration as main.py
        mem0_client = get_mem0_client()
        
        # Get all memories for the default user
        memories = mem0_client.get_all(user_id=DEFAULT_USER_ID)
        
        # Process the memories - handle both response formats
        if isinstance(memories, dict) and "results" in memories:
            memories_list = memories["results"]
        elif isinstance(memories, list):
            memories_list = memories
        else:
            memories_list = []
            
        print(f"✅ Retrieved {len(memories_list)} memories")
        
        if args.format == 'json':
            # For JSON format, extract just the memory content like main.py
            flattened_memories = []
            for memory in memories_list:
                if isinstance(memory, dict) and "memory" in memory:
                    flattened_memories.append(memory["memory"])
                else:
                    flattened_memories.append(str(memory))
            
            print("\nMemories (JSON format):")
            print(json.dumps(flattened_memories, indent=2))
        else:
            # For list format, show detailed information like mem0_memory_manager.py
            print("\nMemories:")
            for i, memory in enumerate(memories_list, 1):
                if isinstance(memory, dict):
                    print(f"{i}. ID: {memory.get('id', 'unknown')}")
                    print(f"   Memory: {memory.get('memory', 'N/A')}")
                    print(f"   User ID: {memory.get('user_id', 'N/A')}")
                    print(f"   Agent ID: {memory.get('agent_id', 'N/A')}")
                    print(f"   Created: {memory.get('created_at', 'N/A')}")
                    print()
                else:
                    print(f"{i}. {memory}")
        
        # Also show count information
        if isinstance(memories, dict):
            print(f"\nTotal memories in response: {len(memories.get('results', []))}")
            if 'pagination' in memories:
                pagination = memories['pagination']
                print(f"Pagination info: {pagination}")
        
    except Exception as e:
        print(f"❌ Error retrieving memories: {e}")

def test_connection(args):
    """Test connection to Qdrant and display cluster info."""
    config = load_env_config()
    
    print("Testing Qdrant connection...")
    print(f"URL: {config['url']}")
    print(f"Collection: {config['collection_name']}")
    print(f"LLM Provider: {config['llm_provider']}")
    
    try:
        client = get_qdrant_client(config)
        
        # Test basic connectivity
        collections = client.get_collections()
        print("✅ Connection successful!")
        print(f"Available collections: {len(collections.collections)}")
        
        # Try to get cluster info if available
        try:
            cluster_info = client.get_cluster_info()
            print(f"Cluster status: {cluster_info}")
        except:
            print("Cluster info not available (this is normal for cloud instances)")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Qdrant Database Management for MCP-Mem0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create collection
    create_parser = subparsers.add_parser('create-collection', help='Create a new collection')
    create_parser.add_argument('--collection-name', help='Collection name (default from env)')
    create_parser.add_argument('--force', action='store_true', help='Force recreate if exists')
    
    # List collections
    subparsers.add_parser('list-collections', help='List all collections')
    
    # Delete collection
    delete_parser = subparsers.add_parser('delete-collection', help='Delete a collection')
    delete_parser.add_argument('--collection-name', required=True, help='Collection name to delete')
    delete_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    # Collection info
    info_parser = subparsers.add_parser('collection-info', help='Get collection information')
    info_parser.add_argument('--collection-name', help='Collection name (default from env)')
    
    # Count vectors
    count_parser = subparsers.add_parser('count-vectors', help='Count vectors in collection')
    count_parser.add_argument('--collection-name', help='Collection name (default from env)')
    
    # Clear collection
    clear_parser = subparsers.add_parser('clear-collection', help='Clear all vectors from collection')
    clear_parser.add_argument('--collection-name', help='Collection name (default from env)')
    clear_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    # Get all memories
    memories_parser = subparsers.add_parser('get-all-memories', help='Get all stored memories from mem0')
    memories_parser.add_argument('--format', choices=['json', 'list'], default='list', 
                                help='Output format (default: list)')
    
    # Test connection
    subparsers.add_parser('test-connection', help='Test Qdrant connection')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Map commands to functions
    commands = {
        'create-collection': create_collection,
        'list-collections': list_collections,
        'delete-collection': delete_collection,
        'collection-info': collection_info,
        'count-vectors': count_vectors,
        'clear-collection': clear_collection,
        'get-all-memories': get_all_memories,
        'test-connection': test_connection,
    }
    
    commands[args.command](args)

if __name__ == "__main__":
    main()