from mem0 import Memory
import os
import litellm

# Custom instructions for memory processing
# These aren't being used right now but Mem0 does support adding custom prompting
# for handling memory retrieval and processing.
CUSTOM_INSTRUCTIONS = """
Extract the Following Information:  

- Key Information: Identify and save the most important details.
- Context: Capture the surrounding context to understand the memory's relevance.
- Connections: Note any relationships to other topics or memories.
- Importance: Highlight why this information might be valuable in the future.
- Source: Record where this information came from when applicable.
"""

def get_mem0_client():
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
    
    # Configure vector store (Qdrant or Supabase)
    embedding_dims = 1536  # Default
    if llm_provider == "openai" or llm_provider == "github_copilot":
        embedding_dims = 1536
    elif llm_provider == "ollama":
        embedding_dims = 768
    
    # Check which vector store to use
    vector_store_provider = os.getenv('VECTOR_STORE_PROVIDER', 'supabase')
    
    if vector_store_provider == 'qdrant':
        # Configure Qdrant vector store
        config["vector_store"] = {
            "provider": "qdrant",
            "config": {
                "collection_name": os.getenv('QDRANT_COLLECTION_NAME', 'mem0_memories'),
                "embedding_model_dims": embedding_dims,
                "url": os.getenv('QDRANT_URL'),
                "api_key": os.getenv('QDRANT_API_KEY'),
            }
        }
    else:
        # Configure Supabase vector store (default)
        config["vector_store"] = {
            "provider": "supabase",
            "config": {
                "connection_string": os.environ.get('DATABASE_URL', ''),
                "collection_name": "mem0_memories",
                "embedding_model_dims": embedding_dims
            }
        }

    # config["custom_fact_extraction_prompt"] = CUSTOM_INSTRUCTIONS
    
    # Create and return the Memory client
    return Memory.from_config(config)