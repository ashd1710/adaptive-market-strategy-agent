#!/usr/bin/env python3
"""
Debug script to test stock screener functionality
"""

import yfinance as yf
import pandas as pd

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    prices_series = pd.Series(prices)
    deltas = prices_series.diff()
    gain = (deltas.where(deltas > 0, 0)).rolling(window=period).mean()
    loss = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if len(rsi) > 0 else 50

def test_momentum_screening():
    """Test momentum screening with debug output"""
    
    # Test with a few popular stocks
    test_stocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    print("🔍 Testing Momentum Screening Logic...")
    print("=" * 60)
    
    results = []
    
    for symbol in test_stocks:
        try:
            print(f"\n📊 Analyzing {symbol}:")
            
            stock = yf.Ticker(symbol)
            hist = stock.history(period="3mo")
            
            if len(hist) < 50:
                print(f"   ❌ Insufficient data (only {len(hist)} days)")
                continue
            
            # Calculate indicators
            recent_return = (hist['Close'][-1] / hist['Close'][-21] - 1) * 100
            rsi = calculate_rsi(hist['Close'], 14)
            volume_ratio = hist['Volume'][-5:].mean() / hist['Volume'][-21:].mean()
            
            print(f"   📈 1-month return: {recent_return:.2f}% (need > 3%)")
            print(f"   📊 RSI: {rsi:.1f} (need 45-75)")
            print(f"   📦 Volume ratio: {volume_ratio:.2f} (need > 1.15)")
            
            # Check criteria
            meets_return = recent_return > 3
            meets_rsi = 45 < rsi < 75
            meets_volume = volume_ratio > 1.15
            
            print(f"   ✅ Return criteria: {'PASS' if meets_return else 'FAIL'}")
            print(f"   ✅ RSI criteria: {'PASS' if meets_rsi else 'FAIL'}")
            print(f"   ✅ Volume criteria: {'PASS' if meets_volume else 'FAIL'}")
            
            if meets_return and meets_rsi and meets_volume:
                score = round(recent_return + (rsi-45)*0.3 + (volume_ratio-1)*8, 2)
                results.append({
                    "symbol": symbol,
                    "score": score,
                    "return_1m": round(recent_return, 2),
                    "rsi": round(rsi, 1),
                    "volume_ratio": round(volume_ratio, 2)
                })
                print(f"   🎯 QUALIFIED! Score: {score}")
            else:
                print(f"   ❌ Does not meet criteria")
                
        except Exception as e:
            print(f"   ❌ Error analyzing {symbol}: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 FINAL RESULTS: {len(results)} stocks qualified")
    
    if results:
        print("\n📋 Qualified Stocks:")
        for stock in sorted(results, key=lambda x: x['score'], reverse=True):
            print(f"   {stock['symbol']}: Score {stock['score']} | Return {stock['return_1m']}% | RSI {stock['rsi']} | Volume {stock['volume_ratio']}x")
    else:
        print("\n❌ No stocks met the momentum criteria")
        print("\n🔧 Suggested fixes:")
        print("   1. Lower the return threshold from 3% to 1%")
        print("   2. Widen RSI range to 40-80")
        print("   3. Lower volume ratio to 1.1")
    
    return results

if __name__ == "__main__":
    test_momentum_screening()
