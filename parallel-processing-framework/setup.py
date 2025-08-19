"""
Setup script for Parallel Processing Framework
"""
import subprocess
import sys
import os


def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("Dependencies installed successfully!")


def check_redis():
    """Check if Redis is available"""
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running and accessible")
        return True
    except Exception as e:
        print(f"❌ Redis not available: {e}")
        print("Please install and start Redis:")
        print("  - macOS: brew install redis && brew services start redis")
        print("  - Ubuntu: sudo apt install redis-server && sudo systemctl start redis")
        print("  - Windows: Download from https://redis.io/download")
        return False


def run_demo():
    """Run the demo application"""
    print("\nRunning demo application...")
    demo_path = os.path.join(os.path.dirname(__file__), "examples", "demo.py")
    subprocess.check_call([sys.executable, demo_path])


def main():
    """Main setup function"""
    print("🚀 Parallel Processing Framework Setup")
    print("=" * 40)
    
    # Install dependencies
    try:
        install_dependencies()
    except Exception as e:
        print(f"Failed to install dependencies: {e}")
        return 1
    
    # Check Redis
    if not check_redis():
        print("\nSetup incomplete. Please install Redis and try again.")
        return 1
    
    print("\n✅ Setup completed successfully!")
    print("\nTo get started:")
    print("1. Run the demo: python examples/demo.py")
    print("2. Or import the framework in your code:")
    print("   from parallel_processing_framework import get_orchestrator")
    
    # Ask if user wants to run demo
    try:
        response = input("\nWould you like to run the demo now? (y/n): ").strip().lower()
        if response in ['y', 'yes']:
            run_demo()
    except KeyboardInterrupt:
        print("\nSetup completed. Demo skipped.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())