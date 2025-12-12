"""
Memory Tool - Allows the agent to search and retrieve memories
"""
from langchain.tools import tool
from mem0 import MemoryClient
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Mem0 client
mem0 = MemoryClient(api_key=os.getenv("MEM0_API_KEY"))

@tool
def search_memories(query: str, user_id: str = "samantha") -> str:
    """
    Search through stored memories to find relevant information about the user.
    Use this when the user asks about past conversations, preferences, or personal information.
    
    Args:
        query: The search query to find relevant memories
        user_id: The user ID to search memories for (default: "samantha")
    
    Returns:
        A formatted string containing relevant memories
    """
    try:
        # Mem0 v2 API requires filters
        filters = {
            "OR": [
                {
                    "user_id": user_id
                }
            ]
        }
        
        memories = mem0.search(query, version="v2", filters=filters)
        memory_list = memories.get('results', [])
        
        if memory_list:
            result = f"Found {len(memory_list)} relevant memories:\n\n"
            for i, mem in enumerate(memory_list, 1):
                result += f"{i}. {mem['memory']}\n"
            return result
        else:
            return "No relevant memories found for this query."
    except Exception as e:
        return f"Error searching memories: {str(e)}"

@tool
def get_all_memories(user_id: str = "samantha") -> str:
    """
    Retrieve all stored memories for a user.
    Use this when the user asks "what do you know about me?" or "what do you remember?"
    
    Args:
        user_id: The user ID to retrieve memories for (default: "samantha")
    
    Returns:
        A formatted string containing all memories
    """
    try:
        # Get all memories for the user
        filters = {
            "OR": [
                {
                    "user_id": user_id
                }
            ]
        }
        
        # Use a broad query to get all memories
        memories = mem0.search("", version="v2", filters=filters, limit=50)
        memory_list = memories.get('results', [])
        
        if memory_list:
            result = f"I have {len(memory_list)} memories about you:\n\n"
            for i, mem in enumerate(memory_list, 1):
                result += f"{i}. {mem['memory']}\n"
            return result
        else:
            return "I don't have any stored memories yet."
    except Exception as e:
        return f"Error retrieving memories: {str(e)}"
