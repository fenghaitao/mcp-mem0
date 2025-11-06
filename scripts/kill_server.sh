#!/bin/bash
#
# Emergency kill script for the MCP mem0 server
# Use this if CTRL+C doesn't work
#

echo "🔍 Finding MCP mem0 server processes..."
pids=$(pgrep -f "main.py")

if [ -z "$pids" ]; then
    echo "❌ No MCP mem0 server processes found"
    exit 1
fi

echo "📍 Found processes: $pids"
for pid in $pids; do
    echo "💀 Killing process $pid..."
    kill -9 $pid 2>/dev/null && echo "✅ Process $pid killed" || echo "⚠️  Process $pid already dead"
done

echo "🧹 Cleaning up any remaining python processes with mem0..."
pkill -f "mem0.*mcp\|main.py.*mem0" && echo "✅ Additional cleanup completed" || echo "📝 No additional processes to clean"

echo "✅ Server kill completed!"