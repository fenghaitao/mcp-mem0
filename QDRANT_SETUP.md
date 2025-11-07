# Setting up mem0 with Qdrant Cloud

This guide will help you configure the mem0 MCP server to use Qdrant Cloud as the vector store instead of Supabase.

## Prerequisites

- A Qdrant Cloud account (https://cloud.qdrant.io/)
- Access to your Qdrant cluster

## Steps to Configure Qdrant Cloud

### 1. Get Your Qdrant Cluster Information

**Important**: You need the actual **Cluster API Endpoint**, NOT the dashboard URL!

#### Step 1: Navigate to Your Cluster
1. Go to https://cloud.qdrant.io/accounts/dbebec34-95a6-4947-b646-f1c589308988/clusters
2. You should see a list of your Qdrant clusters

#### Step 2: Click on Your Cluster
- Click on the cluster name or the "Open" button to view cluster details

#### Step 3: Find the API Endpoint
Once inside the cluster details page, look for:

**Option A: "Cluster URL" or "REST API URL"**
- Usually displayed prominently at the top of the cluster details
- Format: `https://<cluster-id>.<region>.aws.qdrant.io`
- Example: `https://abc123def-456.eu-central-1.aws.qdrant.io`

**Option B: "Access" or "Connection" Tab**
- Some versions show this in a dedicated "Access" or "Connection" section
- Look for "REST Endpoint" or "gRPC Endpoint"
- Use the **REST endpoint** (not gRPC)

**Option C: Look for API Information**
- There should be a section showing how to connect via API
- The endpoint will be in this format:
  - `https://<something>.qdrant.io` OR
  - `https://<something>.<region>.aws.qdrant.io` OR
  - `https://<something>.<region>.gcp.qdrant.io`

**Example of what you'll see:**
```
┌─────────────────────────────────────────┐
│  Cluster: my-cluster-name               │
├─────────────────────────────────────────┤
│  Cluster URL:                           │
│  https://xyz123.eu-central.aws.qdrant.io│  ← THIS IS WHAT YOU NEED!
│                                          │
│  API Key: [Show] [Copy]                 │  ← Click to reveal and copy
└─────────────────────────────────────────┘
```

#### Step 4: Get Your API Key
In the same cluster details page:

1. Look for "API Keys" or "Authentication" section
2. You might need to:
   - Click "Create API Key" if you don't have one
   - Or copy an existing API key
3. **Important**: Make sure the API key has read/write permissions

#### Common Mistakes to Avoid

❌ **Wrong**: Using the dashboard URL
```
QDRANT_URL=https://cloud.qdrant.io/accounts/.../clusters
```

✅ **Correct**: Using the cluster API endpoint
```
QDRANT_URL=https://abc123.eu-central-1.aws.qdrant.io
```

❌ **Wrong**: Including `/collections` or other paths
```
QDRANT_URL=https://abc123.eu-central-1.aws.qdrant.io/collections
```

✅ **Correct**: Just the base URL
```
QDRANT_URL=https://abc123.eu-central-1.aws.qdrant.io
```

### 2. Update Your `.env` File

Edit the `/nfs/site/disks/hfeng1_fw_01/simics-mcp-server/mcp-mem0/.env` file and update the following variables:

```bash
# Vector Store Configuration
VECTOR_STORE_PROVIDER=qdrant

# Qdrant Cloud Configuration
QDRANT_URL=https://your-cluster-id.your-region.aws.qdrant.io
QDRANT_API_KEY=your_api_key_here

# Optional: Change the collection name (defaults to mem0_memories)
QDRANT_COLLECTION_NAME=mem0_memories
```

### 3. Install Qdrant Client (if needed)

The mem0 library should already include the Qdrant client, but if you encounter issues, you can install it explicitly:

```bash
cd /nfs/site/disks/hfeng1_fw_01/simics-mcp-server/mcp-mem0
pip install qdrant-client
```

Or if using uv:

```bash
uv pip install qdrant-client
```

### 4. Verify the Configuration

The code has been updated in `src/utils.py` to support both Qdrant and Supabase vector stores. The system will automatically:
- Use Qdrant when `VECTOR_STORE_PROVIDER=qdrant`
- Fall back to Supabase when `VECTOR_STORE_PROVIDER=supabase` or when the variable is not set

### 5. Test the Connection

Start the mem0 MCP server to verify the Qdrant connection works:

```bash
cd /nfs/site/disks/hfeng1_fw_01/simics-mcp-server/mcp-mem0
# If using the startup script
./start_mcp_servers.sh

# Or run directly
python3 src/main.py
```

The server will automatically create the collection in Qdrant if it doesn't exist.

## Configuration Summary

Your `.env` file should have these key settings:

```bash
# LLM Configuration (existing)
LLM_PROVIDER=github_copilot
LLM_CHOICE=github_copilot/gpt-4o
EMBEDDING_MODEL_CHOICE=github_copilot/text-embedding-3-small

# Vector Store Configuration (new)
VECTOR_STORE_PROVIDER=qdrant
QDRANT_URL=<your-cluster-url>
QDRANT_API_KEY=<your-api-key>
QDRANT_COLLECTION_NAME=mem0_memories
```

## Switching Back to Supabase

If you need to switch back to Supabase:

```bash
VECTOR_STORE_PROVIDER=supabase
# DATABASE_URL remains configured
```

## Troubleshooting

### Quick Test: Verify Your Endpoint

Once you have the endpoint, test it with curl to make sure it's correct:

```bash
# Replace with your actual endpoint and API key
curl -X GET \
  "https://your-cluster-id.region.aws.qdrant.io/collections" \
  -H "api-key: your-api-key-here"
```

If it's correct, you should get a JSON response (even if it's an empty collections list).

If you get a timeout or connection error, the URL might be wrong or there's a proxy/firewall issue.

### Connection Issues

If you encounter connection issues:

1. Verify your Qdrant cluster is active and running (not stopped/creating)
2. Check that the API key has the correct permissions
3. Ensure the URL is the cluster API endpoint, not the dashboard URL
4. Make sure the URL includes `https://` but no trailing paths like `/collections`
5. Check if there are any firewall rules or corporate proxies blocking access

### If You Can't Find the Cluster URL

1. Make sure you're logged into Qdrant Cloud
2. Make sure the cluster is in "Running" state (not stopped/creating)
3. Try the Qdrant documentation: https://qdrant.tech/documentation/cloud/

### If You're Behind a Corporate Proxy

You might need to configure proxy settings. See the `test_mem0_with_proxy.py` file for examples of how to handle proxies with Qdrant.

Alternatively, you can set environment variables before running:
```bash
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
```

### Alternative: Use Qdrant CLI

If you have the Qdrant CLI installed:
```bash
qdrant-cloud cluster list
qdrant-cloud cluster get <cluster-id>
```

This will show you the cluster details including the API endpoint.

### Collection Not Found

The mem0 library will automatically create the collection with the correct schema. If you see collection errors, ensure:
- Your API key has write permissions
- The cluster has enough resources available

### Embedding Dimension Mismatch

Make sure the embedding model dimensions match:
- OpenAI/GitHub Copilot `text-embedding-3-small`: 1536 dimensions
- Ollama `nomic-embed-text`: 768 dimensions

The code automatically sets the correct dimensions based on your LLM provider.

## Benefits of Using Qdrant

- **Performance**: Optimized for large-scale vector search
- **Scalability**: Cloud-managed scaling
- **Features**: Advanced filtering, payload storage, and search options
- **Reliability**: Managed backups and high availability
