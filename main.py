from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import pymongo
from datetime import datetime, timedelta
import os
from typing import List, Dict, Any
import json
from bson import ObjectId
import requests
import asyncio

app = FastAPI(title="Adaptive Market Strategy Agent API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGODB_URI = os.getenv('MONGODB_URI', 'your_connection_string_here')
try:
    client = pymongo.MongoClient(MONGODB_URI)
    db = client.adaptive_market_db
    # Test connection
    client.admin.command('ping')
    print("✅ MongoDB connection successful")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    client = None
    db = None

# Initialize news fetcher (optional)
NEWS_API_KEY = os.getenv('NEWS_API_KEY', 'demo')

# Sample news data for when news fetcher fails
SAMPLE_NEWS_EVENTS = [
    {
        "title": "Markets Show Momentum as Tech Stocks Rally",
        "category": "market_analysis",
        "sentiment_score": 0.75,
        "impact_level": "high",
        "published_at": datetime.now() - timedelta(hours=2),
        "description": "Technology stocks continue upward trend with strong volume confirmation, creating momentum opportunities for traders."
    },
    {
        "title": "Fed Officials Signal Dovish Stance on Interest Rates",
        "category": "monetary_policy", 
        "sentiment_score": 0.65,
        "impact_level": "high",
        "published_at": datetime.now() - timedelta(hours=4),
        "description": "Recent comments from Federal Reserve officials suggest continued accommodative monetary policy, supporting market sentiment."
    },
    {
        "title": "Earnings Season Drives Selective Trading Opportunities",
        "category": "earnings",
        "sentiment_score": 0.2,
        "impact_level": "medium",
        "published_at": datetime.now() - timedelta(hours=6),
        "description": "Mixed earnings results across sectors creating trading opportunities as markets digest corporate performance data."
    },
    {
        "title": "Technical Analysis Points to Range-Bound Trading",
        "category": "technical_analysis",
        "sentiment_score": 0.1,
        "impact_level": "medium", 
        "published_at": datetime.now() - timedelta(hours=8),
        "description": "Market indices showing consolidation patterns with key support and resistance levels holding firm."
    }
]

# ETF explanations
ETF_EXPLANATIONS = {
    "SPY": {
        "name": "SPDR S&P 500 ETF",
        "tracks": "S&P 500 Index", 
        "simple_description": "500 biggest US companies",
        "icon": "🏢"
    },
    "QQQ": {
        "name": "Invesco QQQ ETF",
        "tracks": "NASDAQ 100 Index",
        "simple_description": "Top 100 tech companies", 
        "icon": "💻"
    },
    "IWM": {
        "name": "iShares Russell 2000 ETF",
        "tracks": "Russell 2000 Index",
        "simple_description": "2000 smaller US companies",
        "icon": "🏭"
    },
    "DIA": {
        "name": "SPDR Dow Jones ETF", 
        "tracks": "Dow Jones Index",
        "simple_description": "30 largest US companies",
        "icon": "🏦"
    }
}

# Market regime explanations
MARKET_REGIME_EXPLANATIONS = {
    "range_bound": {
        "simple": "Markets moving sideways, no clear direction",
        "technical": "Price oscillating between support and resistance levels, trend strength < 5%, normal volatility (VIX < 25)",
        "strategy_fit": "Good for mean reversion and range trading strategies"
    },
    "trending": {
        "simple": "Markets moving in a clear direction",
        "technical": "Strong trend confirmed, trend strength > 5%, sustained momentum with volume confirmation",
        "strategy_fit": "Ideal for momentum and trend following strategies"
    },
    "high_volatility": {
        "simple": "Markets making big swings up and down", 
        "technical": "VIX > 25, daily price changes > 2%, elevated options activity, news-driven movements",
        "strategy_fit": "Suitable for volatility trading and shorter timeframes"
    }
}

# Strategy simple descriptions
STRATEGY_DESCRIPTIONS = {
    "Trend Following Strategy": {
        "simple": "Buy rising stocks, sell falling",
        "seven_word": "Follow market direction with momentum",
        "technical": "Systematic approach following established trends with volume confirmation"
    },
    "Mean Reversion Strategy": {
        "simple": "Buy oversold, sell overbought",
        "seven_word": "Trade against temporary price extremes",
        "technical": "Contrarian approach targeting temporary price deviations from mean"
    },
    "Momentum Trading": {
        "simple": "Buy stocks moving up fast",
        "seven_word": "Ride strong price movements with volume", 
        "technical": "Capitalize on accelerating price movements with volume confirmation"
    },
    "Breakout Strategy": {
        "simple": "Buy stocks breaking resistance levels",
        "seven_word": "Trade stocks breaking key price barriers",
        "technical": "Enter positions on volume-confirmed breaks of key technical levels"
    }
}

# Enhanced sample stock data for screener
SAMPLE_STOCKS = {
    "momentum": [
        {"symbol": "GOOGL", "score": 17.93, "monthly_return": "12.17%", "volume_ratio": 1.35, "rsi": 68.2, "trend_strength": "Strong"},
        {"symbol": "MSFT", "score": 15.84, "monthly_return": "8.45%", "volume_ratio": 1.28, "rsi": 65.4, "trend_strength": "Strong"},
        {"symbol": "AAPL", "score": 14.72, "monthly_return": "6.23%", "volume_ratio": 1.22, "rsi": 62.8, "trend_strength": "Moderate"},
        {"symbol": "NVDA", "score": 13.58, "monthly_return": "9.87%", "volume_ratio": 1.45, "rsi": 71.3, "trend_strength": "Strong"},
        {"symbol": "AMZN", "score": 12.91, "monthly_return": "5.44%", "volume_ratio": 1.18, "rsi": 59.7, "trend_strength": "Moderate"},
        {"symbol": "META", "score": 11.76, "monthly_return": "7.92%", "volume_ratio": 1.31, "rsi": 66.1, "trend_strength": "Strong"},
        {"symbol": "TSLA", "score": 10.83, "monthly_return": "4.56%", "volume_ratio": 1.52, "rsi": 58.9, "trend_strength": "Moderate"},
        {"symbol": "NFLX", "score": 9.95, "monthly_return": "6.78%", "volume_ratio": 1.25, "rsi": 61.4, "trend_strength": "Moderate"},
        {"symbol": "CRM", "score": 9.42, "monthly_return": "5.23%", "volume_ratio": 1.19, "rsi": 57.6, "trend_strength": "Weak"},
        {"symbol": "AMD", "score": 8.87, "monthly_return": "8.91%", "volume_ratio": 1.41, "rsi": 69.8, "trend_strength": "Strong"},
        {"symbol": "ADBE", "score": 8.34, "monthly_return": "4.17%", "volume_ratio": 1.14, "rsi": 55.2, "trend_strength": "Weak"}
    ],
    "mean_reversion": [
        {"symbol": "META", "score": 11.45, "oversold_level": "Extreme", "rsi": 28.4, "deviation_pct": "-8.2%", "support_level": "$485.20"},
        {"symbol": "PYPL", "score": 10.23, "oversold_level": "High", "rsi": 31.7, "deviation_pct": "-6.8%", "support_level": "$58.45"},
        {"symbol": "SNAP", "score": 9.67, "oversold_level": "Extreme", "rsi": 25.9, "deviation_pct": "-9.1%", "support_level": "$9.85"},
        {"symbol": "UBER", "score": 8.95, "oversold_level": "Moderate", "rsi": 33.2, "deviation_pct": "-5.4%", "support_level": "$68.90"},
        {"symbol": "ROKU", "score": 8.42, "oversold_level": "High", "rsi": 27.6, "deviation_pct": "-7.7%", "support_level": "$45.30"},
        {"symbol": "ZM", "score": 7.89, "oversold_level": "High", "rsi": 29.8, "deviation_pct": "-6.3%", "support_level": "$67.15"},
        {"symbol": "DOCU", "score": 7.34, "oversold_level": "Moderate", "rsi": 32.1, "deviation_pct": "-5.9%", "support_level": "$52.40"},
        {"symbol": "SQ", "score": 6.78, "oversold_level": "High", "rsi": 30.5, "deviation_pct": "-6.6%", "support_level": "$58.75"}
    ],
    "breakout": [
        {"symbol": "TSLA", "score": 10.23, "resistance_level": "$185.50", "distance_to_breakout": "1.2%", "volume_surge": "67%", "pattern": "Bull Flag"},
        {"symbol": "COIN", "score": 9.45, "resistance_level": "$95.80", "distance_to_breakout": "0.8%", "volume_surge": "84%", "pattern": "Ascending Triangle"},
        {"symbol": "PLTR", "score": 8.76, "resistance_level": "$18.45", "distance_to_breakout": "1.5%", "volume_surge": "52%", "pattern": "Rectangle"},
        {"symbol": "RIVN", "score": 8.12, "resistance_level": "$12.75", "distance_to_breakout": "2.1%", "volume_surge": "73%", "pattern": "Cup & Handle"},
        {"symbol": "HOOD", "score": 7.58, "resistance_level": "$14.20", "distance_to_breakout": "1.8%", "volume_surge": "41%", "pattern": "Symmetrical Triangle"},
        {"symbol": "SOFI", "score": 6.94, "resistance_level": "$8.85", "distance_to_breakout": "1.3%", "volume_surge": "29%", "pattern": "Pennant"}
    ],
    "value": [
        {"symbol": "JPM", "score": 18.67, "pe_ratio": 12.4, "pb_ratio": 1.3, "dividend_yield": "2.8%", "peg_ratio": 0.95},
        {"symbol": "BRK.B", "score": 17.23, "pe_ratio": 15.6, "pb_ratio": 1.4, "dividend_yield": "0.0%", "peg_ratio": 1.1},
        {"symbol": "WFC", "score": 16.45, "pe_ratio": 11.8, "pb_ratio": 1.1, "dividend_yield": "3.2%", "peg_ratio": 0.89},
        {"symbol": "BAC", "score": 15.89, "pe_ratio": 13.2, "pb_ratio": 1.2, "dividend_yield": "2.5%", "peg_ratio": 1.02},
        {"symbol": "XOM", "score": 15.34, "pe_ratio": 14.7, "pb_ratio": 1.8, "dividend_yield": "5.4%", "peg_ratio": 0.76},
        {"symbol": "CVX", "score": 14.78, "pe_ratio": 13.9, "pb_ratio": 1.6, "dividend_yield": "4.9%", "peg_ratio": 0.82},
        {"symbol": "JNJ", "score": 14.23, "pe_ratio": 16.5, "pb_ratio": 5.2, "dividend_yield": "2.9%", "peg_ratio": 1.15},
        {"symbol": "PG", "score": 13.67, "pe_ratio": 24.8, "pb_ratio": 7.8, "dividend_yield": "2.4%", "peg_ratio": 2.1},
        {"symbol": "KO", "score": 13.12, "pe_ratio": 25.3, "pb_ratio": 9.1, "dividend_yield": "3.1%", "peg_ratio": 2.3},
        {"symbol": "PFE", "score": 12.58, "pe_ratio": 12.9, "pb_ratio": 2.8, "dividend_yield": "4.2%", "peg_ratio": 0.94},
        {"symbol": "T", "score": 12.04, "pe_ratio": 8.7, "pb_ratio": 1.1, "dividend_yield": "6.8%", "peg_ratio": 0.67},
        {"symbol": "VZ", "score": 11.49, "pe_ratio": 9.2, "pb_ratio": 1.3, "dividend_yield": "6.2%", "peg_ratio": 0.71}
    ]
}

# Sample market data for when API fails
SAMPLE_MARKET_DATA = [
    {
        "symbol": "SPY",
        "price": 563.45,
        "change_percent": 0.85,
        "volume": 45230000,
        "indicators": {"rsi": 61.2, "sma_20": 559.80, "sma_50": 548.30},
        "regime_signals": {"trend": "up", "strength": "moderate"},
        "timestamp": datetime.now().isoformat()
    },
    {
        "symbol": "QQQ", 
        "price": 485.67,
        "change_percent": 1.25,
        "volume": 32180000,
        "indicators": {"rsi": 64.8, "sma_20": 481.20, "sma_50": 468.90},
        "regime_signals": {"trend": "up", "strength": "strong"},
        "timestamp": datetime.now().isoformat()
    },
    {
        "symbol": "IWM",
        "price": 225.89,
        "change_percent": -0.45,
        "volume": 28450000,
        "indicators": {"rsi": 48.3, "sma_20": 227.10, "sma_50": 229.60},
        "regime_signals": {"trend": "down", "strength": "weak"},
        "timestamp": datetime.now().isoformat()
    },
    {
        "symbol": "DIA",
        "price": 442.12,
        "change_percent": 0.65,
        "volume": 15670000,
        "indicators": {"rsi": 58.7, "sma_20": 439.85, "sma_50": 435.20},
        "regime_signals": {"trend": "up", "strength": "moderate"},
        "timestamp": datetime.now().isoformat()
    }
]

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the main dashboard"""
    return FileResponse('static/index.html')

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "mongodb_connected": db is not None,
        "sample_strategies": list(SAMPLE_STOCKS.keys())
    }

async def fetch_real_news_direct():
    """Fetch real news directly from NewsAPI"""
    api_key = os.getenv('NEWS_API_KEY')
    if not api_key or api_key == 'demo':
        print("❌ No NewsAPI key available")
        return []
    
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': 'stock market OR finance OR trading OR nasdaq OR dow jones',
            'apiKey': api_key,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 4,
            'from': (datetime.now() - timedelta(hours=24)).strftime('%Y-%m-%d')
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            articles = []
            
            for article in data.get('articles', [])[:4]:
                if article.get('title') and article.get('description'):
                    # Simple sentiment analysis based on keywords
                    title_desc = (article['title'] + ' ' + article.get('description', '')).lower()
                    
                    if any(word in title_desc for word in ['surge', 'rise', 'gain', 'up', 'growth', 'bull', 'rally']):
                        sentiment = 0.7
                        impact = 'high' if any(word in title_desc for word in ['surge', 'rally']) else 'medium'
                    elif any(word in title_desc for word in ['drop', 'fall', 'decline', 'down', 'bear', 'crash', 'plunge']):
                        sentiment = -0.5
                        impact = 'high' if any(word in title_desc for word in ['crash', 'plunge']) else 'medium'
                    else:
                        sentiment = 0.1
                        impact = 'medium'
                    
                    # Categorize news
                    if any(word in title_desc for word in ['earnings', 'revenue', 'profit', 'quarterly']):
                        category = 'earnings'
                    elif any(word in title_desc for word in ['fed', 'interest', 'monetary', 'policy', 'rate']):
                        category = 'monetary_policy'
                    elif any(word in title_desc for word in ['crypto', 'bitcoin', 'ethereum']):
                        category = 'crypto'
                    elif any(word in title_desc for word in ['tech', 'technology', 'ai', 'semiconductor']):
                        category = 'technology'
                    else:
                        category = 'market_analysis'
                    
                    # Clean up title and description
                    title = article['title']
                    if len(title) > 100:
                        title = title[:97] + '...'
                    
                    description = article.get('description', 'Financial market news and analysis.')
                    if len(description) > 200:
                        description = description[:197] + '...'
                    
                    articles.append({
                        'title': title,
                        'description': description,
                        'category': category,
                        'sentiment_score': sentiment,
                        'impact_level': impact,
                        'published_at': article.get('publishedAt', datetime.now().isoformat())
                    })
            
            print(f"✅ Fetched {len(articles)} real news articles from NewsAPI")
            return articles
            
        elif response.status_code == 429:
            print("⚠️ NewsAPI rate limit exceeded")
        elif response.status_code == 401:
            print("❌ NewsAPI authentication failed - check API key")
        else:
            print(f"❌ NewsAPI error: {response.status_code} - {response.text}")
            
    except requests.exceptions.Timeout:
        print("⏰ NewsAPI request timed out")
    except requests.exceptions.RequestException as e:
        print(f"❌ NewsAPI request error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error fetching news: {e}")
    
    return []

@app.get("/api/current-analysis")
async def get_current_analysis():
    """Get the latest market analysis and strategy recommendation"""
    try:
        # Get latest market conditions
        if db:
            latest_market = db.market_conditions.find().sort("timestamp", -1).limit(4)
            market_data = list(latest_market)
            
            # Get latest strategy recommendation
            latest_strategy = db.strategies.find_one(sort=[("timestamp", -1)])
        else:
            market_data = []
            latest_strategy = None

        # If no DB data, use sample data
        if not market_data:
            print("📊 Using sample market data")
            market_data = SAMPLE_MARKET_DATA
        
        # Always fetch fresh real news for demo
        print("🔄 Fetching real-time financial news...")
        recent_events = await fetch_real_news_direct()

        # If direct fetch fails, try database
        if not recent_events and db:
            print("📊 Checking database for stored news...")
            db_events = list(db.events.find().sort("published_at", -1).limit(5))
            if db_events:
                recent_events = []
                for event in db_events:
                    recent_events.append({
                        'title': event.get('title', ''),
                        'description': event.get('description', ''),
                        'category': event.get('category', 'market_analysis'),
                        'sentiment_score': event.get('sentiment_score', 0),
                        'impact_level': event.get('impact_level', 'medium'),
                        'published_at': event.get('published_at', datetime.now()).isoformat() if hasattr(event.get('published_at', datetime.now()), 'isoformat') else str(event.get('published_at', datetime.now()))
                    })

        # If still no events, use sample data as last resort
        if not recent_events:
            print("📰 Using sample news events for demo")
            recent_events = SAMPLE_NEWS_EVENTS
        
        # Calculate overall market regime
        if market_data:
            regime_signals = [item.get('regime_signals', {}) for item in market_data]
            trend_signals = [r.get('trend', 'neutral') for r in regime_signals]
            
            # Determine overall regime
            strong_trends = sum(1 for t in trend_signals if 'strong' in str(t))
            if strong_trends >= 2:
                overall_regime = "trending"
            else:
                overall_regime = "range_bound"
        else:
            overall_regime = "range_bound"
        
        # Get strategy name for descriptions
        strategy_name = latest_strategy.get('primary_strategy', {}).get('name', 'Trend Following Strategy') if latest_strategy else 'Trend Following Strategy'
        strategy_desc = STRATEGY_DESCRIPTIONS.get(strategy_name, STRATEGY_DESCRIPTIONS['Trend Following Strategy'])
        
        return {
            "market_regime": {
                "type": overall_regime,
                "confidence": latest_strategy.get('market_analysis', {}).get('confidence', 0.75) if latest_strategy else 0.75,
                "last_updated": market_data[0]['timestamp'] if market_data else datetime.now().isoformat(),
                "explanation": MARKET_REGIME_EXPLANATIONS.get(overall_regime, MARKET_REGIME_EXPLANATIONS['range_bound'])
            },
            "strategy_recommendation": {
                "name": strategy_name,
                "confidence": latest_strategy.get('primary_strategy', {}).get('confidence_score', 0.74) if latest_strategy else 0.74,
                "risk_level": latest_strategy.get('primary_strategy', {}).get('risk_level', 'medium') if latest_strategy else 'medium',
                "timeframe": latest_strategy.get('primary_strategy', {}).get('timeframe', '2-4 weeks') if latest_strategy else '2-4 weeks',
                "reasoning": latest_strategy.get('reasoning', 'Market analysis indicates favorable conditions for this strategy') if latest_strategy else 'Range-bound market showing trend following opportunities',
                "simple_description": strategy_desc["simple"],
                "seven_word_description": strategy_desc["seven_word"],
                "technical_description": strategy_desc["technical"]
            },
            "market_data": [
                {
                    "symbol": item['symbol'],
                    "price": item['price'],
                    "change_percent": item['change_percent'],
                    "volume": item['volume'],
                    "rsi": item['indicators']['rsi'],
                    "trend": item['regime_signals']['trend'],
                    # Add ETF explanations
                    "explanation": ETF_EXPLANATIONS.get(item['symbol'], {
                        "name": f"{item['symbol']} ETF",
                        "tracks": "Market Index",
                        "simple_description": "Market tracking fund",
                        "icon": "📊"
                    })
                } for item in market_data[:4]
            ],
            "recent_events": [
                {
                    "title": event.get('title', event.get('title')),
                    "category": event.get('category', 'market_analysis'),
                    "sentiment_score": event.get('sentiment_score', 0),
                    "impact_level": event.get('impact_level', 'medium'),
                    "published_at": event.get('published_at', datetime.now()).isoformat() if hasattr(event.get('published_at', datetime.now()), 'isoformat') else str(event.get('published_at', datetime.now())),
                    "description": event.get('description', 'Market news and analysis')
                } for event in recent_events[:5]
            ],
            "regime_explanations": MARKET_REGIME_EXPLANATIONS,
            "status": "enhanced_with_real_news"
        }
    except Exception as e:
        print(f"Error in current analysis: {str(e)}")
        # Return sample data if everything fails
        return {
            "market_regime": {
                "type": "range_bound",
                "confidence": 0.75,
                "last_updated": datetime.now().isoformat(),
                "explanation": MARKET_REGIME_EXPLANATIONS["range_bound"]
            },
            "strategy_recommendation": {
                "name": "Trend Following Strategy",
                "confidence": 0.74,
                "risk_level": "medium",
                "timeframe": "2-4 weeks", 
                "reasoning": "Sample data for demo purposes",
                "simple_description": "Buy rising stocks, sell falling",
                "seven_word_description": "Follow market direction with momentum",
                "technical_description": "Systematic approach following established trends"
            },
            "market_data": SAMPLE_MARKET_DATA,
            "recent_events": await fetch_real_news_direct() or SAMPLE_NEWS_EVENTS,
            "regime_explanations": MARKET_REGIME_EXPLANATIONS,
            "status": "demo_mode"
        }

@app.get("/api/stocks/{strategy_type}")
async def get_strategy_stocks(strategy_type: str):
    """Get stocks for a specific strategy with better error handling"""
    
    print(f"🔍 API called for strategy: {strategy_type}")
    
    # Always check if we have sample data for this strategy
    if strategy_type not in SAMPLE_STOCKS:
        print(f"❌ Strategy '{strategy_type}' not found in available strategies")
        return {
            "stocks": [],
            "strategy_type": strategy_type,
            "count": 0,
            "status": "strategy_not_found",
            "message": f"Strategy '{strategy_type}' not available",
            "available_strategies": list(SAMPLE_STOCKS.keys())
        }
    
    try:
        # Try MongoDB first (but expect it to fail in demo)
        if db:
            print(f"📊 Checking MongoDB for {strategy_type} stocks...")
            stocks_cursor = db.stock_analysis.find({"strategy": strategy_type}).sort("score", -1).limit(20)
            stocks = list(stocks_cursor)
            
            if stocks and len(stocks) > 0:
                print(f"✅ Found {len(stocks)} stocks in MongoDB for {strategy_type}")
                # Convert MongoDB documents to proper format
                formatted_stocks = []
                for stock in stocks:
                    stock_dict = dict(stock)
                    # Remove MongoDB ObjectId if present
                    if '_id' in stock_dict:
                        del stock_dict['_id']
                    formatted_stocks.append(stock_dict)
                
                return {
                    "stocks": formatted_stocks,
                    "strategy_type": strategy_type,
                    "count": len(formatted_stocks),
                    "status": "mongodb_data"
                }
            else:
                raise Exception("No stocks found in MongoDB")
        else:
            raise Exception("MongoDB not connected")
            
    except Exception as db_error:
        print(f"📦 MongoDB unavailable ({db_error}), using sample data for {strategy_type}")
        
        # Use sample data as fallback
        strategy_stocks = SAMPLE_STOCKS.get(strategy_type, [])
        print(f"📊 Returning {len(strategy_stocks)} sample stocks for {strategy_type}")
        
        return {
            "stocks": strategy_stocks,
            "strategy_type": strategy_type,
            "count": len(strategy_stocks),
            "status": "sample_data",
            "note": "Demo mode - using sample data"
        }

@app.get("/api/test-stocks")
async def test_sample_stocks():
    """Test endpoint to verify sample stock data"""
    return {
        "available_strategies": list(SAMPLE_STOCKS.keys()),
        "sample_counts": {strategy: len(stocks) for strategy, stocks in SAMPLE_STOCKS.items()},
        "sample_momentum_stocks": SAMPLE_STOCKS["momentum"][:3],  # First 3 for testing
        "mongodb_connected": db is not None,
        "status": "test_successful"
    }

@app.get("/api/market-regime-explanations")
async def get_market_regime_explanations():
    """Get detailed explanations for all market regimes"""
    return {
        "explanations": MARKET_REGIME_EXPLANATIONS,
        "current_regime": "range_bound",  # This would be dynamic based on current analysis
        "status": "success"
    }

@app.get("/api/historical-data/{symbol}")
async def get_historical_data(symbol: str, days: int = 30):
    """Get historical data for a symbol"""
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        # Try to get from your existing data source
        if db:
            historical_data = list(db.historical_data.find({
                "symbol": symbol,
                "date": {"$gte": start_date}
            }).sort("date", 1))
        else:
            historical_data = []
        
        if not historical_data:
            # Generate sample data if no real data available
            sample_data = []
            base_price = 100.0
            for i in range(days):
                date = start_date + timedelta(days=i)
                price = base_price + (i * 0.5) + (i % 7) * 2
                sample_data.append({
                    "date": date.isoformat(),
                    "price": price,
                    "volume": 1000000 + (i * 10000)
                })
            return {"symbol": symbol, "data": sample_data, "status": "sample_data"}
        
        return {"symbol": symbol, "data": historical_data, "status": "success"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Adaptive Market Strategy Agent...")
    print(f"📊 Available strategies: {list(SAMPLE_STOCKS.keys())}")
    print(f"🔗 MongoDB connected: {db is not None}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
