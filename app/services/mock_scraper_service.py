from fastapi import Depends
from playwright.async_api import async_playwright
from app.services.truth_service import TruthService
from app.services.mock_truth_generator import MockTruthPostGenerator
from rich.console import Console
from datetime import datetime
import asyncio
import logging
import random
import json
from app.core.config import settings

class MockTruthScraperService:
    def __init__(
        self, 
        truth_service: TruthService, 
        target_username="realDonaldTrump", 
        headless=True, 
        scroll_iterations=4,
        testing_mode=False 
    ):
        self.target_username = target_username
        self.headless = headless
        self.truth_service = truth_service
        self.scroll_iterations = scroll_iterations
        self.console = Console()
        self.logger = self._setup_logger()
        self.testing_mode = testing_mode
        self.mock_generator = MockTruthPostGenerator() if testing_mode else None
        
    def _setup_logger(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def enable_testing_mode(self):
        """Enable testing mode with mock data"""
        self.testing_mode = True
        self.mock_generator = MockTruthPostGenerator()
        self.console.print("[yellow]🧪 Testing mode enabled - using mock data[/yellow]")
    
    def disable_testing_mode(self):
        """Disable testing mode - use real scraping"""
        self.testing_mode = False
        self.mock_generator = None
        self.console.print("[blue]🌐 Testing mode disabled - using real scraping[/blue]")

    async def simulate_scraping_delay(self):
        """Simulate realistic scraping delay"""
        delay = random.uniform(2, 8)  # Random delay between 2-8 seconds
        self.console.print(f"[yellow]⏳ Simulating scraping delay ({delay:.1f}s)...[/yellow]")
        await asyncio.sleep(delay)

    async def generate_mock_posts_for_testing(self) -> list:
        """Generate mock posts that simulate real scraping behavior"""
        await self.simulate_scraping_delay()
        
        # Return new posts with probability to mock no new posts
        # 30% chance of no new posts
        if random.random() < 0.3:  
            self.console.print("[yellow]🎭 Mock: No new posts found[/yellow]")
            return []
        
        # Generate 1-5 new posts
        post_count = random.randint(1, 5)
        
        # Get last saved post to ensure new timestamps
        last_saved_post = await self.truth_service.get_last_truth()
        start_time = last_saved_post.timestamp if last_saved_post else datetime.now()
        
        mock_posts = self.mock_generator.generate_mock_posts(
            count=post_count,
            start_time=start_time
        )
        
        self.console.print(f"[green]🎭 Mock: Generated {len(mock_posts)} new posts[/green]")
        self.console.print("User Data:\n%s", json.dumps(mock_posts, indent=4))
        return mock_posts

    async def scrape_posts(self):
        """Main scraping method - with testing mode support"""
        try:
            self.console.print("🚀 Starting Truth Social scraper...")
            
            if self.testing_mode:
                self.console.print("[yellow]🧪 TESTING MODE: Using mock data[/yellow]")
                fetched_posts = await self.generate_mock_posts_for_testing()
            else:
                # Original scraping logic
                start_url = f"{settings.truth_social_base_url}/{self.target_username}"
                async with async_playwright() as playwright:
                    fetched_posts = await self._run_browser_session(playwright, start_url)
            
            # Rest of the method remains the same
            last_saved_post = await self.truth_service.get_last_truth()
            last_saved_post_time = last_saved_post.timestamp if last_saved_post else None
            
            self.console.print(f"fetched_posts: {len(fetched_posts)} posts collected.")
            self.console.print(f"[blue]Last saved post time: {last_saved_post_time}[/blue]")
            
            new_posts = []
            for post in fetched_posts:
                post_ts = (
                    post["timestamp"]
                    if isinstance(post["timestamp"], datetime)
                    else self.parse_iso_datetime(post["timestamp"])
                )
                if last_saved_post_time is None or post_ts > last_saved_post_time:
                    new_posts.append(post)
            
            self.console.print(f"[green]Collected {len(new_posts)} new posts after last saved post.[/green]")
            
            # Save the posts to the database
            if new_posts:
                self.console.print(f"[blue]--Saving {len(new_posts)} posts to database...[/blue]")
                await self.truth_service.save_truths(new_posts)
                self.console.print("[green]Posts saved to database![/green]")
                
                # Trigger SSE update for new posts
                await self.trigger_sse_for_new_posts(new_posts)
            else:
                self.console.print("[yellow]No new posts collected.[/yellow]")
            
            return fetched_posts
                
        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            self.console.print(f"[red]Scraping failed: {e}[/red]")
            return []

    async def trigger_sse_for_new_posts(self, new_posts):
        """Trigger SSE update when new posts are saved"""
        try:
            # Format posts for SSE
            sse_data = {
                "type": "new_posts",
                "count": len(new_posts),
                "data": new_posts,
                "timestamp": datetime.now().isoformat()
            }
            
            # Here you would trigger your SSE service
            # await SSEService.broadcast(sse_data)
            self.console.print(f"[green]📡 SSE triggered for {len(new_posts)} new posts[/green]")
            
        except Exception as e:
            self.console.print(f"[red]❌ SSE trigger failed: {e}[/red]")

    def parse_iso_datetime(self, dt_str: str) -> datetime:
        """Parse ISO 8601 datetime string safely."""
        # Avoid double appending +00:00 if already present
        if dt_str.endswith("Z"):
            dt_str = dt_str.replace("Z", "+00:00")
        
        # Prevent +00:00+00:00 situation
        if dt_str.count("+00:00") > 1:
            dt_str = dt_str.replace("+00:00", "", 1)
    
        return datetime.fromisoformat(dt_str)

    async def extract_key_properties(self, posts_data):
        """Extract key properties from posts data"""
        simplified_posts = []
        
        for post in posts_data:
            simplified_post = {
                "id": post["id"], 
                "content": post["content"],
                "timestamp": post["created_at"],
                "url": post["url"],
            }
            
            if post["media_attachments"] and len(post["media_attachments"]) > 0:
                simplified_post["media_urls"] = [
                    media["url"] for media in post["media_attachments"]
                ]
            
            simplified_posts.append(simplified_post)
        
        return simplified_posts

    async def run_once(self):
        """Run the scraper once - useful for scheduled tasks"""
        mode = "TESTING" if self.testing_mode else "PRODUCTION"
        self.console.print(f"[cyan]📅 Scheduled scrape started at {datetime.now()} [{mode}][/cyan]")
        posts = await self.scrape_posts()
        self.console.print(f"[cyan]📅 Scheduled scrape completed. Collected {len(posts)} posts. [{mode}][/cyan]")
        return posts