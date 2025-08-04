import os
import time
import lancedb
from dotenv import load_dotenv
from langchain.chains import RetrievalQA
from langchain.schema import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import LanceDB

load_dotenv()

# Initialize embedding model
embedding_model = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# Initialize chat model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    google_api_key=os.getenv("GEMINI_API_KEY")
)
llm.name = "Smurfy"

def setup_qa_chain(db_path="./lance_db", use_existing_index=True):
    db = lancedb.connect(db_path)

    if "faculty_rag" not in db.table_names() or not use_existing_index:
        print("📦 Creating faculty_rag table with index...")

        if "faculty" not in db.table_names():
            raise RuntimeError("❌ Missing 'faculty' table. Run the scraper/loader first.")

        table = db.open_table("faculty")
        records = table.to_arrow().to_pylist()

        documents = []
        for row in records:
            content = (
                f"{row['name']} {row['designation']} {row['qualification']} "
                f"{row['department']} {row['email']} {row['phone']} {row['img_url']}"
            )
            metadata = {
                "name": row["name"],
                "designation": row["designation"],
                "department": row["department"],
                "email": row["email"],
                "phone": row["phone"],
                "image": row["img_url"]
            }
            documents.append(Document(page_content=content, metadata=metadata))

        vector_store = LanceDB.from_documents(
            documents=documents,
            embedding=embedding_model,
            connection=db,
            table_name="faculty_rag"
        )

        num_vectors = len(documents)
        if num_vectors < 256:
            print(f"⚠️ Only {num_vectors} vectors — skipping index creation.")
        else:
            num_partitions = min(64, max(1, num_vectors // 2))
            print(f"🧠 Creating PQ index with {num_partitions} partitions for {num_vectors} vectors")
            vector_store.create_index(
                metric="cosine",
                vector_col="vector",
                num_partitions=num_partitions
            )

        print("✅ faculty_rag table created and indexed.")
    else:
        vector_store = LanceDB(
            connection=db,
            table_name="faculty_rag",
            embedding=embedding_model
        )

    retriever = vector_store.as_retriever(search_kwargs={"k": 50, "n_probe": 10})
    qa = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff"
    )
    return qa

if __name__ == "__main__":
    qa_chain = setup_qa_chain(use_existing_index=True)
    while True:
        q = input("\nQuery (or 'exit'): ").strip()
        if q.lower() == "exit":
            break
        try:
            res = qa_chain.invoke(q)
            print("\n🤖", res["result"])
        except Exception as e:
            print("❌", e)
        time.sleep(2)
