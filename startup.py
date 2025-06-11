#!/usr/bin/env python3
"""
Startup script for Adaptive Market Strategy Agent Dashboard
Run this script to start the web server and begin the demo
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_requirements():
    """Check if all required packages are installed"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'pymongo',
        'python-multipart'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstalling missing packages...")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"   ✅ Installed {package}")
            except subprocess.CalledProcessError:
                print(f"   ❌ Failed to install {package}")
                return False
    
    return True

def create_static_directory():
    """Create static directory if it doesn't exist"""
    static_dir = Path("static")
    static_dir.mkdir(exist_ok=True)
    
    # Check if index.html exists in static directory
    static_index = static_dir / "index.html"
    
    if not static_index.exists():
        print("⚠️ Warning: static/index.html not found. Please ensure the frontend file is available.")
        return False
    
    return True

def check_data_pipeline():
    """Check if data pipeline scripts exist"""
    required_files = [
        "market_data_fetcher.py",
        "news_data_fetcher.py", 
        "strategy_engine.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("⚠️ Warning: Some data pipeline files are missing:")
        for file in missing_files:
            print(f"   - {file}")
        print("The dashboard will work but may not have live data.")
        return False
    
    return True

def check_mongodb_connection():
    """Check MongoDB connection"""
    try:
        import pymongo
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            print("⚠️ Warning: MONGODB_URI environment variable not set")
            return False
        
        client = pymongo.MongoClient(mongodb_uri)
        client.admin.command('ping')
        print("   ✅ MongoDB connection successful")
        return True
    except Exception as e:
        print(f"   ❌ MongoDB connection failed: {e}")
        return False

def start_data_pipeline():
    """Start the data collection processes in background"""
    print("🔄 Starting data pipeline...")
    
    scripts = [
        "market_data_fetcher.py",
        "news_data_fetcher.py",
        "strategy_engine.py"
    ]
    
    processes = []
    for script in scripts:
        if Path(script).exists():
            try:
                process = subprocess.Popen([sys.executable, script], 
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE)
                processes.append((script, process))
                print(f"   ✅ Started {script}")
                time.sleep(2)  # Small delay between starts
            except Exception as e:
                print(f"   ❌ Failed to start {script}: {e}")
    
    return processes

def main():
    print("🚀 Adaptive Market Strategy Agent - Startup Script")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    
    # Check requirements
    print("📦 Checking required packages...")
    if not check_requirements():
        print("❌ Failed to install required packages")
        sys.exit(1)
    print("   ✅ All packages ready")
    
    # Check static files
    print("📁 Checking static files...")
    if not create_static_directory():
        print("   ⚠️ Frontend files may be missing")
    else:
        print("   ✅ Static files ready")
    
    # Check MongoDB connection
    print("🔍 Checking MongoDB connection...")
    mongodb_ok = check_mongodb_connection()
    
    # Check data pipeline
    print("🔍 Checking data pipeline...")
    pipeline_ready = check_data_pipeline()
    if pipeline_ready:
        print("   ✅ Data pipeline files found")
    
    # Ask about starting data pipeline
    if pipeline_ready and mongodb_ok:
        start_pipeline = input("\n🤖 Start data pipeline in background? (y/n): ").lower().strip()
        processes = []
        if start_pipeline == 'y':
            processes = start_data_pipeline()
    else:
        processes = []
    
    # Start web server
    print("\n🌐 Starting web server...")
    print("   📊 Dashboard will be available at: http://localhost:8000")
    print("   🔄 API endpoints available at: http://localhost:8000/api/")
    print("\n   Press Ctrl+C to stop all services")
    print("=" * 50)
    
    try:
        # Import and run the FastAPI server
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        
        # Stop data pipeline processes
        for script_name, process in processes:
            try:
                process.terminate()
                print(f"   ✅ Stopped {script_name}")
            except:
                pass
        
        print("   ✅ All services stopped")
        print("   👋 Thanks for using Adaptive Market Strategy Agent!")
    
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure main.py (FastAPI app) exists in current directory")
        print("2. Check if port 8000 is available")
        print("3. Verify MongoDB connection string is set")
        sys.exit(1)

if __name__ == "__main__":
    main()
