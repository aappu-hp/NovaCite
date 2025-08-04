import os
import pyarrow as pa
import lancedb
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import settings

load_dotenv()
db = lancedb.connect(settings.LANCEDB_PATH)

# Embedding client
emb_client = GoogleGenerativeAIEmbeddings(
    model=settings.GEMINI_EMBEDDING_MODEL,
    google_api_key=os.getenv('GEMINI_API_KEY')
)

def store_in_lancedb(data: list[list]):
    if not data:
        print("⚠️ No data to store."); return

    rows = []
    for r in data:
        try:
            name, desig, qual, phone, email, img_url, dept = r
        except ValueError:
            print(f"⚠️ Skipping malformed record: {r}")
            continue

        text = f"{name} {desig} {qual} {phone} {email} {dept}".strip()
        try:
            vec = emb_client.embed_query(text)
        except Exception as e:
            print(f"Error embedding {name}: {e}")
            continue

        rows.append({
            'name': name, 
            'designation': desig, 
            'qualification': qual,
            'phone': phone, 
            'email': email, 
            'img_url': img_url, 
            'department': dept,
            'embedding': vec
        })

    if not rows:
        print("❌ All embeddings failed."); return

    dim = len(rows[0]['embedding'])
    schema = pa.schema([
        pa.field('name', pa.string()), 
        pa.field('designation', pa.string()),
        pa.field('qualification', pa.string()), 
        pa.field('phone', pa.string()),
        pa.field('email', pa.string()), 
        pa.field('img_url', pa.string()),
        pa.field('department', pa.string()),
        pa.field('embedding', pa.list_(pa.float32(), dim))
    ])

    db.create_table(settings.FACULTY_TABLE, data=rows, schema=schema, mode='overwrite')
    print(f"✅ {len(rows)} records stored in LanceDB.")
