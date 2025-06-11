# Demo Performance Optimization
# Save as: optimize_for_demo.py

import requests
import json
import time
from datetime import datetime

def pre_cache_all_screeners():
    """Pre-cache all screener results for faster demo"""
    print("🚀 PRE-CACHING SCREENER RESULTS FOR DEMO")
    print("=" * 50)
    
    strategies = ["momentum", "value", "breakout", "mean_reversion"]
    cached_results = {}
    
    for strategy in strategies:
        print(f"📊 Caching {strategy.upper()} strategy...")
        start_time = time.time()
        
        try:
            response = requests.get(
                f"http://localhost:8000/api/strategy-screener/{strategy}",
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                cached_results[strategy] = data
                
                duration = time.time() - start_time
                stock_count = len(data.get('recommendations', []))
                
                print(f"✅ {strategy}: {stock_count} stocks cached in {duration:.1f}s")
                
                # Show top pick
                if stock_count > 0:
                    top_stock = data['recommendations'][0]
                    symbol = top_stock.get('symbol', 'N/A')
                    score = top_stock.get('score', 'N/A')
                    return_1m = top_stock.get('return_1m', 'N/A')
                    print(f"   🎯 Top Pick: {symbol} (Score: {score}, Return: {return_1m}%)")
            else:
                print(f"❌ {strategy}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {strategy}: Error - {str(e)}")
    
    # Save cached results
    cache_file = f"demo_cache_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(cache_file, 'w') as f:
        json.dump(cached_results, f, indent=2)
    
    print(f"\n💾 Results cached to: {cache_file}")
    return cached_results

def generate_demo_summary(cached_results):
    """Generate demo talking points"""
    print("\n🎯 DEMO TALKING POINTS")
    print("=" * 50)
    
    total_stocks = 0
    
    for strategy, data in cached_results.items():
        stock_count = len(data.get('recommendations', []))
        total_stocks += stock_count
        
        print(f"\n📈 {strategy.upper()} STRATEGY:")
        print(f"   • {stock_count} qualified stocks")
        
        if stock_count > 0:
            top_3 = data['recommendations'][:3]
            for i, stock in enumerate(top_3, 1):
                symbol = stock.get('symbol', 'N/A')
                score = stock.get('score', 'N/A')
                return_1m = stock.get('return_1m', 'N/A')
                print(f"   {i}. {symbol}: {score} score, {return_1m}% return")
    
    print(f"\n🏆 DEMO HIGHLIGHTS:")
    print(f"   • Total stocks analyzed: {total_stocks}")
    print(f"   • 4 strategy types available")
    print(f"   • Real-time scoring and ranking")
    print(f"   • Live market data integration")

def test_demo_flow():
    """Test the complete demo flow"""
    print("\n🎬 TESTING DEMO FLOW")
    print("=" * 30)
    
    # Test market analysis
    try:
        response = requests.get("http://localhost:8000/api/current-analysis", timeout=10)
        if response.status_code == 200:
            data = response.json()
            strategy = data.get('strategy', {}).get('type', 'Unknown')
            confidence = data.get('strategy', {}).get('confidence', 'Unknown')
            regime = data.get('market_conditions', {}).get('regime', 'Unknown')
            
            print("✅ Current Market Analysis:")
            print(f"   📊 Recommended Strategy: {strategy}")
            print(f"   📈 Market Regime: {regime}")
            print(f"   🎯 Confidence: {confidence}")
        else:
            print("❌ Market analysis failed")
    except Exception as e:
        print(f"❌ Market analysis error: {e}")

def main():
    print("🎯 DEMO OPTIMIZATION SCRIPT")
    print("This will pre-cache all results for fastest demo performance")
    print("=" * 60)
    
    # Pre-cache all screener results
    cached_results = pre_cache_all_screeners()
    
    # Generate demo summary
    if cached_results:
        generate_demo_summary(cached_results)
    
    # Test demo flow
    test_demo_flow()
    
    print("\n🎉 DEMO OPTIMIZATION COMPLETE!")
    print("Your system is now optimized for the fastest possible demo performance.")
    print("\n🎬 Ready for your 5-minute hackathon presentation!")

if __name__ == "__main__":
    main()
