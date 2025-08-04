# NovaCite — Intelligent College RAG System

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/status-production-green" alt="Status">
</p>

An **Intelligent College Information RAG System** for **Malnad College of Engineering (MCE)**, branded as **NovaCite**, that:

* 🧭 **Classifies** user queries into `faculty_info` or `pdf_request`
* 👩‍🏫 **Scrapes** faculty listings → embeds via Google Gemini → stores in LanceDB
* 🤖 **Performs** retrieval-augmented generation on faculty data (map-reduce)
* 📑 **Fetches** real-time PDF circulars → semantic search → interactive download
* 🗺️ **Orchestrates** flows via a LangGraph state machine
* 📝 **Logs** every conversation turn with timestamp, intent, and response

---

## 🚀 Features

| 🔍 Component           | 🛠️  Description                                              |
| ---------------------- | ------------------------------------------------------------- |
| **Intent Recognition** | Gemini‑Flash + LangChain classifier                           |
| **Faculty RAG**        | Async scraper (`crawl4ai`) + LanceDB + map-reduce QA          |
| **PDF/Circular Fetch** | Semantic search over live circulars + sanitized PDF downloads |
| **Scheduler**          | Daily circular re-scrape via APScheduler                      |
| **Logging**            | Full conversation logs in `logs/app.log`                      |

---

## 🔧 Prerequisites

* Python 3.11+
* UV package manager (`uv`)
* Google Gemini API key
* (Optional) Playwright for `crawl4ai`

---

## 📥 Installation

Follow the steps below to set up **NovaCite** on your local machine:

---

### 🧾 Step 1: Clone the Repository

```bash
git clone https://github.com/aappu-hp/NovaCite.git
cd NovaCite
```

---

### 🧪 Step 2: Set Up a Virtual Environment

Using [**uv**](https://github.com/astral-sh/uv) (a fast Python package/dependency manager):

```bash
uv venv
```

Then activate the virtual environment:

* **Windows**:

  ```bash
  .\.venv\Scripts\activate
  ```

* **macOS/Linux**:

  ```bash
  source .venv/bin/activate
  ```

---

### 📦 Step 3: Install Project Dependencies

```bash
uv run -r requirements.txt
```

---

### 🌐 Step 4 (Optional): Install Playwright Browsers

If using Playwright for scraping or automation, install the required browsers:

```bash
playwright install
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and set:

```ini
GOOGLE_API_KEY=your_gemini_api_key
```

Paths & models are in `config.py`:

* `FACULTY_BASE_URL`, `DEPARTMENTS`, `PAGE_SUFFIXES`
* `CIRCULARS_URL`, `PDF_STORAGE`
* `LANCEDB_PATH`, `FACULTY_TABLE`, `RAG_TABLE`
* `GEMINI_EMBEDDING_MODEL`, `GEMINI_CHAT_MODEL`
* `RETRY_DELAY`, `SCRAPE_HOUR`

---

## 📂 Project Structure

```
novacite/
├── app.py                   # CLI entry & logging
├── graph.py                 # LangGraph state machine
├── config.py                # Pydantic settings
├── data_ingestion/          # Faculty scraper + loader
│   ├── scraper.py
│   └── loader.py
├── circulars/               # Circular fetcher & scheduler
│   ├── circulars_fetcher.py
│   └── scheduler.py
├── llm_module/              # Intent recognizer
│   └── intent_recognizer.py
├── qa_system/               # RAG retriever
│   └── retriever.py
├── logs/                    # Conversation logs
│   └── app.log
├── lance_db/                # LanceDB vector store
├── data/pdfs/               # Downloaded PDFs
├── .env                     # Env vars
├── README.md
└── requirements.txt
```

---

## ▶️ Usage Workflow

1. **Intent Classification**

   ```bash
   uv run -m llm_module.intent_recognizer
   ```
2. **Faculty Data & QA**

   ```bash
   uv run -m data_ingestion.scraper      # scrape faculty
   uv run -m qa_system.retriever         # interactive QA
   ```
3. **Circular Fetching**

   ```bash
   uv run -m circulars.circulars_fetcher # scrape & index circulars
   uv run app.py                         # interactive PDF fetch
   ```
4. **Scheduler (Daily)**

   ```bash
   uv run -m circulars.scheduler
   ```

---

## 📝 Sample Logs (`logs/app.log`)

```text
2025-08-04 03:02:25 INFO     USER: who are you | INTENT: identity
2025-08-04 03:02:28 INFO     BOT : I am NovaCite, a helpful assistant built for Malnad College of Engineering. I provide faculty info and college circulars.
2025-08-04 03:02:38 INFO     USER: who created you | INTENT: identity
2025-08-04 03:02:40 INFO     BOT : I was created by Anonymous for Malnad College of Engineering.
2025-08-04 03:02:49 INFO     USER: what can you do | INTENT: identity
2025-08-04 03:02:51 INFO     BOT : I'm NovaCite, an assistant for Malnad College of Engineering. I can provide information about faculty and college circulars.
2025-08-04 03:03:19 INFO     USER: i need a list of all HODs in the all dept of Malnad College of engineering | INTENT: faculty_info
2025-08-04 03:03:26 INFO     BOT : Here is a list of the HODs (Heads of Department) at Malnad College of Engineering, based on the provided data:

*   **Civil Engineering:** Dr. H. S. Narashimhan
*   **Computer Science and Engineering:** Dr. Chandrika.J
*   **Electronics and Communication Engineering:** Dr. Padmaja Devi G
*   **Electrical and Electronics Engineering:** Dr. Rajanna S.
*   **Mechanical Engineering:** Dr. Ezhil Vannan S
*   **Information Science and Engineering:** Dr. Ananda Babu J
*   **Computer Science and Business Systems:** Dr. Ramesh B
*   **AI & ML:** Dr. Arjun B C
*   **Mathematics:** Dr. Kalavathi G K
2025-08-04 03:03:49 INFO     USER: 6th sem exam timetable | INTENT: pdf_request
2025-08-04 03:03:58 INFO     BOT : ✅ Downloaded and saved to ./data/pdfs\Make_up_exam_Time_table_for_4th_and_6th_SEM.pdf
```

© 2025 **Malnad College of Engineering** — Built by **Anonymous**
