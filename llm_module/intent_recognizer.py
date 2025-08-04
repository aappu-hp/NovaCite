import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableSequence
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings

# Load environment variables
load_dotenv()

# 🚀 Improved prompt with explicit identity-related intent category
template = """
Classify the user's request as one of the following:
- faculty_info: when the user asks for faculty details or information about specific staff/departments
- pdf_request: when the user asks for circulars, PDFs, exam timetables, notifications
- identity: when the user asks about who you are, your name, what you do, who created you, or other questions about your role
- unknown: if none of the above apply

User query: {text}

Answer with exactly one of: faculty_info, pdf_request, identity, unknown
"""
prompt = PromptTemplate(input_variables=["text"], template=template)

# Gemini-powered classifier
llm = ChatGoogleGenerativeAI(
    model=settings.GEMINI_CHAT_MODEL,
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0
)

# Classifier chain
chain = RunnableSequence(
    first=RunnablePassthrough.assign(text=lambda x: x["text"]),
    last=prompt | llm | StrOutputParser()
)

def recognize_intent(text: str) -> str:
    """
    Runs the classification chain and returns one of:
    'faculty_info', 'pdf_request', 'identity', or 'unknown'
    """
    try:
        resp = chain.invoke({"text": text}).strip().lower()
        if resp in ["faculty_info", "pdf_request", "identity"]:
            return resp
        return "unknown"
    except Exception as e:
        print(f"❌ Intent classification error: {e}")
        return "unknown"

# 🔍 Example usage
if __name__ == '__main__':
    test_queries = [
        "Show me timetable PDFs",
        "Tell me about Dr. Rajesh in CSE",
        "Who are you?",
        "What can you do?",
        "How's the weather?",
        "Who created you?",
        "Are you a bot?"
    ]

    for q in test_queries:
        intent = recognize_intent(q)
        print(f"🔹 Query: {q}\n➡️ Intent: {intent}\n")
