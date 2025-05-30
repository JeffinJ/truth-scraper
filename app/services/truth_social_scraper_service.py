from playwright.async_api import async_playwright
from app.services.truth_service import TruthService
from rich.console import Console
from datetime import datetime
import asyncio
import json
import logging
from app.core.config import settings


def parse_iso_datetime(dt_str: str) -> datetime:
    """Parse ISO 8601 datetime with Z suffix."""
    if dt_str.endswith("Z"):
        dt_str = dt_str.replace("Z", "+00:00")
    return datetime.fromisoformat(dt_str)


class TruthSocialResponseHandler:
    """Handles API responses from Truth Social"""
    
    def __init__(self, parent_scraper):
        self.collected_posts = []
        self.parent = parent_scraper
        
    async def handle_response(self, response):
        """Process successful API response"""
        data = await response.json()
        truths_data = await self.parent.extract_post_data(data)
        self.parent.logger.info("User Data:\n%s", json.dumps(truths_data, indent=4))
        
        # Append the extracted posts to our collection
        self.collected_posts.extend(truths_data)
        
    async def check_response(self, response):
        """Check and route API responses based on status"""
        if "statuses" in response.url:
            if response.status == 200:
                self.parent.console.print(f"[green]Response: {response.url} - {response.status}[/green]")
                await self.handle_response(response)
                return
            if response.status == 403:
                self.parent.console.print(f"[red]Response: {response.url} - {response.status}[/red]")
                print("403:", await response.json())
            if response.status == 429:
                self.parent.console.print(f"[red]Response: {response.url} - {response.status}[/red]")
                self.parent.console.print(f"[red]429 Too Many Requests[/red]")
                try:
                    await asyncio.sleep(10)
                    text = await response.text()
                    self.parent.console.print(f"[yellow]Raw 429 response: {text}[/yellow]")
                except Exception as e:
                    self.parent.console.print(f"[red]Error reading 429 response: {e}[/red]")
            else:
                try:
                    text = await response.text()
                    self.parent.console.print(f"[red]Unhandled status {response.status}: {text}[/red]")
                except Exception as e:
                    self.parent.console.print(f"[red]Error reading error response: {e}[/red]")
                    
                    
                    
                    
class TruthSocialScraperService:
    """Main scraping service for Truth Social posts"""
    
    def __init__(
            self, 
            truth_service: TruthService, 
            target_username: str = None, 
            headless: bool = True, 
            scroll_iterations: int = 4
        ):
        self.target_username = target_username
        self.headless = headless
        self.truth_service = truth_service
        self.scroll_iterations = scroll_iterations
        self.console = Console()
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def extract_post_data(self, posts_data):
        simplified_posts = []
        
        for post in posts_data:
            simplified_post = {
                "id": post["id"], 
                "content": post["content"],
                "timestamp": post["created_at"],
                "url": post["url"],
            }
            
            # Only add media_urls if media_attachments exists and has items
            if post["media_attachments"] and len(post["media_attachments"]) > 0:
                simplified_post["media_urls"] = [
                    media["url"] for media in post["media_attachments"]
                ]
            
            simplified_posts.append(simplified_post)
        
        return simplified_posts

    async def scrape_posts(self):
        """Main scraping method"""
        try:
            self.console.print("🚀 Starting Truth Social scraper...")
            start_url = f"{settings.truth_social_base_url}/{self.target_username}"
            
            async with async_playwright() as playwright:
                fetched_posts = await self._run_browser_session(playwright, start_url)
                last_saved_post = await self.truth_service.get_last_truth()
                last_saved_post_time = last_saved_post.timestamp if last_saved_post else None
                self.console.print(f"fetched_posts: {len(fetched_posts)} posts collected.")
                self.console.print(f"[blue]Last saved post time: {last_saved_post_time}[/blue]")
                
                new_posts = []
                for post in fetched_posts:
                    post_ts = (
                        post["timestamp"]
                        if isinstance(post["timestamp"], datetime)
                        else parse_iso_datetime(post["timestamp"])
                    )
                    if last_saved_post_time is None or post_ts > last_saved_post_time:
                        new_posts.append(post)
                
                
                self.console.print(f"[green]Collected {len(new_posts)} new posts after last saved post.[/green]")
                
                # Save the posts to the database
                if new_posts:
                    self.console.print(f"[blue]--Saving {len(new_posts)} posts to database...[/blue]")
                    await self.truth_service.save_truths(new_posts)
                    self.console.print("[green]Posts saved to database![/green]")
                else:
                    self.console.print("[yellow]No posts collected.[/yellow]")
                
                return fetched_posts
                
        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            self.console.print(f"[red]Scraping failed: {e}[/red]")
            return []

    async def _run_browser_session(self, playwright, start_url):
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )

        chrome = playwright.chromium
        browser = await chrome.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        try:
            context = await browser.new_context(
                user_agent=user_agent,
                viewport={"width": 1280, "height": 720},
                locale="en-US"
            )
            page = await context.new_page()
            
            # Create response handler instance
            handler = TruthSocialResponseHandler(self)
            
            # Set up response listener
            page.on("response", lambda response: asyncio.create_task(handler.check_response(response)))
            
            await page.goto(start_url, wait_until="domcontentloaded")
            self.console.print("🔄 Loading page...")
            await page.wait_for_load_state("networkidle")
            await asyncio.sleep(5)  
            
            # Handle cookie consent if present
            await self._handle_cookie_consent(page)
            
            # Wait for posts to load
            await page.wait_for_selector('[data-testid="status"]', timeout=10000)
            # Additional wait to ensure all posts are loaded
            await asyncio.sleep(5) 
            
            # Scroll to load more posts
            for i in range(1, self.scroll_iterations + 1):
                self.console.print(f"[yellow]Scrolling {i}/{self.scroll_iterations} to load more posts...[/yellow]")
                await page.mouse.wheel(0, 800) 
                await asyncio.sleep(2) 
                
            # Wait for a few seconds to ensure all posts are loaded
            await asyncio.sleep(5)
            self.console.print("[green]Scraping completed![/green]")
            
            return handler.collected_posts
            
        finally:
            await browser.close()
            self.console.print("[blue]Browser closed.[/blue]")

    async def _handle_cookie_consent(self, page):
        try:
            accept_button = page.get_by_role("button", name="Accept")
            is_visible = await accept_button.is_visible(timeout=3000)
            if is_visible:
                await accept_button.click()
                self.console.print("[blue]🍪 Handled cookie consent[/blue]")
        except:
            pass 

    async def run_once(self):
        self.console.print(f"[cyan]📅 Scheduled scrape started at {datetime.now()}[/cyan]")
        posts = await self.scrape_posts()
        self.console.print(f"[cyan]📅 Scheduled scrape completed. Collected {len(posts)} posts.[/cyan]")
        return posts