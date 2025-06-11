import requests
from pymongo import MongoClient
from datetime import datetime, timedelta
import time
import re
from typing import Dict, List
import json

class NewsDataFetcher:
    def __init__(self, mongo_connection_string: str, newsapi_key: str):
        """
        Initialize the news data fetcher
        
        Args:
            mongo_connection_string: MongoDB Atlas connection string
            newsapi_key: NewsAPI key
        """
        self.newsapi_key = newsapi_key
        self.newsapi_base_url = "https://newsapi.org/v2/everything"
        
        # MongoDB setup
        self.client = MongoClient(mongo_connection_string)
        self.db = self.client['adaptive_market_db']
        self.events = self.db['events']
        
        # Keywords for different event categories
        self.keywords = {
            'fed': ['federal reserve', 'fed', 'interest rate', 'powell', 'fomc', 'monetary policy'],
            'earnings': ['earnings', 'quarterly results', 'eps', 'revenue', 'guidance', 'profit'],
            'economic': ['gdp', 'inflation', 'unemployment', 'jobs report', 'cpi', 'ppi', 'economic data'],
            'geopolitical': ['trade war', 'tariff', 'election', 'regulation', 'policy', 'government'],
            'market': ['market', 'stocks', 'trading', 'dow', 'nasdaq', 's&p', 'spy', 'volatility']
        }
        
        # Sentiment keywords
        self.positive_words = ['up', 'rise', 'gain', 'strong', 'beat', 'exceed', 'positive', 'growth', 'bull']
        self.negative_words = ['down', 'fall', 'drop', 'weak', 'miss', 'decline', 'negative', 'bear', 'crash']
    
    def fetch_financial_news(self, hours_back: int = 24) -> List[Dict]:
        """
        Fetch financial news from NewsAPI
        
        Args:
            hours_back: How many hours back to fetch news
            
        Returns:
            List of news articles
        """
        try:
            # Calculate time range
            to_time = datetime.utcnow()
            from_time = to_time - timedelta(hours=hours_back)
            
            # Search terms for financial news
            search_query = 'stock market OR S&P OR nasdaq OR dow OR fed OR earnings OR inflation'
            
            params = {
                'q': search_query,
                'from': from_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'to': to_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': self.newsapi_key
            }
            
            response = requests.get(self.newsapi_base_url, params=params)
            data = response.json()
            
            if response.status_code == 200 and data.get('status') == 'ok':
                articles = data.get('articles', [])
                print(f"✅ Fetched {len(articles)} news articles")
                return articles
            else:
                print(f"❌ NewsAPI Error: {data.get('message', 'Unknown error')}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching news: {e}")
            return []
    
    def categorize_news(self, article: Dict) -> str:
        """
        Categorize news article based on keywords
        
        Args:
            article: News article dictionary
            
        Returns:
            Category string
        """
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        content = f"{title} {description}"
        
        # Count keyword matches for each category
        category_scores = {}
        for category, keywords in self.keywords.items():
            score = sum(content.count(keyword) for keyword in keywords)
            if score > 0:
                category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            return max(category_scores, key=category_scores.get)
        else:
            return 'general'
    
    def calculate_sentiment_score(self, article: Dict) -> float:
        """
        Calculate basic sentiment score for article
        
        Args:
            article: News article dictionary
            
        Returns:
            Sentiment score between -1 (negative) and 1 (positive)
        """
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        content = f"{title} {description}"
        
        # Count positive and negative words
        positive_count = sum(content.count(word) for word in self.positive_words)
        negative_count = sum(content.count(word) for word in self.negative_words)
        
        # Calculate sentiment score
        total_words = len(content.split())
        if total_words == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / max(total_words / 10, 1)
        
        # Normalize to -1 to 1 range
        return max(-1.0, min(1.0, sentiment))
    
    def assess_impact_level(self, article: Dict, category: str, sentiment: float) -> str:
        """
        Assess the potential market impact of news
        
        Args:
            article: News article dictionary
            category: News category
            sentiment: Sentiment score
            
        Returns:
            Impact level: 'high', 'medium', or 'low'
        """
        title = article.get('title', '').lower()
        source = article.get('source', {}).get('name', '').lower()
        
        # High impact indicators
        high_impact_keywords = ['fed', 'federal reserve', 'interest rate', 'powell', 'fomc', 
                               'earnings beat', 'earnings miss', 'guidance', 'breaking']
        high_impact_sources = ['reuters', 'bloomberg', 'cnbc', 'wall street journal', 'financial times']
        
        # Check for high impact
        has_high_keywords = any(keyword in title for keyword in high_impact_keywords)
        is_major_source = any(src in source for src in high_impact_sources)
        strong_sentiment = abs(sentiment) > 0.3
        
        if (has_high_keywords and is_major_source) or (category == 'fed' and strong_sentiment):
            return 'high'
        elif category in ['earnings', 'economic'] or strong_sentiment:
            return 'medium'
        else:
            return 'low'
    
    def process_article(self, article: Dict) -> Dict:
        """
        Process a single news article
        
        Args:
            article: Raw news article from API
            
        Returns:
            Processed article dictionary
        """
        try:
            # Basic article info
            processed = {
                'title': article.get('title', ''),
                'description': article.get('description', ''),
                'url': article.get('url', ''),
                'source': article.get('source', {}).get('name', ''),
                'published_at': datetime.fromisoformat(article.get('publishedAt', '').replace('Z', '+00:00')),
                'fetched_at': datetime.utcnow()
            }
            
            # AI analysis
            processed['category'] = self.categorize_news(article)
            processed['sentiment_score'] = self.calculate_sentiment_score(article)
            processed['impact_level'] = self.assess_impact_level(
                article, processed['category'], processed['sentiment_score']
            )
            
            # Create unique ID
            processed['_id'] = f"{processed['source']}_{processed['published_at'].strftime('%Y%m%d_%H%M%S')}"
            
            return processed
            
        except Exception as e:
            print(f"❌ Error processing article: {e}")
            return None
    
    def store_news_data(self, processed_article: Dict) -> bool:
        """
        Store processed news article in MongoDB
        
        Args:
            processed_article: Processed article dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Insert or update
            self.events.replace_one(
                {'_id': processed_article['_id']},
                processed_article,
                upsert=True
            )
            
            print(f"✅ Stored: {processed_article['category']} | {processed_article['impact_level']} | {processed_article['title'][:50]}...")
            return True
            
        except Exception as e:
            print(f"❌ Error storing news: {e}")
            return False
    
    def fetch_and_process_news(self, hours_back: int = 24):
        """
        Fetch and process all news articles
        
        Args:
            hours_back: How many hours back to fetch news
        """
        print(f"📰 Fetching financial news from last {hours_back} hours...")
        
        # Fetch raw articles
        articles = self.fetch_financial_news(hours_back)
        
        if not articles:
            print("❌ No articles fetched")
            return
        
        # Process and store each article
        processed_count = 0
        for article in articles:
            processed = self.process_article(article)
            if processed:
                success = self.store_news_data(processed)
                if success:
                    processed_count += 1
        
        print(f"✅ Processed and stored {processed_count} out of {len(articles)} articles")
    
    def get_recent_events_summary(self) -> Dict:
        """
        Get a summary of recent events stored in database
        
        Returns:
            Summary dictionary with event statistics
        """
        try:
            # Get events from last 24 hours
            yesterday = datetime.utcnow() - timedelta(hours=24)
            recent_events = list(self.events.find({
                'fetched_at': {'$gte': yesterday}
            }))
            
            if not recent_events:
                return {'total': 0, 'by_category': {}, 'by_impact': {}}
            
            # Calculate statistics
            summary = {
                'total': len(recent_events),
                'by_category': {},
                'by_impact': {},
                'avg_sentiment': 0,
                'latest_events': []
            }
            
            # Count by category and impact
            for event in recent_events:
                category = event.get('category', 'unknown')
                impact = event.get('impact_level', 'unknown')
                
                summary['by_category'][category] = summary['by_category'].get(category, 0) + 1
                summary['by_impact'][impact] = summary['by_impact'].get(impact, 0) + 1
            
            # Calculate average sentiment
            sentiments = [event.get('sentiment_score', 0) for event in recent_events]
            summary['avg_sentiment'] = sum(sentiments) / len(sentiments) if sentiments else 0
            
            # Get latest high impact events
            high_impact_events = [e for e in recent_events if e.get('impact_level') == 'high']
            summary['latest_events'] = sorted(
                high_impact_events, 
                key=lambda x: x.get('published_at', datetime.min),
                reverse=True
            )[:5]
            
            return summary
            
        except Exception as e:
            print(f"❌ Error getting events summary: {e}")
            return {}
    
    def start_continuous_news_fetching(self, interval_hours: int = 1):
        """
        Start continuous news fetching
        
        Args:
            interval_hours: Hours between news fetches
        """
        print(f"🚀 Starting continuous news fetching every {interval_hours} hour(s)")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.fetch_and_process_news(hours_back=interval_hours + 1)
                
                # Show summary
                summary = self.get_recent_events_summary()
                print(f"\n📊 Recent Events Summary:")
                print(f"   Total: {summary.get('total', 0)} events")
                print(f"   High Impact: {summary.get('by_impact', {}).get('high', 0)}")
                print(f"   Avg Sentiment: {summary.get('avg_sentiment', 0):.2f}")
                
                print(f"\n💤 Sleeping for {interval_hours} hour(s)...")
                time.sleep(interval_hours * 3600)  # Convert hours to seconds
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping news data fetcher")


# Usage example
if __name__ == "__main__":
    # Configuration - Replace with your actual keys
    MONGO_CONNECTION = "mongodb+srv://marketagent:T9QjESNK8lunUoTU@adaptive-market-cluster.aganihz.mongodb.net/"
    NEWSAPI_KEY = "24072d5660c04b3b990736cff17ebeb5"
    
    # Initialize fetcher
    news_fetcher = NewsDataFetcher(MONGO_CONNECTION, NEWSAPI_KEY)
    
    # Test single fetch
    print("🧪 Testing news data fetch...")
    news_fetcher.fetch_and_process_news(hours_back=6)
    
    # Show summary
    summary = news_fetcher.get_recent_events_summary()
    print(f"\n📊 Summary: {summary}")
    
    # Start continuous fetching (uncomment to run continuously)
    # news_fetcher.start_continuous_news_fetching(interval_hours=2)
