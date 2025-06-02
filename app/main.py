import sys
import asyncio
import logging
from contextlib import asynccontextmanager

from app.services.ai.ai_processing_service import AIProcessingService
from app.services.scraper.scraping_scheduler_service import ScrapingSchedulerService
from dotenv import load_dotenv
load_dotenv(".env", override=True)

from rich.console import Console
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.db_config import init_db
from app.api.controllers import truth_controller
from app.api.controllers import truth_sse_controller
from app.core.config import settings

# Fix for Playwright on Windows
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
console = Console()
TEST_MODE = False  

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    console.print("[blue]🚀 Starting application...[/blue]")
    
    try:
        # Initialize database
        await init_db()
        console.print("[green]✅ Database initialized[/green]")
        
        # Initialize AI processing service
        ai_processing_service = AIProcessingService()
        await ai_processing_service.start(num_workers=2)
        app.state.ai_processing_service = ai_processing_service
        console.print("[green]✅ AI processing service started[/green]")
        
        # Initialize and start scraping scheduler service
        scheduler_service = ScrapingSchedulerService(test_mode=TEST_MODE, ai_processing_service=ai_processing_service)
        await scheduler_service.start()
        app.state.scheduler_service = scheduler_service
        console.print("[green]🎉 Application startup completed![/green]")
        
    except Exception as e:
        console.print(f"[red]🔥 Application startup failed: {e}[/red]")
        logger.error(f"Application startup failed: {e}", exc_info=True)
        raise
    
    yield
    
    console.print("[blue]🛑 Shutting down application...[/blue]")
    
    try:
        if hasattr(app.state, 'scheduler_service'):
            await app.state.scheduler_service.stop()
            
        if hasattr(app.state, 'ai_processing_service'):
            await app.state.ai_processing_service.stop()
            
        console.print("[green]✅ Application shutdown completed[/green]")
        
    except Exception as e:
        console.print(f"[red]🔥 Error during shutdown: {e}[/red]")
        logger.error(f"Error during shutdown: {e}", exc_info=True)
        

app = FastAPI(
    title="Truth Social Scraper API",
    description="API with automated Truth Social scraping",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(truth_sse_controller.router, prefix="/api/v1", tags=["truths"])
app.include_router(truth_controller.router, prefix="/api/v1", tags=["truths"])

@app.get("/")
async def root():
    return {"message": "Truth Social Scraper API is running"}


@app.post("/scrape/pause")
async def pause_scraper():
    """Pause the scheduled scraping"""
    success = app.state.scheduler_service.pause_job()
    return {
        "status": "success" if success else "error",
        "message": "Scraper paused" if success else "Failed to pause scraper"
    }
    
@app.post("/api/v1/scrape/resume")
async def resume_scraper():
    """Resume the scheduled scraping"""
    success = app.state.scheduler_service.resume_job()
    return {
        "status": "success" if success else "error",
        "message": "Scraper resumed" if success else "Failed to resume scraper"
    }
    
    
@app.get("/api/v1/scrape/status")
async def scraper_status():
    """Get current scraper status"""
    return app.state.scheduler_service.get_status()