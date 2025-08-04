import os
import time
import re
import json
import requests
from urllib.parse import urljoin
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import lancedb

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import LanceDB
from langchain.schema import Document
from config import settings

# Load environment variables
env_path = os.getenv("DOTENV_PATH", ".env")
load_dotenv(env_path)

# Configuration
PDF_DIR = settings.PDF_STORAGE
DB_PATH = settings.LANCEDB_PATH
TABLE_NAME = "circulars"
STATE_FILE = os.path.join(PDF_DIR, "circulars_state.json")

# Ensure storage dirs exist
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(DB_PATH, exist_ok=True)

# Initialize embedding & LLM clients
embeddings = GoogleGenerativeAIEmbeddings(
    model=settings.GEMINI_EMBEDDING_MODEL,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)
llm = ChatGoogleGenerativeAI(
    model=settings.GEMINI_CHAT_MODEL,
    temperature=0,
    google_api_key=os.getenv("GEMINI_API_KEY"),
)

# Connect to LanceDB
db = lancedb.connect(DB_PATH)


def load_circulars() -> None:
    """
    Scrape the circulars table and rebuild the LanceDB index only
    when a new circular appears in the first row.
    """
    try:
        resp = requests.get(str(settings.CIRCULARS_URL), timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch circulars page: {e}")
        return

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find("table", class_="table-hover")
    if not table or not table.tbody:
        print("⚠️ Circular table not found on page.")
        return

    # Collect (desc, url)
    rows = []
    for tr in table.tbody.find_all("tr"):
        cols = tr.find_all("td")
        if len(cols) != 3:
            continue
        desc = cols[1].get_text(strip=True)
        a = cols[2].find("a")
        href = a["href"] if a and a.has_attr("href") else None
        if href:
            full_url = urljoin(str(settings.CIRCULARS_URL), href)
            rows.append((desc, full_url))

    if not rows:
        print("⚠️ No circulars found.")
        return

    # Check state
    prev_first = None
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as sf:
                prev_first = json.load(sf).get("first_desc")
        except Exception:
            prev_first = None

    # If unchanged, skip
    if prev_first and rows[0][0] == prev_first:
        print("ℹ️ No new circulars detected; skipping update.")
        return

    # Build Document list
    docs = [
        Document(page_content=desc, metadata={"url": url})
        for desc, url in rows
    ]

    # Drop & rebuild index
    if TABLE_NAME in db.table_names():
        db.drop_table(TABLE_NAME)
    LanceDB.from_documents(
        documents=docs,
        embedding=embeddings,
        connection=db,
        table_name=TABLE_NAME,
    )
    print(f"✅ Indexed {len(docs)} circulars.")

    # Save new state
    try:
        with open(STATE_FILE, "w") as sf:
            json.dump({"first_desc": rows[0][0]}, sf)
    except Exception as e:
        print(f"⚠️ Could not write state file: {e}")


def find_circulars(query: str, k: int = 5) -> list[Document]:
    """
    Semantic search on the circulars index.
    """
    if TABLE_NAME not in db.table_names():
        print("⚠️ Circulars index not found; run load_circulars() first.")
        return []

    vs = LanceDB(
        connection=db,
        table_name=TABLE_NAME,
        embedding=embeddings,
    )
    retriever = vs.as_retriever(search_kwargs={"k": k})
    return retriever.invoke(query)


def download_pdf(url: str, title: str) -> str:
    """
    Download a PDF if not already saved, using a sanitized, underscore-based filename.
    """
    # Sanitize & truncate title
    clean = re.sub(r"[^\w\s]", "", title)
    underscored = "_".join(clean.strip().split())[:50]
    filename = f"{underscored}.pdf"
    path = os.path.join(PDF_DIR, filename)

    if os.path.exists(path):
        return path

    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        if "application/pdf" not in resp.headers.get("Content-Type", ""):
            raise ValueError("URL did not return a PDF")

        with open(path, "wb") as f:
            f.write(resp.content)
        return path

    except Exception as e:
        print(f"❌ Download failed: {e}")
        return ""


def handle_pdf_scraping(user_query: str) -> str:
    """
    End-to-end flow for circular requests:
      1) load_circulars()
      2) find_circulars()
      3) interactive selection & download
    Returns a summary string or error.
    """
    load_circulars()
    docs = find_circulars(user_query, k=5)
    if not docs:
        return "❌ No matching circulars found."

    # Show options
    menu = "\n".join(f"{i+1}. {d.page_content}" for i, d in enumerate(docs))
    prompt = (
        f"I found these circulars for \"{user_query}\":\n{menu}\n"
        "Please pick a number (or type 'skip')."
    )
    # Use LLM to ask user which one? Here we fallback to raw input
    choice = input(f"\n{prompt}\n> ").strip()
    if choice.lower() == "skip":
        return "Skipped download."

    if not choice.isdigit() or not (1 <= int(choice) <= len(docs)):
        return "❌ Invalid selection."

    selected = docs[int(choice) - 1]
    path = download_pdf(selected.metadata["url"], selected.page_content)
    if path:
        return f"✅ Downloaded and saved to {path}"
    else:
        return "❌ Download failed."


if __name__ == "__main__":
    while True:
        q = input("\nEnter circular query (or 'exit'): ").strip()
        if q.lower() in ("exit", "quit"):
            break
        print(handle_pdf_scraping(q))
        time.sleep(settings.RETRY_DELAY)
