import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

from llm_module.intent_recognizer import recognize_intent
from qa_system.retriever import setup_qa_chain
from circulars.circulars_fetcher import handle_pdf_scraping
from config import settings

load_dotenv()

class AgentState(dict):
    query: str
    intent: str = ""
    result: str = ""

# Preload faculty QA RAG chain
doc_qa_chain = setup_qa_chain()

# 🔧 Dedicated Gemini LLM instance for identity flow
identity_llm = ChatGoogleGenerativeAI(
    model=settings.GEMINI_CHAT_MODEL,
    temperature=0.3,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Node: Classify intent
async def classify(state: AgentState):
    state["intent"] = recognize_intent(state["query"])
    return state

# Node: Faculty data from RAG
async def faculty_flow(state: AgentState):
    resp = await doc_qa_chain.ainvoke({"query": state["query"]})
    state["result"] = resp["result"]
    return state

# Node: Scrape circular PDFs
async def circular_flow(state: AgentState):
    result = handle_pdf_scraping(state["query"])  # no await
    state["result"] = result
    return state

# ✅ Node: Dynamic identity answer using chat history messages
async def identity_flow(state: AgentState):
    system_msg = SystemMessage(
        content=(
            "You are NovaCite, a helpful assistant built for Malnad College of Engineering, "
            "created by Anonymous. You assist students with faculty info and college circulars. "
            "Respond briefly and clearly about who you are or what you do."
        )
    )
    human_msg = HumanMessage(content=state["query"])

    result = await identity_llm.ainvoke([system_msg, human_msg])
    state["result"] = result.content
    return state

# Node: Unknown intent
async def unknown_flow(state: AgentState):
    state["result"] = (
        "❓ Sorry, I can only help with faculty info or college circulars.\n"
        "Try asking about exam schedules, PDFs, or faculty details."
    )
    return state

# Build graph
builder = StateGraph(AgentState)

builder.add_node("classify", RunnableLambda(classify))
builder.add_node("faculty", RunnableLambda(faculty_flow))
builder.add_node("circular", RunnableLambda(circular_flow))
builder.add_node("identity", RunnableLambda(identity_flow))  # ✅
builder.add_node("unknown", RunnableLambda(unknown_flow))

builder.set_entry_point("classify")

builder.add_conditional_edges("classify", lambda s: s["intent"], {
    "faculty_info": "faculty",
    "pdf_request": "circular",
    "identity": "identity",  # ✅
    "unknown": "unknown"
})

builder.set_finish_point("faculty")
builder.set_finish_point("circular")
builder.set_finish_point("identity")
builder.set_finish_point("unknown")

agent_executor = builder.compile()
