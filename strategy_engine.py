#!/usr/bin/env python3

import pymongo
from datetime import datetime, timedelta
import os
import time

def generate_strategy_reasoning(strategy_name, market_data, market_regime, events):
    """Generate intelligent reasoning for strategy recommendations"""
    
    if not market_data:
        return "No market data available for analysis."
    
    # Calculate market metrics
    avg_rsi = sum(item.get('indicators', {}).get('rsi', 50) for item in market_data) / len(market_data)
    avg_change = sum(item.get('change_percent', 0) for item in market_data) / len(market_data)
    strong_trends = sum(1 for item in market_data if 'strong' in item.get('regime_signals', {}).get('trend', ''))
    
    # Build reasoning based on strategy type
    reasoning_parts = []
    
    if strategy_name == "Mean Reversion Strategy":
        reasoning_parts.append(f"Market showing {'strong' if avg_change > 1 else 'moderate'} momentum with average gain of {avg_change:.1f}% across major ETFs.")
        reasoning_parts.append(f"RSI levels averaging {avg_rsi:.1f} {'suggest overbought conditions' if avg_rsi > 60 else 'indicate room for mean reversion' if avg_rsi > 50 else 'show oversold potential'}.")
        reasoning_parts.append("Mean reversion strategy targets pullbacks after strong moves, capitalizing on temporary corrections.")
        
    elif strategy_name == "Momentum Breakout Strategy":
        reasoning_parts.append(f"Strong directional momentum confirmed with {strong_trends}/{len(market_data)} ETFs showing strong trends.")
        reasoning_parts.append(f"Average RSI of {avg_rsi:.1f} supports continued momentum with room for further upside.")
        reasoning_parts.append("Breakout strategy recommended to ride established trends with proper risk management.")
        
    elif strategy_name == "Volatility Trading Strategy":
        reasoning_parts.append(f"Market volatility detected with mixed signals across {len(market_data)} major indices.")
        reasoning_parts.append("Volatility trading strategy can profit from price swings in uncertain conditions.")
        reasoning_parts.append("Focus on options strategies and short-term tactical trades.")
        
    elif strategy_name == "Trend Following Strategy":
        reasoning_parts.append(f"Established trend confirmed with {strong_trends} of {len(market_data)} indices showing strong directional bias.")
        reasoning_parts.append("Trend following strategy aligns with market momentum for sustained moves.")
        reasoning_parts.append("Entry on pullbacks to moving averages recommended for optimal risk/reward.")
        
    elif strategy_name == "Defensive Strategy":
        reasoning_parts.append("Market uncertainty and mixed economic signals suggest defensive positioning.")
        reasoning_parts.append("Focus on dividend-paying stocks, utilities, and consumer staples for stability.")
        reasoning_parts.append("Capital preservation takes priority over aggressive growth in current environment.")
        
    elif strategy_name == "Event-Driven Strategy":
        event_count = len(events) if events else 0
        reasoning_parts.append(f"{'High' if event_count > 3 else 'Moderate'} event activity with {event_count} recent catalysts identified.")
        reasoning_parts.append("Event-driven strategy targets price movements around earnings, Fed announcements, and economic data.")
        reasoning_parts.append("Focus on stocks with upcoming catalysts and clear directional bias.")
    
    # Add market regime context
    if market_regime:
        regime_type = market_regime.get('regime', 'unknown')
        confidence = market_regime.get('confidence', 0)
        reasoning_parts.append(f"Current market regime classified as '{regime_type}' with {confidence*100:.0f}% confidence.")
    
    return " ".join(reasoning_parts)

