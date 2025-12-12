import os
from dotenv import load_dotenv
from loguru import logger
from typing import Annotated, Literal, List, Dict
from typing_extensions import TypedDict

from langchain_cerebras import ChatCerebras
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from mem0 import MemoryClient

# Import tools from the tools package
from tools.tavily_tool import tavily_tool
from tools.stock_tools import get_stock_price, get_company_info
from tools.weather_tool import get_weather
from tools.flight_tool import search_flights
from tools.hotel_tool import search_hotels
from tools.database_tool import database_search
from tools.shop_tool import shopping_search
from tools.job_search_tool import job_search
from tools.memory_tool import search_memories, get_all_memories
from tools.recipe_tool import search_recipes

load_dotenv()

# ==========================
# 1. LLM MODEL (CEREBRAS)
# ==========================
model = ChatCerebras(
    model="gpt-oss-120b",
    max_tokens=512,
    api_key=os.getenv("CEREBRAS_API_KEY"),
    temperature=0.3,
)

# Initialize Mem0 Memory Client
mem0 = MemoryClient(api_key=os.getenv("MEM0_API_KEY"))

# ==========================
# 2. DEFINE STATE
# ==========================
class AgentState(TypedDict):
    messages: Annotated[list, "The messages in the conversation"]
    next: str
    user_id: str  # User ID for memory management

# ==========================
# 3. MEMORY FUNCTIONS
# ==========================

def retrieve_memory_context(query: str, user_id: str) -> List[Dict]:
    """Retrieve relevant context from Mem0"""
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
            serialized_memories = ' '.join([mem["memory"] for mem in memory_list])
            logger.info(f"Retrieved {len(memory_list)} memories for user {user_id}")
            context = [
                SystemMessage(content=f"Relevant information from past conversations: {serialized_memories}")
            ]
            return context
        else:
            logger.info(f"No memories found for user {user_id}")
            return []
    except Exception as e:
        logger.error(f"Error retrieving memories: {e}")
        return []

def save_interaction_to_memory(user_id: str, user_input: str, assistant_response: str):
    """Save the interaction to Mem0"""
    try:
        interaction = [
            {
                "role": "user",
                "content": user_input
            },
            {
                "role": "assistant",
                "content": assistant_response
            }
        ]
        result = mem0.add(interaction, user_id=user_id)
        logger.info(f"Memory saved successfully: {len(result.get('results', []))} memories added")
    except Exception as e:
        logger.error(f"Error saving interaction: {e}")

# ==========================
# 4. CREATE SPECIALIZED AGENTS
# ==========================

# Research Agent - handles web searches and general information
research_agent = create_react_agent(
    model=model,
    tools=[tavily_tool],
    prompt="You are a research specialist. Use web search to general or current information."
            "Provide direct and straightforward answers without unnecessary fluff. Get straight to the point."
)

# Finance Agent - handles stock prices and company information
finance_agent = create_react_agent(
    model=model,
    tools=[get_stock_price, get_company_info],
    prompt="You are a financial analyst. Provide stock prices, company information, "
           "and financial data. Provide direct and straightforward answers without unnecessary fluff. Get straight to the point."
)

# Travel Agent - handles weather, flights, and hotels
travel_agent = create_react_agent(
    model=model,
    tools=[get_weather, search_flights, search_hotels],
    prompt="You are a travel specialist. Help with weather information, flight bookings, "
           "and hotel reservations. Provide direct and straightforward answers without unnecessary fluff. Get straight to the point."
)

# Database Agent - handles internal knowledge and document queries
database_agent = create_react_agent(
    model=model,
    tools=[database_search],
    prompt="You are a knowledge base specialist. Search internal documents, manuals, "
           "and other information. Provide direct and straightforward answers without unnecessary fluff. Get straight to the point."
)

# Shopping Agent - handles product searches and shopping
shopping_agent = create_react_agent(
    model=model,
    tools=[shopping_search],
    prompt="You are a shopping assistant. Search for products, prices, and reviews using Google Shopping. Provide direct and straightforward answers without unnecessary fluff. Get straight to the point."
)

# Job Agent - handles job postings and career opportunities
job_agent = create_react_agent(
    model=model,
    tools=[job_search],
    prompt="You are a career specialist. Search for job postings, employment opportunities, and career openings. Provide direct and straightforward answers regarding job roles, companies, and requirements."
)

# Memory Agent - handles memory retrieval and past conversation queries
memory_agent = create_react_agent(
    model=model,
    tools=[search_memories, get_all_memories],
    prompt="You are a memory specialist. Help users recall past conversations, preferences, and stored information. Use search_memories to find specific information and get_all_memories when users ask what you remember about them."
)

# Recipe Agent - handles recipe searches
recipe_agent = create_react_agent(
    model=model,
    tools=[search_recipes],
    prompt="You are a culinary specialist. Search for recipes, cooking instructions, and ingredient lists. Provide direct and straightforward answers with ratings, cooking times, and sources."
)

# ==========================
# 5. DEFINE AGENT NODES
# ==========================

def research_node(state: AgentState):
    result = research_agent.invoke(state)
    return {"messages": result["messages"], "next": "FINISH"}

def finance_node(state: AgentState):
    result = finance_agent.invoke(state)
    return {"messages": result["messages"], "next": "FINISH"}

def travel_node(state: AgentState):
    result = travel_agent.invoke(state)
    return {"messages": result["messages"], "next": "FINISH"}

def database_node(state: AgentState):
    result = database_agent.invoke(state)
    return {"messages": result["messages"], "next": "FINISH"}

def shopping_node(state: AgentState):
    result = shopping_agent.invoke(state)
    return {"messages": result["messages"], "next": "FINISH"}

def job_node(state: AgentState):
    result = job_agent.invoke(state)
    return {"messages": result["messages"], "next": "FINISH"}

