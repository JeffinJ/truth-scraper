import logging
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.job import Job
from rich.console import Console

from app.repositories.truth_repository import TruthRepository
from app.services.ai.ai_processing_service import AIProcessingService
from app.services.truth_service import TruthService
from app.services.scraper.mock_scraper_service import MockTruthScraperService
from app.services.scraper.truth_social_scraper_service import TruthSocialScraperService
from app.database.db_config import async_session
from app.core.config import settings

logger = logging.getLogger(__name__)
console = Console()


class ScrapingSchedulerService:
    """Service to manage the async scheduler and scraping jobs"""
    
    def __init__(
                    self, 
                    ai_processing_service: AIProcessingService,
                    test_mode: bool = False
                 ):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.truth_scraper = None
        self.ai_processing_service = ai_processing_service
        self.test_mode = test_mode
        self._is_running = False
        self._job_id = "truth_scraper_interval"
        
    async def start(self) -> None:
        """Initialize and start the scheduler with scraping job"""
        if self._is_running:
            logger.warning("Scheduler is already running")
            return
            
        try:
            # Initialize the scraper service
            await self._initialize_scraper()
            
            # Setup and start scheduler
            self.scheduler = AsyncIOScheduler()
            
            # Add the scraping job
            self.scheduler.add_job(
                self._scheduled_scrape_job,
                trigger=IntervalTrigger(seconds=settings.truth_scraper_interval),
                id=self._job_id,
                name="Truth Social Scraper (Interval)",
                replace_existing=True,
                max_instances=1,  # Prevent overlapping jobs
                coalesce=True     # Combine multiple pending executions
            )
            
            self.scheduler.start()
            self._is_running = True
            
            # Log startup information
            next_run = self.scheduler.get_job(self._job_id).next_run_time
            console.print("[green]✅ Scheduler started successfully![/green]")
            console.print(f"[blue]✅ Next run: {next_run}[/blue]")
            console.print(f"[blue]✅ Scraper interval: {settings.truth_scraper_interval} seconds[/blue]")
            console.print(f"[blue]✅ Target username: {settings.truth_profile_username}[/blue]")
            console.print(f"[blue]✅ Test mode: {'enabled' if self.test_mode else 'disabled'}[/blue]")
            
            logger.info("SchedulerService started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}", exc_info=True)
            console.print(f"[red]❌ Failed to start scheduler: {e}[/red]")
            await self.stop()  # Cleanup on failure
            raise
    
    async def stop(self) -> None:
        """Stop the scheduler and cleanup resources"""
        if not self._is_running:
            logger.info("Scheduler is not running")
            return
            
        try:
            # Stop scheduler
            if self.scheduler:
                self.scheduler.shutdown(wait=True)
                self.scheduler = None
                
            # Cleanup scraper resources
            if self.truth_scraper and hasattr(self.truth_scraper, 'cleanup'):
                try:
                    await self.truth_scraper.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up scraper: {e}")
                    
            self._is_running = False
            console.print("[yellow]⏹️ Scheduler stopped[/yellow]")
            logger.info("SchedulerService stopped")
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}", exc_info=True)
            console.print(f"[red]❌ Error stopping scheduler: {e}[/red]")
    
    async def _initialize_scraper(self) -> None:
        """Initialize the appropriate scraper service"""
        try:
            async with async_session() as session:
                truth_repo = TruthRepository(session)
                truth_service = TruthService(truth_repo)
                
                if self.test_mode:
                    console.print("[yellow]🧪 Testing mode enabled - using mock data[/yellow]")
                    self.truth_scraper = MockTruthScraperService(
                        target_username=settings.truth_profile_username,
                        truth_service=truth_service,
                        headless=False,
                        scroll_iterations=4,
                        testing_mode=True
                    )
                else:
                    self.truth_scraper = TruthSocialScraperService(
                        target_username=settings.truth_profile_username,
                        truth_service=truth_service,
                        ai_processing_service=self.ai_processing_service,
                        headless=True,
                        scroll_iterations=4
                    )
                    
        except Exception as e:
            logger.error(f"Failed to initialize scraper: {e}", exc_info=True)
            raise
    
    async def _scheduled_scrape_job(self) -> None:
        """Job function that will be called by the scheduler"""
        if not self.truth_scraper:
            logger.error("Truth scraper not initialized")
            return
            
        try:
            logger.info("Starting scheduled scrape job")
            console.print("[blue]🔄 Running scheduled scrape...[/blue]")
            
            await self.truth_scraper.run_once()
            
            logger.info("Scheduled scrape job completed successfully")
            console.print("[green]✅ Scheduled scrape completed[/green]")
            
        except Exception as e:
            logger.error(f"Scheduled scrape job failed: {e}", exc_info=True)
            console.print(f"[red]❌ Scheduled scrape failed: {e}[/red]")
            
            # TODO: Implement retry logic or circuit breaker pattern
            # TODO: Add alerting for persistent failures
    
    async def run_manual_scrape(self) -> dict:
        """Manually trigger a scrape job (useful for API endpoints)"""
        if not self.truth_scraper:
            raise RuntimeError("Scraper not initialized")
            
        try:
            logger.info("Starting manual scrape job")
            await self.truth_scraper.run_once()
            logger.info("Manual scrape job completed successfully")
            return {"status": "success", "message": "Manual scrape completed"}
            
        except Exception as e:
            logger.error(f"Manual scrape job failed: {e}", exc_info=True)
            return {"status": "error", "message": f"Manual scrape failed: {str(e)}"}
    
    def get_status(self) -> dict:
        """Get current scheduler status"""
        if not self.scheduler or not self._is_running:
            return {
                "running": False,
                "next_run": None,
                "job_count": 0
            }
        
        job = self.scheduler.get_job(self._job_id)
        return {
            "running": self.scheduler.running,
            "next_run": str(job.next_run_time) if job else None,
            "job_count": len(self.scheduler.get_jobs()),
            "test_mode": self.test_mode,
            "target_username": settings.truth_profile_username,
            "interval_seconds": settings.truth_scraper_interval
        }
    
    def pause_job(self) -> bool:
        """Pause the scraping job"""
        if not self.scheduler or not self._is_running:
            return False
            
        try:
            self.scheduler.pause_job(self._job_id)
            logger.info("Scraping job paused")
            return True
        except Exception as e:
            logger.error(f"Failed to pause job: {e}")
            return False
    
    def resume_job(self) -> bool:
        """Resume the scraping job"""
        if not self.scheduler or not self._is_running:
            return False
            
        try:
            self.scheduler.resume_job(self._job_id)
            logger.info("Scraping job resumed")
            return True
        except Exception as e:
            logger.error(f"Failed to resume job: {e}")
            return False
    
    @property
    def is_running(self) -> bool:
        """Check if the scheduler is currently running"""
        return self._is_running and self.scheduler is not None and self.scheduler.running