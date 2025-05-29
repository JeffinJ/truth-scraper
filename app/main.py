import sys
import asyncio
import logging
from contextlib import asynccontextmanager
from app.repositories.truth_repository import TruthRepository
from app.services.t_scraper_service import TestTruthScraperService
from app.services.truth_service import TruthService
from rich.console import Console
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.triggers.interval import IntervalTrigger
from app.services.truth_scraper_service import TruthScraperService
from app.database.db_config import async_session, init_db
from app.api.controllers import truth_controller
from app.api.controllers import truth_sse_controller

# Fix for Playwright on Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()

TEST_MODE = True

origins = [
    "http://localhost:3000",
]

async def scheduled_scrape_job():
    """Job function that will be called by the scheduler"""
    try:
        await truth_scraper.run_once()
    except Exception as e:
        logger.error(f"Scheduled scrape job failed: {e}")
        console.print(f"[red]Scheduled scrape failed: {e}[/red]")


async def start_scheduler():
    """Initialize and start the scheduler"""    
    async with async_session() as session:
        global scheduler, truth_scraper
        
        truth_repo = TruthRepository(session)
        truth_service = TruthService(truth_repo)

        if TEST_MODE:
            console.print("[yellow]🧪 Testing mode enabled - using mock data[/yellow]")
            truth_scraper = TestTruthScraperService(
                target_username="realDonaldTrump",
                truth_service=truth_service,
                headless=False,  # Set to True for production
                scroll_iterations=4,
                testing_mode=True  # Enable testing mode
            )
        else:
            truth_scraper = TruthScraperService(
                target_username="realDonaldTrump",
                truth_service=truth_service,
                headless=False,  # Set to True for production
                scroll_iterations=4
            )
    
        # Initialize scheduler
        scheduler = AsyncIOScheduler()

        scheduler.add_job(
            scheduled_scrape_job,
            trigger=IntervalTrigger(seconds=30),  # Run every 30 minutes
            id="truth_scraper_interval",
            name="Truth Social Scraper (Interval)",
            replace_existing=True
        )

        scheduler.start()
        console.print("[green]✅ Scheduler started successfully![/green]")
        logger.info("AsyncIOScheduler started")


def stop_scheduler():
    """Stop the scheduler"""
    global scheduler
    if scheduler:
        scheduler.shutdown()
        console.print("[yellow]⏹️  Scheduler stopped[/yellow]")
        logger.info("AsyncIOScheduler stopped")



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    console.print("[blue]🚀 Starting application...[/blue]")
    await init_db()  # Initialize the database
    await start_scheduler()
    # try:
    #     console.print("[cyan]🔄 Running initial scrape...[/cyan]")
    #     await truth_scraper.run_once()
    # except Exception as e:
    #     logger.error(f"Initial scrape failed: {e}")
    #     console.print(f"[red]Initial scrape failed: {e}[/red]")
    yield
    
    # Shutdown
    console.print("[blue]🛑 Shutting down application...[/blue]")
    stop_scheduler()

# Create FastAPI app with lifespan
app = FastAPI(
    title="Truth Social Scraper API",
    description="API with automated Truth Social scraping",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(truth_sse_controller.router, prefix="/api/v1", tags=["truths"])
app.include_router(truth_controller.router, prefix="/api/v1", tags=["truths"])

@app.get("/")
async def root():
    return {"message": "Truth Social Scraper API is running"}