def memory_node(state: AgentState):
    result = memory_agent.invoke(state)
    return {"messages": result["messages"], "next": "FINISH"}

def recipe_node(state: AgentState):
    result = recipe_agent.invoke(state)
    return {"messages": result["messages"], "next": "FINISH"}

# ==========================
# 6. SUPERVISOR AGENT
# ==========================

# Define available agents
members = ["research_agent", "finance_agent", "travel_agent", "database_agent", "shopping_agent", "job_agent", "memory_agent", "recipe_agent", "respond", "FINISH"]

supervisor_prompt = """You are Samantha, a helpful AI supervisor managing a team of specialized agents.

Your team consists of:
- research_agent: Handles web searches, current events, general information, and news
- finance_agent: Handles stock prices, company financials, market data
- travel_agent: Handles weather queries, flight searches, hotel bookings
- database_agent: Handles internal documents, manuals, company knowledge base
- shopping_agent: Handles product searches, price comparisons, shopping queries
- job_agent: Handles job searches, career opportunities, employment postings
- memory_agent: Handles queries about past conversations, what you remember, user preferences
- recipe_agent: Handles recipe searches, cooking instructions, ingredients, and culinary queries
- respond: Use this for greetings, casual conversation, or when you can answer directly without tools
- FINISH: Select this when the conversation is complete

Based on the user's query, determine which agent should handle it next.
For greetings like "hello", "hi", introductions, or simple questions you can answer, use "respond".
For queries about past conversations like "what do you remember?", "what do you know about me?", use "memory_agent".
For recipe queries like "how to make pasta", "recipe for cheesecake", use "recipe_agent".
For queries needing specific tools, route to the appropriate specialist agent.

Respond ONLY with the name of the next agent to use.
"""
    
def supervisor_node(state: AgentState):
    """The supervisor routes to the appropriate agent with memory context."""
    messages = state["messages"]
    user_id = state.get("user_id", "samantha")
    
    # Retrieve memory context for better routing decisions
    last_message = messages[-1].content if messages and hasattr(messages[-1], 'content') else (messages[-1].get('content', '') if messages and isinstance(messages[-1], dict) else '')
    memory_context = retrieve_memory_context(last_message, user_id)
    
    # Create routing prompt with memory context
    routing_messages = [
        SystemMessage(content=supervisor_prompt),
    ] + memory_context + messages
    
    # Get supervisor decision
    response = model.invoke(routing_messages)
    next_agent = response.content.strip()
    
    # Validate the response
    if next_agent not in members:
        # Default to respond for conversational queries
        logger.warning(f"Invalid routing decision: {next_agent}. Defaulting to respond")
        next_agent = "respond"
    
    logger.info(f"Supervisor routing to: {next_agent}")
    
    return {"next": next_agent}

def respond_node(state: AgentState):
    """Handles direct responses without tools - for greetings and simple queries with memory."""
    messages = state["messages"]
    user_id = state.get("user_id", "samantha")
    
    # Retrieve memory context
    last_message = messages[-1].content if messages and hasattr(messages[-1], 'content') else (messages[-1].get('content', '') if messages and isinstance(messages[-1], dict) else '')
    memory_context = retrieve_memory_context(last_message, user_id)
    
    # Create a conversational response with memory context
    system_prompt = """You are Samantha, a friendly and helpful AI assistant. 
    Respond naturally to greetings, introductions, and casual conversation. 
    Use the provided context from past conversations to personalize your responses.
    Provide direct and straightforward answers without unnecessary fluff. 
    Get straight to the point."""
    
    response_prompt = [
        SystemMessage(content=system_prompt)
    ] + memory_context + messages
    
    # Use Cerebras for memory-enhanced responses
    response = model.invoke(response_prompt)
    
    # Save interaction to memory
    save_interaction_to_memory(user_id, last_message, response.content)
    
    return {"messages": [response], "next": "FINISH"}

# ==========================
# 7. BUILD THE GRAPH
# ==========================

def create_supervisor_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("research_agent", research_node)
    workflow.add_node("finance_agent", finance_node)
    workflow.add_node("travel_agent", travel_node)
    workflow.add_node("database_agent", database_node)
    workflow.add_node("shopping_agent", shopping_node)
    workflow.add_node("job_agent", job_node)
    workflow.add_node("memory_agent", memory_node)
    workflow.add_node("recipe_agent", recipe_node)
    workflow.add_node("respond", respond_node)
    
    # Add edges: Start -> Supervisor
    workflow.add_edge(START, "supervisor")
    
    # Add conditional edges from supervisor to agents
    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {
            "research_agent": "research_agent",
            "finance_agent": "finance_agent",
            "travel_agent": "travel_agent",
            "database_agent": "database_agent",
            "shopping_agent": "shopping_agent",
            "job_agent": "job_agent",
            "memory_agent": "memory_agent",
            "recipe_agent": "recipe_agent",
            "respond": "respond",
            "FINISH": END,
        },
    )
    
    # After each agent completes, check if they want to finish or continue
    for agent_name in ["research_agent", "finance_agent", "travel_agent", "database_agent", "shopping_agent", "job_agent", "memory_agent", "recipe_agent", "respond"]:
        workflow.add_conditional_edges(
            agent_name,
            lambda x: x.get("next", "FINISH"),
            {
                "FINISH": END,
                "supervisor": "supervisor",
            },
        )
    
    return workflow

# ==========================
# 8. COMPILE THE GRAPH
# ==========================

memory = InMemorySaver()
workflow = create_supervisor_graph()
agent = workflow.compile(checkpointer=memory)

# Config
agent_config = {
    "configurable": {
        "thread_id": "samantha"
    },
    "user_id": "samantha"  # Default user ID for memory management
}