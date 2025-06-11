# 🏥 System Health Check Script
# Save as: health_check.py

import requests
import json
from datetime import datetime

def test_api_endpoint(url, name):
    """Test an API endpoint and return status"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"✅ {name}: Working (Status: {response.status_code})")
            return True, response.json()
        else:
            print(f"❌ {name}: Failed (Status: {response.status_code})")
            return False, None
    except Exception as e:
        print(f"❌ {name}: Error - {str(e)}")
        return False, None

def main():
    print("🏥 ADAPTIVE MARKET STRATEGY AGENT - SYSTEM HEALTH CHECK")
    print("=" * 60)
    print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    base_url = "http://localhost:8000"
    
    # Test endpoints
    endpoints = [
        (f"{base_url}", "Dashboard Home"),
        (f"{base_url}/api/current-analysis", "Market Analysis API"),
        (f"{base_url}/api/available-strategies", "Available Strategies API"),
        (f"{base_url}/api/strategy-screener/momentum", "Momentum Screener API"),
        (f"{base_url}/api/strategy-screener/value", "Value Screener API"),
        (f"{base_url}/api/strategy-screener/breakout", "Breakout Screener API"),
        (f"{base_url}/api/strategy-screener/mean_reversion", "Mean Reversion Screener API"),
    ]
    
    working_count = 0
    total_count = len(endpoints)
    
    print("🔍 TESTING API ENDPOINTS:")
    print("-" * 40)
    
    for url, name in endpoints:
        is_working, data = test_api_endpoint(url, name)
        if is_working:
            working_count += 1
            
            # Show sample data for key endpoints
            if "current-analysis" in url and data:
                print(f"   📊 Current Strategy: {data.get('strategy', {}).get('type', 'Unknown')}")
                print(f"   📈 Market Regime: {data.get('market_conditions', {}).get('regime', 'Unknown')}")
            elif "screener" in url and data:
                stocks = data.get('recommendations', [])
                print(f"   📋 Found {len(stocks)} stocks")
                if stocks:
                    top_stock = stocks[0]
                    print(f"   🎯 Top Pick: {top_stock.get('symbol', 'N/A')} (Score: {top_stock.get('score', 'N/A')})")
    
    print()
    print("📊 SYSTEM STATUS SUMMARY:")
    print("-" * 40)
    print(f"✅ Working Endpoints: {working_count}/{total_count}")
    print(f"📈 System Health: {(working_count/total_count)*100:.1f}%")
    
    if working_count == total_count:
        print("🎉 ALL SYSTEMS OPERATIONAL - READY FOR DEMO!")
    elif working_count >= total_count * 0.8:
        print("⚠️ MOSTLY OPERATIONAL - MINOR ISSUES TO ADDRESS")
    else:
        print("🚨 CRITICAL ISSUES - NEEDS IMMEDIATE ATTENTION")
    
    print()
    print("🎯 NEXT STEPS:")
    if working_count == total_count:
        print("✅ Proceed to demo rehearsal")
        print("✅ Test visual enhancements")
        print("✅ Prepare presentation slides")
    else:
        print("🔧 Fix failing endpoints first")
        print("🔍 Check logs for error details")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
