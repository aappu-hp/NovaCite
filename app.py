# app.py
import os
import sys
import asyncio
import logging
from graph import agent_executor
from llm_module.intent_recognizer import recognize_intent

# ─── Ensure log directory exists ───────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)

# ─── Setup logging ─────────────────────────────────────────────────────────────
logging.basicConfig(
    filename="logs/app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Async Input Loop ──────────────────────────────────────────────────────────
async def interactive_loop():
    print("🤖 Type your query, or 'exit' to quit.")
    while True:
        try:
            query = input("\nYou: ").strip()
            if query.lower() in ("exit", "quit"):
                print("👋 Goodbye!")
                break

            # Optional: detect intent for logs
            intent = recognize_intent(query)
            logger.info(f"USER: {query} | INTENT: {intent}")

            # Process query
            result = await agent_executor.ainvoke({"query": query})
            response = result.get("result", "No response.")
            logger.info(f"BOT : {response}")

            print(f"\n🤖 Agent: {response}")

        except KeyboardInterrupt:
            print("\n👋 Exiting...")
            break

        except Exception as e:
            logger.exception(f"❌ Exception during query handling: {e}")
            print(f"❌ Unexpected error: {e}")

# ─── Entrypoint ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        asyncio.run(interactive_loop())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Program stopped.")
        sys.exit(0)