def analyze_market_conditions(db):
    """Analyze current market conditions and generate strategy recommendations"""
    
    # Get latest market data (last 4 records for major ETFs)
    latest_market = list(db.market_conditions.find().sort("timestamp", -1).limit(4))
    
    if not latest_market:
        print("No market data found")
        return None
    
    # Get recent events
    recent_events = list(db.events.find().sort("published_at", -1).limit(5))
    
    # Analyze market regime
    regime_signals = [item.get('regime_signals', {}) for item in latest_market]
    trend_signals = [r.get('trend', 'neutral') for r in regime_signals]
    volume_signals = [r.get('volume', 'normal') for r in regime_signals]
    
    # Determine overall market regime
    strong_trends = sum(1 for t in trend_signals if 'strong' in t)
    up_trends = sum(1 for t in trend_signals if 'up' in t)
    high_volume = sum(1 for v in volume_signals if v == 'high')
    
    if strong_trends >= 2:
        regime = "trending"
        regime_confidence = 0.8 + (strong_trends * 0.05)
    elif up_trends >= 2:
        regime = "trending"
        regime_confidence = 0.6 + (up_trends * 0.05)
    else:
        regime = "range_bound"
        regime_confidence = 0.7
    
    # Cap confidence at 1.0
    regime_confidence = min(regime_confidence, 1.0)
    
    # Calculate market metrics for strategy selection
    prices = [item['price'] for item in latest_market]
    changes = [item['change_percent'] for item in latest_market]
    rsi_values = [item['indicators']['rsi'] for item in latest_market]
    
    avg_change = sum(changes) / len(changes)
    avg_rsi = sum(rsi_values) / len(rsi_values)
    volatility = max(changes) - min(changes)
    
    # Strategy selection logic
    strategies = []
    
    # Mean Reversion Strategy
    if avg_rsi > 55 and avg_change > 0.8:
        confidence = 0.3 + (avg_rsi - 55) * 0.01 + (avg_change - 0.8) * 0.1
        strategies.append({
            "name": "Mean Reversion Strategy",
            "confidence_score": min(confidence, 0.8),
            "risk_level": "low",
            "timeframe": "3-7 days"
        })
    
    # Momentum Breakout Strategy
    if strong_trends >= 2 and avg_change > 0.5:
        confidence = 0.4 + (strong_trends * 0.1) + (avg_change * 0.05)
        strategies.append({
            "name": "Momentum Breakout Strategy",
            "confidence_score": min(confidence, 0.9),
            "risk_level": "medium",
            "timeframe": "1-3 weeks"
        })
    
    # Trend Following Strategy
    if up_trends >= 3:
        confidence = 0.5 + (up_trends * 0.08)
        strategies.append({
            "name": "Trend Following Strategy",
            "confidence_score": min(confidence, 0.85),
            "risk_level": "medium",
            "timeframe": "2-4 weeks"
        })
    
    # Volatility Trading Strategy
    if volatility > 2.0 or high_volume >= 2:
        confidence = 0.4 + (volatility * 0.05)
        strategies.append({
            "name": "Volatility Trading Strategy",
            "confidence_score": min(confidence, 0.75),
            "risk_level": "high",
            "timeframe": "1-5 days"
        })
    
    # Event-Driven Strategy
    if len(recent_events) > 2:
        confidence = 0.3 + (len(recent_events) * 0.05)
        strategies.append({
            "name": "Event-Driven Strategy",
            "confidence_score": min(confidence, 0.7),
            "risk_level": "medium",
            "timeframe": "1-7 days"
        })
    
    # Defensive Strategy (fallback)
    if not strategies or avg_change < 0:
        strategies.append({
            "name": "Defensive Strategy",
            "confidence_score": 0.6,
            "risk_level": "low",
            "timeframe": "1-3 months"
        })
    
    # Select primary strategy (highest confidence)
    primary_strategy = max(strategies, key=lambda x: x['confidence_score'])
    
    # Generate reasoning
    market_analysis = {
        "regime": regime,
        "confidence": regime_confidence,
        "event_impact": "high" if len(recent_events) > 3 else "medium" if len(recent_events) > 1 else "low"
    }
    
    reasoning = generate_strategy_reasoning(
        primary_strategy['name'], 
        latest_market, 
        market_analysis, 
        recent_events
    )
    
    return {
        "primary_strategy": primary_strategy,
        "alternative_strategies": strategies[1:3],  # Top 2 alternatives
        "market_analysis": market_analysis,
        "reasoning": reasoning,
        "timestamp": datetime.now()
    }

def main():
    """Main execution loop"""
    
    # MongoDB connection
    MONGODB_URI = os.getenv('MONGODB_URI')
    if not MONGODB_URI:
        print("Error: MONGODB_URI environment variable not set")
        return
    
    try:
        client = pymongo.MongoClient(MONGODB_URI)
        db = client.adaptive_market_db
        print("✅ Connected to MongoDB")
        
        while True:
            try:
                print(f"\n🤖 Analyzing market conditions at {datetime.now().strftime('%H:%M:%S')}")
                
                # Analyze market and generate strategy
                strategy_recommendation = analyze_market_conditions(db)
                
                if strategy_recommendation:
                    # Store in database
                    result = db.strategies.insert_one(strategy_recommendation)
                    
                    # Print summary
                    strategy = strategy_recommendation['primary_strategy']
                    market = strategy_recommendation['market_analysis']
                    
                    print(f"📊 Market Regime: {market['regime']} ({market['confidence']*100:.0f}% confidence)")
                    print(f"🎯 Strategy: {strategy['name']}")
                    print(f"💪 Confidence: {strategy['confidence_score']*100:.0f}%")
                    print(f"⚖️ Risk: {strategy['risk_level']}")
                    print(f"⏰ Timeframe: {strategy['timeframe']}")
                    print(f"💭 Reasoning: {strategy_recommendation['reasoning'][:100]}...")
                    
                    print(f"✅ Strategy recommendation stored with ID: {result.inserted_id}")
                else:
                    print("⚠️ No strategy recommendation generated")
                
            except Exception as e:
                print(f"❌ Error in strategy analysis: {e}")
            
            # Wait 5 minutes before next analysis
            print("⏳ Waiting 5 minutes for next analysis...")
            time.sleep(300)
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
    except KeyboardInterrupt:
        print("\n🛑 Strategy engine stopped")

if __name__ == "__main__":
    main()
