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
client = pymongo.MongoClient(MONGODB_URI)
db = client.adaptive_market_db

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the main dashboard"""
    return FileResponse('static/index.html')

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/current-analysis")
async def get_current_analysis():
    """Get the latest market analysis and strategy recommendation"""
    try:
        # Get latest market conditions
        latest_market = db.market_conditions.find().sort("timestamp", -1).limit(4)
        market_data = list(latest_market)
        
        # Get latest strategy recommendation
        latest_strategy = db.strategies.find_one(sort=[("timestamp", -1)])
        
        # Get recent events
        recent_events = list(db.events.find().sort("published_at", -1).limit(5))
        
        # Calculate overall market regime
        if market_data:
            regime_signals = [item.get('regime_signals', {}) for item in market_data]
            trend_signals = [r.get('trend', 'neutral') for r in regime_signals]
            
            # Determine overall regime
            strong_trends = sum(1 for t in trend_signals if 'strong' in t)
            if strong_trends >= 2:
                overall_regime = "trending"
            else:
                overall_regime = "range_bound"
        else:
            overall_regime = "unknown"
        
        return {
            "market_regime": {
                "type": overall_regime,
                "confidence": latest_strategy.get('market_analysis', {}).get('confidence', 0.5) if latest_strategy else 0.5,
                "last_updated": market_data[0]['timestamp'] if market_data else datetime.now().isoformat()
            },
            "strategy_recommendation": {
                "name": latest_strategy.get('primary_strategy', {}).get('name', 'No recommendation') if latest_strategy else 'No recommendation',
                "confidence": latest_strategy.get('primary_strategy', {}).get('confidence_score', 0) if latest_strategy else 0,
                "risk_level": latest_strategy.get('primary_strategy', {}).get('risk_level', 'unknown') if latest_strategy else 'unknown',
                "timeframe": latest_strategy.get('primary_strategy', {}).get('timeframe', 'unknown') if latest_strategy else 'unknown',
                "reasoning": latest_strategy.get('reasoning', 'No reasoning available') if latest_strategy else 'No reasoning available'
            },
            "market_data": [
                {
                    "symbol": item['symbol'],
                    "price": item['price'],
                    "change_percent": item['change_percent'],
                    "volume": item['volume'],
                    "rsi": item['indicators']['rsi'],
                    "trend": item['regime_signals']['trend']
                } for item in market_data[:4]
            ],
            "recent_events": [
                {
                    "title": event['title'],
                    "category": event['category'],
                    "sentiment_score": event['sentiment_score'],
                    "impact_level": event['impact_level'],
                    "published_at": event['published_at']
                } for event in recent_events
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching current analysis: {str(e)}")

@app.get("/api/historical-data/{symbol}")
async def get_historical_data(symbol: str, days: int = 30):
    """Get historical data for a symbol"""
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        historical_data = list(
            db.market_conditions.find({
                "symbol": symbol.upper(),
                "timestamp": {"$gte": start_date}
            }).sort("timestamp", 1).limit(100)
        )
        
        return {
            "symbol": symbol.upper(),
            "data": [
                {
                    "timestamp": item['timestamp'],
                    "price": item['price'],
                    "volume": item['volume'],
                    "rsi": item['indicators']['rsi'],
                    "sma_20": item['indicators']['sma_20']
                } for item in historical_data
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical data: {str(e)}")

@app.get("/api/strategy-history")
async def get_strategy_history(limit: int = 10):
    """Get recent strategy recommendations history"""
    try:
        strategies = list(
            db.strategies.find().sort("timestamp", -1).limit(limit)
        )
        
        return {
            "strategies": [
                {
                    "timestamp": strategy['timestamp'],
                    "strategy_name": strategy.get('primary_strategy', {}).get('name', 'Unknown'),
                    "confidence": strategy.get('primary_strategy', {}).get('confidence_score', 0),
                    "market_regime": strategy.get('market_analysis', {}).get('regime', 'unknown'),
                    "reasoning": strategy.get('reasoning', 'No reasoning provided')[:100] + "..."
                } for strategy in strategies
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching strategy history: {str(e)}")

@app.get("/api/market-stats")
async def get_market_stats():
    """Get overall market statistics"""
    try:
        # Get total data points
        total_market_records = db.market_conditions.count_documents({})
        total_events = db.events.count_documents({})
        total_strategies = db.strategies.count_documents({})
        
        # Get latest timestamp
        latest_market = db.market_conditions.find_one(sort=[("timestamp", -1)])
        last_update = latest_market['timestamp'] if latest_market else None
        
        # Calculate strategy distribution
        pipeline = [
            {"$group": {
                "_id": "$primary_strategy.name",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]
        strategy_dist = list(db.strategies.aggregate(pipeline))
        
        return {
            "total_records": {
                "market_data": total_market_records,
                "events": total_events,
                "strategies": total_strategies
            },
            "last_update": last_update,
            "strategy_distribution": strategy_dist[:5],  # Top 5 strategies
            "system_status": "operational"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market stats: {str(e)}")

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    import pandas as pd
    prices_series = pd.Series(prices)
    deltas = prices_series.diff()
    gain = (deltas.where(deltas > 0, 0)).rolling(window=period).mean()
    loss = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if len(rsi) > 0 else 50

def get_strategy_criteria(strategy_name):
    """Get screening criteria description"""
    criteria = {
        "momentum": {
            "description": "Stocks with strong price momentum and volume confirmation",
            "metrics": ["1-month return > 2%", "RSI between 35-75", "Volume 75% above average"],
            "timeframe": "1-3 months"
        },
        "mean_reversion": {
            "description": "Oversold stocks positioned for bounce back",
            "metrics": ["5-day decline > 1%", "RSI below 45", "Price below 20-day MA"],
            "timeframe": "1-4 weeks"
        },
        "breakout": {
            "description": "Stocks approaching resistance with volume surge",
            "metrics": ["Near 1-month high", "Volume 30% above average", "Technical breakout setup"],
            "timeframe": "1-2 weeks"
        },
        "value": {
            "description": "Fundamentally undervalued dividend-paying stocks",
            "metrics": ["P/E ratio < 25", "P/B ratio < 4", "Dividend yield > 0.5%"],
            "timeframe": "6-18 months"
        }
    }
    return criteria.get(strategy_name.lower(), {})

@app.get("/api/strategy-screener/{strategy_name}")
async def get_strategy_screener(strategy_name: str, limit: int = 50):
    """Get stocks that match a specific strategy criteria"""
    try:
        import yfinance as yf
        import pandas as pd
        
        # Expanded stock universe for better results
        stock_universe = [
            # Technology
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'CRM', 
            'UBER', 'SNOW', 'PLTR', 'SQ', 'PYPL', 'SHOP', 'ADBE', 'ORCL', 'SALESFORCE', 'ZOOM',
            
            # Finance
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'BRK-B', 'V', 'MA',
            
            # Healthcare
            'JNJ', 'PFE', 'UNH', 'ABBV', 'LLY', 'TMO', 'DHR', 'ABT', 'MRK', 'CVS',
            
            # Energy
            'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'PXD', 'MPC', 'VLO', 'OXY', 'KMI',
            
            # Consumer
            'WMT', 'TGT', 'COST', 'HD', 'LOW', 'NKE', 'SBUX', 'MCD', 'DIS', 'KO',
            
            # Industrial
            'BA', 'CAT', 'GE', 'MMM', 'HON', 'UPS', 'RTX', 'LMT', 'NOC', 'GD',
            
            # Communication
            'T', 'VZ', 'CMCSA', 'CHTR', 'TMUS', 'DISH'
        ]
        
        screened_stocks = []
        processed_count = 0
        
        if strategy_name.lower() == "momentum":
            # Relaxed momentum screening criteria
            for symbol in stock_universe:
                if processed_count >= limit:
                    break
                try:
                    stock = yf.Ticker(symbol)
                    hist = stock.history(period="3mo")
                    if len(hist) < 50:
                        continue
                    
                    processed_count += 1
                    
                    # Calculate momentum indicators with relaxed criteria
                    recent_return = (hist['Close'][-1] / hist['Close'][-21] - 1) * 100  # 1-month return
                    rsi = calculate_rsi(hist['Close'], 14)
                    volume_ratio = hist['Volume'][-5:].mean() / hist['Volume'][-21:].mean()
                    
                    # Relaxed momentum criteria: positive return, RSI 45-75, volume > average
                    if recent_return > 2 and 35 < rsi < 75 and volume_ratio > 0.75:
                        screened_stocks.append({
                            "symbol": symbol,
                            "score": round(recent_return + (rsi-45)*0.3 + (volume_ratio-1)*8, 2),
                            "return_1m": round(recent_return, 2),
                            "rsi": round(rsi, 1),
                            "volume_ratio": round(volume_ratio, 2),
                            "criteria": "Strong momentum with volume confirmation"
                        })
                except Exception as e:
                    continue
        
        elif strategy_name.lower() == "mean_reversion":
            # Relaxed mean reversion screening criteria
            for symbol in stock_universe:
                if processed_count >= limit:
                    break
                try:
                    stock = yf.Ticker(symbol)
                    hist = stock.history(period="3mo")
                    if len(hist) < 50:
                        continue
                    
                    processed_count += 1
                    
                    recent_return = (hist['Close'][-1] / hist['Close'][-5] - 1) * 100  # 5-day return
                    rsi = calculate_rsi(hist['Close'], 14)
                    distance_from_ma = ((hist['Close'][-1] / hist['Close'][-20:].mean()) - 1) * 100
                    
                    # Relaxed mean reversion criteria
                    if recent_return < -1 and rsi < 45 and distance_from_ma < -2:
                        screened_stocks.append({
                            "symbol": symbol,
                            "score": round(abs(recent_return) + (40-rsi)*0.5 + abs(distance_from_ma)*0.3, 2),
                            "return_5d": round(recent_return, 2),
                            "rsi": round(rsi, 1),
                            "ma_distance": round(distance_from_ma, 2),
                            "criteria": "Oversold condition for mean reversion"
                        })
                except Exception as e:
                    continue
        
        elif strategy_name.lower() == "breakout":
            # Relaxed breakout screening criteria
            for symbol in stock_universe:
                if processed_count >= limit:
                    break
                try:
                    stock = yf.Ticker(symbol)
                    hist = stock.history(period="3mo")
                    if len(hist) < 50:
                        continue
                    
                    processed_count += 1
                    
                    current_price = hist['Close'][-1]
                    resistance_level = hist['High'][-21:].max()  # 1-month high
                    volume_ratio = hist['Volume'][-1] / hist['Volume'][-21:].mean()
                    price_vs_resistance = (current_price / resistance_level - 1) * 100
                    
                    # Relaxed breakout criteria
                    if price_vs_resistance > -8 and volume_ratio > 0.8:
                        screened_stocks.append({
                            "symbol": symbol,
                            "score": round(volume_ratio * 8 + (5 + price_vs_resistance) * 3, 2),
                            "price_vs_resistance": round(price_vs_resistance, 2),
                            "volume_ratio": round(volume_ratio, 2),
                            "resistance_level": round(resistance_level, 2),
                            "criteria": "Approaching breakout with volume"
                        })
                except Exception as e:
                    continue
        
        elif strategy_name.lower() == "value":
            # Relaxed value screening criteria
            for symbol in stock_universe:
                if processed_count >= limit:
                    break
                try:
                    stock = yf.Ticker(symbol)
                    info = stock.info
                    
                    processed_count += 1
                    
                    pe_ratio = info.get('trailingPE', 999)
                    pb_ratio = info.get('priceToBook', 999)
                    div_yield = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
                    
                    # Relaxed value criteria
                    if pe_ratio < 30 and pb_ratio < 5 and div_yield > 0.1:
                        screened_stocks.append({
                            "symbol": symbol,
                            "score": round((25-pe_ratio) + (4-pb_ratio)*3 + div_yield*2, 2),
                            "pe_ratio": round(pe_ratio, 1),
                            "pb_ratio": round(pb_ratio, 2),
                            "dividend_yield": round(div_yield, 2),
                            "criteria": "Undervalued with dividend income"
                        })
                except Exception as e:
                    continue
        
        else:
            return {"error": f"Strategy '{strategy_name}' not supported", "supported": ["momentum", "mean_reversion", "breakout", "value"]}
        
        # Sort by score and return top results
        screened_stocks.sort(key=lambda x: x['score'], reverse=True)
        
        return {
            "strategy": strategy_name,
            "total_screened": processed_count,
            "matches_found": len(screened_stocks),
            "top_picks": screened_stocks[:15],  # Show top 15 results
            "criteria_used": get_strategy_criteria(strategy_name)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in stock screening: {str(e)}")

@app.get("/api/available-strategies")
async def get_available_strategies():
    """Get list of available screening strategies"""
    return {
        "strategies": [
            {
                "name": "momentum",
                "display_name": "Momentum Strategy",
                "description": "Stocks with strong price momentum and volume confirmation",
                "risk_level": "medium-high",
                "criteria": ["1-month return > 3%", "RSI between 45-75", "Volume 15% above average"]
            },
            {
                "name": "mean_reversion", 
                "display_name": "Mean Reversion Strategy",
                "description": "Oversold stocks positioned for bounce back",
                "risk_level": "medium",
                "criteria": ["5-day decline > 2%", "RSI below 40", "Price below 20-day MA"]
            },
            {
                "name": "breakout",
                "display_name": "Breakout Strategy", 
                "description": "Stocks approaching resistance with volume surge",
                "risk_level": "high",
                "criteria": ["Near 1-month high", "Volume 30% above average", "Technical breakout setup"]
            },
            {
                "name": "value",
                "display_name": "Value Strategy",
                "description": "Fundamentally undervalued dividend-paying stocks", 
                "risk_level": "low",
                "criteria": ["P/E ratio < 25", "P/B ratio < 4", "Dividend yield > 0.5%"]
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
