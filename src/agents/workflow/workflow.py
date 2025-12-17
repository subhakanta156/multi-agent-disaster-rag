from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Dict
import json
import os
from dotenv import load_dotenv

# =========================
# AGENTS
# =========================
from agents.agent_types.user_query_agent import UserQueryAgent
from agents.agent_types.weather_agent import WeatherAgent
from agents.agent_types.rag_agent import RAGAgent
from agents.agent_types.evaluator_agent import EvaluatorAgent

# =========================
# ROUTING
# =========================
from agents.policies.routing_policy import RoutingPolicy

# =========================
# TOOLS
# =========================
from agents.tools.calculator import calculator_tool
from agents.tools.web_search_tool import web_search_tool
from agents.tools.weather_api import (
    weather_location_detector,
    weather_station_mapper,
    imd_weather_fetcher
)
from agents.tools.local_file_reader import imd_pdf_reader
from agents.tools.rag_tool import RAGTool

# =========================
# LLM
# =========================
from langchain_groq import ChatGroq

# =========================
# MEMORY
# =========================
from agents.memory.short_term import ShortTermMemory
from agents.memory.long_term import LongTermMemory


# =========================
# ENV
# =========================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
env_path = os.path.join(project_root, ".env")

load_dotenv(env_path)

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("❌ GROQ_API_KEY missing")

print("✅ Environment loaded")


# =========================
# STATE
# =========================
class AppState(TypedDict):
    query: str
    rewritten_query: Optional[str]
    route: Optional[str]
    selected_agent: Optional[str]
    agent_response: Optional[str]
    response: Optional[str]
    evaluation: Optional[Dict]


# =========================
# INIT CORE
# =========================
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0.2)
routing_policy = RoutingPolicy(debug=True)

short_term_memory = ShortTermMemory()
long_term_memory = LongTermMemory()


# =========================
# RAG RETRIEVER
# =========================
from retriver import DocumentRetriever

retriever = DocumentRetriever(persist_dir=os.path.join(project_root, "chroma_db"))
rag_tool = RAGTool(retriever)

# =========================
# AGENTS
# =========================
user_agent = UserQueryAgent(llm=llm)

weather_agent = WeatherAgent(tools={
    "weather_location_detector": weather_location_detector,
    "weather_station_mapper": weather_station_mapper,
    "imd_weather_fetcher": imd_weather_fetcher,
    "imd_pdf_reader": imd_pdf_reader
})

rag_agent = RAGAgent(llm_client=llm, tools={"rag": rag_tool})

evaluator_agent = EvaluatorAgent(
    llm=llm,
    tools={"rag": rag_tool, "web_search": web_search_tool},
    auto_improve_confidence=0.75
)


# ============================================================
# 🔥 NODE 1: QUERY REWRITER (MOST IMPORTANT FIX)
# ============================================================
def rewrite_query_node(state: AppState) -> AppState:
    """
    Convert follow-up questions into self-contained queries
    using short-term memory.
    """

    history = short_term_memory.get()
    if not history:
        state["rewritten_query"] = state["query"]
        return state

    context = ""
    for h in history[-3:]:
        context += f"User: {h['user']}\nAssistant: {h['assistant']}\n"

    prompt = f"""
You are a query rewriter.

Conversation history:
{context}

User follow-up question:
{state['query']}

Rewrite it into a fully self-contained question.
DO NOT answer. Only rewrite.
"""

    rewritten = llm.invoke(prompt).content.strip()

    print("🔁 QUERY REWRITTEN →", rewritten)

    state["rewritten_query"] = rewritten
    return state


# =========================
# ROUTER NODE
# =========================
def router_node(state: AppState) -> AppState:
    query = state.get("rewritten_query", state["query"])
    route = routing_policy.route(query)

    print(f"[Router] → {route}")
    return {"route": route, "selected_agent": route}


# =========================
# TOOL NODES
# =========================
def calculator_node(state: AppState):
    q = state["rewritten_query"]
    result = calculator_tool.invoke({"expression": q})
    return {"response": f"Calculation: {result}"}

def web_search_node(state: AppState):
    q = state["rewritten_query"]
    result = web_search_tool.invoke({"query": q})
    return {"response": result}


# =========================
# AGENT NODES
# =========================
def weather_node(state: AppState):
    result = weather_agent({"query": state["rewritten_query"]})
    return {"agent_response": result["response"]}

def rag_node(state: AppState):
    result = rag_agent.run(state["rewritten_query"])
    return {"agent_response": result.get("answer")}

def general_node(state: AppState):
    return {"agent_response": user_agent({"query": state["rewritten_query"]})["agent_response"]}


# =========================
# EVALUATOR
# =========================
def evaluator_node(state: AppState):
    result = evaluator_agent(state)
    final = result.get("evaluation", {}).get(
        "improved_answer",
        state.get("agent_response")
    )

    short_term_memory.add({
        "user": state["query"],
        "assistant": final
    })

    return {"response": final}


# =========================
# GRAPH
# =========================
graph = StateGraph(AppState)

graph.add_node("rewrite", rewrite_query_node)
graph.add_node("router", router_node)
graph.add_node("calculator", calculator_node)
graph.add_node("web_search", web_search_node)
graph.add_node("weather", weather_node)
graph.add_node("rag", rag_node)
graph.add_node("general", general_node)
graph.add_node("evaluator", evaluator_node)

graph.set_entry_point("rewrite")

graph.add_edge("rewrite", "router")

graph.add_conditional_edges(
    "router",
    lambda s: s["route"],
    {
        "calculator": "calculator",
        "web_search": "web_search",
        "weather": "weather",
        "rag": "rag",
        "general": "general"
    }
)

graph.add_edge("calculator", END)
graph.add_edge("web_search", END)

graph.add_edge("weather", "evaluator")
graph.add_edge("rag", "evaluator")
graph.add_edge("general", "evaluator")

graph.add_edge("evaluator", END)

app = graph.compile()

print("✅ FINAL WORKFLOW READY")
print("📊 Flow: Rewrite → Router → Agent/Tool → Evaluator → Response")
