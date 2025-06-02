from datetime import datetime, timedelta, timezone
import random
from typing import List, Dict
from faker import Faker

fake = Faker()

class MockTruthPostGenerator:
    def __init__(self):
        self.sample_contents = [
            "Just had a great meeting with incredible business leaders! 🇺🇸",
            "The fake news media is at it again. Sad!",
            "Our country is doing better than ever before!",
            "Thank you to all the incredible supporters!",
            "MAKE AMERICA GREAT AGAIN!",
            "The radical left Democrats are destroying our country!",
            "We will never give up fighting for America!",
            "The best is yet to come! 🇺🇸🦅",
            "Crooked politicians are being exposed!",
            "America First, always!",
            "The truth will always prevail!",
            "Our economy is the strongest it's ever been!",
            "We're bringing jobs back to America!",
            "The swamp is being drained!",
            "Patriots are fighting back!",
        ]
        
        self.media_urls = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.png",
            "https://example.com/video1.mp4",
            "https://example.com/image3.jpg",
        ]
    
    def generate_mock_posts(self, count: int = 1, start_time: datetime = None) -> List[Dict]:
        """Generate mock Truth Social posts"""
        if start_time is None:
            start_time = datetime.now()
        
        posts = []
        for i in range(count):
            # Generate timestamp that's newer than start_time
            post_time = start_time + timedelta(minutes=random.randint(1, 30))
            has_media = random.choice([True, False, False])  # 33% chance
            
            post = {
                "id": random.randint(10**17, 10**18 - 1),
                "content": random.choice(self.sample_contents),
                "timestamp": post_time.astimezone(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
                "url": f"https://truthsocial.com/@realDonaldTrump/posts/{random.randint(100000, 999999)}",
            }
            
            if has_media:
                post["media_urls"] = [random.choice(self.media_urls)]
            
            posts.append(post)
            
        return posts
    
    def generate_realistic_batch(self, batch_size: int = 3) -> List[Dict]:
        """Generate a realistic batch of posts with varying timestamps"""
        now = datetime.now()
        posts = []
        
        for i in range(batch_size):
            # Spread posts over the last few minutes
            minutes_ago = random.randint(1, 10)
            post_time = now - timedelta(minutes=minutes_ago)
            
            post = {
                "id": f"mock_{int(post_time.timestamp())}_{i}",
                "content": random.choice(self.sample_contents),
                "timestamp": post_time.isoformat() + "Z",
                "url": f"https://truthsocial.com/@realDonaldTrump/posts/mock_{int(post_time.timestamp())}",
            }
            
            # 30% chance of having media
            if random.random() < 0.3:
                post["media_urls"] = [random.choice(self.media_urls)]
            
            posts.append(post)
        
        posts.sort(key=lambda x: x["timestamp"], reverse=True)
        return posts