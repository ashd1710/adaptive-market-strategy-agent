import requests
import pandas as pd
from pymongo import MongoClient
from datetime import datetime, timedelta
import time
import os
from typing import Dict, List
import yfinance as yf
import numpy as np

class MarketDataFetcher:
    def __init__(self, mongo_connection_string: str, alpha_vantage_key: str):
        """
        Initialize the market data fetcher
        
        Args:
            mongo_connection_string: MongoDB Atlas connection string
            alpha_vantage_key: Alpha Vantage API key
        """
        self.alpha_vantage_key = alpha_vantage_key
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"
        
        # MongoDB setup
        self.client = MongoClient(mongo_connection_string)
        self.db = self.client['adaptive_market_db']
        self.market_conditions = self.db['market_conditions']
        
        # Symbols to track
        self.symbols = ['SPY', 'QQQ', 'IWM', 'DIA', 'VIX']
        
    def convert_numpy_types(self, obj):
        """Convert numpy types to native Python types for MongoDB storage"""
        if isinstance(obj, dict):
            return {key: self.convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_numpy_types(item) for item in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif hasattr(obj, 'dtype'):  # Additional numpy type check
            if 'bool' in str(obj.dtype):
                return bool(obj)
            elif 'int' in str(obj.dtype):
                return int(obj)
            elif 'float' in str(obj.dtype):
                return float(obj)
        return obj
        
    def fetch_alpha_vantage_data(self, symbol: str) -> Dict:
        """
        Fetch real-time data from Alpha Vantage
        
        Args:
            symbol: Stock symbol (e.g., 'SPY')
            
        Returns:
            Dictionary with price and volume data
        """
        try:
            # Get real-time quote
            url = f"{self.alpha_vantage_base_url}?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_key}"
            response = requests.get(url)
            data = response.json()
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                return {
                    'symbol': symbol,
                    'price': float(quote['05. price']),
                    'change': float(quote['09. change']),
                    'change_percent': float(quote['10. change percent'].replace('%', '')),
                    'volume': int(quote['06. volume']),
                    'previous_close': float(quote['08. previous close']),
                    'timestamp': datetime.utcnow()
                }
            else:
                print(f"Error fetching {symbol}: {data}")
                return None
                
        except Exception as e:
            print(f"Error fetching Alpha Vantage data for {symbol}: {e}")
            return None
    
    def fetch_yahoo_finance_backup(self, symbol: str) -> Dict:
        """
        Backup data source using Yahoo Finance (faster, no API limits)
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with market data
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="2d")
            
            if len(hist) >= 2:
                current = hist.iloc[-1]
                previous = hist.iloc[-2]
                
                return {
                    'symbol': symbol,
                    'price': float(current['Close']),
                    'change': float(current['Close'] - previous['Close']),
                    'change_percent': float(((current['Close'] - previous['Close']) / previous['Close']) * 100),
                    'volume': int(current['Volume']),
                    'previous_close': float(previous['Close']),
                    'timestamp': datetime.utcnow()
                }
            else:
                return None
                
        except Exception as e:
            print(f"Error fetching Yahoo Finance data for {symbol}: {e}")
            return None
    
    def calculate_technical_indicators(self, symbol: str, data: Dict) -> Dict:
        """
        Calculate basic technical indicators
        
        Args:
            symbol: Stock symbol
            data: Current market data
            
        Returns:
            Dictionary with technical indicators
        """
        try:
            # Get historical data for calculations
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="60d")  # 60 days for indicators
            
            if len(hist) < 20:
                return {}
            
            # Calculate indicators
            indicators = {}
            
            # Simple Moving Averages
            indicators['sma_20'] = float(hist['Close'].rolling(20).mean().iloc[-1])
            indicators['sma_50'] = float(hist['Close'].rolling(50).mean().iloc[-1])
            
            # RSI (Relative Strength Index)
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            indicators['rsi'] = float(100 - (100 / (1 + rs.iloc[-1])))
            
            # Volume indicators
            indicators['volume_sma_20'] = int(hist['Volume'].rolling(20).mean().iloc[-1])
            indicators['volume_ratio'] = float(data['volume'] / indicators['volume_sma_20'])
            
            # Trend signals
            current_price = data['price']
            indicators['above_sma_20'] = bool(current_price > indicators['sma_20'])
            indicators['above_sma_50'] = bool(current_price > indicators['sma_50'])
            
            return indicators
            
        except Exception as e:
            print(f"Error calculating indicators for {symbol}: {e}")
            return {}
    
    def determine_regime_signals(self, data: Dict, indicators: Dict) -> Dict:
        """
        Generate basic market regime signals
        
        Args:
            data: Market data
            indicators: Technical indicators
            
        Returns:
            Dictionary with regime signals
        """
        signals = {}
        
        # Trend direction
        if data['change_percent'] > 1:
            signals['trend'] = 'strong_up'
        elif data['change_percent'] > 0:
            signals['trend'] = 'up'
        elif data['change_percent'] < -1:
            signals['trend'] = 'strong_down'
        else:
            signals['trend'] = 'down'
        
        # Volume signal
        volume_ratio = indicators.get('volume_ratio', 1)
        if volume_ratio > 1.5:
            signals['volume'] = 'high'
        elif volume_ratio > 1.1:
            signals['volume'] = 'above_average'
        else:
            signals['volume'] = 'normal'
        
        # RSI signals
        rsi = indicators.get('rsi', 50)
        if rsi > 70:
            signals['momentum'] = 'overbought'
        elif rsi > 60:
            signals['momentum'] = 'strong'
        elif rsi < 30:
            signals['momentum'] = 'oversold'
        elif rsi < 40:
            signals['momentum'] = 'weak'
        else:
            signals['momentum'] = 'neutral'
        
        return signals
    
    def store_market_data(self, market_data: Dict) -> bool:
        """
        Store market data in MongoDB with numpy type conversion
        
        Args:
            market_data: Complete market data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert numpy types to native Python types
            clean_data = self.convert_numpy_types(market_data)
            
            # Add unique identifier for deduplication
            clean_data['_id'] = f"{clean_data['symbol']}_{clean_data['timestamp'].strftime('%Y%m%d_%H%M')}"
            
            # Insert or update
            self.market_conditions.replace_one(
                {'_id': clean_data['_id']},
                clean_data,
                upsert=True
            )
            
            print(f"✅ Stored data for {clean_data['symbol']}: ${clean_data['price']}")
            return True
            
        except Exception as e:
            print(f"❌ Error storing market data: {e}")
            return False
    
    def fetch_and_store_all_symbols(self):
        """
        Fetch data for all symbols and store in MongoDB
        """
        print(f"🔄 Fetching market data at {datetime.now().strftime('%H:%M:%S')}")
        
        for symbol in self.symbols:
            try:
                # Try Alpha Vantage first, then Yahoo Finance backup
                data = self.fetch_alpha_vantage_data(symbol)
                if not data:
                    print(f"⚠️  Alpha Vantage failed for {symbol}, using Yahoo Finance")
                    data = self.fetch_yahoo_finance_backup(symbol)
                
                if data:
                    # Calculate technical indicators
                    indicators = self.calculate_technical_indicators(symbol, data)
                    
                    # Generate regime signals
                    signals = self.determine_regime_signals(data, indicators)
                    
                    # Combine all data
                    complete_data = {
                        **data,
                        'indicators': indicators,
                        'regime_signals': signals
                    }
                    
                    # Store in MongoDB
                    self.store_market_data(complete_data)
                    
                else:
                    print(f"❌ Failed to fetch data for {symbol}")
                
                # Rate limiting - wait between API calls
                time.sleep(12)  # 5 calls per minute = 12 seconds between calls
                
            except Exception as e:
                print(f"❌ Error processing {symbol}: {e}")
                continue
    
    def start_continuous_fetching(self, interval_minutes: int = 5):
        """
        Start continuous data fetching every X minutes
        
        Args:
            interval_minutes: Interval between fetches
        """
        print(f"🚀 Starting continuous market data fetching every {interval_minutes} minutes")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.fetch_and_store_all_symbols()
                print(f"💤 Sleeping for {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping market data fetcher")


# Usage example
if __name__ == "__main__":
    # Configuration - Replace with your actual keys
    MONGO_CONNECTION = "mongodb+srv://marketagent:T9QjESNK8lunUoTU@adaptive-market-cluster.aganihz.mongodb.net/"
    ALPHA_VANTAGE_KEY = "UXBC4N9UA6OYP60O"
    
    # Initialize fetcher
    fetcher = MarketDataFetcher(MONGO_CONNECTION, ALPHA_VANTAGE_KEY)
    
    # Test single fetch
    print("🧪 Testing single data fetch...")
    fetcher.fetch_and_store_all_symbols()
    
    # Start continuous fetching (uncomment to run continuously)
    # fetcher.start_continuous_fetching(interval_minutes=5)
