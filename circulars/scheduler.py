from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from circulars.circulars_fetcher import load_circulars
from config import settings

def scheduled_job():
    print(f"[{datetime.now()}] Re-scraping circulars...")
    load_circulars()

if __name__ == "__main__":
    sched = BlockingScheduler()
    # Schedule daily at configured hour
    sched.add_job(scheduled_job, 'cron', hour=settings.SCRAPE_HOUR, minute=0)
    print(f"Scheduler started — re-scrapes daily at {settings.SCRAPE_HOUR}:00")
    sched.start()
