import os
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, Field

class Settings(BaseSettings):
    # Embeddings (Gemini)
    GEMINI_API_KEY: str = Field(..., env="GEMINI_API_KEY")
    GEMINI_EMBEDDING_MODEL: str = "models/embedding-001"

    # Chat (Gemini)
    GEMINI_CHAT_MODEL: str = "gemini-2.0-flash"

    # LanceDB paths
    LANCEDB_PATH: str = "./lance_db"
    FACULTY_TABLE: str = "faculty"
    RAG_TABLE: str = "faculty_rag"
    CIRCULARS_TABLE: str = "circulars"

    # Faculty scraping
    FACULTY_BASE_URL: AnyHttpUrl = "https://www.mcehassan.ac.in/home/Faculty"
    DEPARTMENTS: list[str] = [
        "Civil-Engineering",
        "Mechanical-Engineering",
        "Electrical-and-Electronics-Engineering",
        "Electronics-and-Communication-Engineering",
        "Computer-Science-and-Engineering",
        "Information-Science-and-Engineering",
        "Computer-Science-and-Engineering-(AI&ML)",
        "Computer-Science-and-Business-Systems",
        "Physics",
        "Chemistry",
        "Mathematics",
    ]
    PAGE_SUFFIXES: list[str] = ["", "/10", "/20"]

    # Circulars page & storage
    CIRCULARS_URL: AnyHttpUrl = "https://www.mcehassan.ac.in/home/Circulars"
    PDF_STORAGE: str = "./data/pdfs"

    # Scheduler
    SCRAPE_HOUR: int = 2  # 2 AM daily

    # Retry/rate-limit
    MAX_RETRIES: int = 5
    RETRY_DELAY: int = 4  # seconds between API calls

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
