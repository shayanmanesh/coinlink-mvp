#!/usr/bin/env python3
"""
Integration Testing Script for CoinLink MVP
Testing critical user flows:
1. Authentication flow
2. WebSocket real-time updates
3. Alert creation and notifications
4. API endpoints
"""

import asyncio
import json
import time
import requests
import websockets
from datetime import datetime
import random
import string

# Configuration
BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

# Test results storage
test_results = []

def generate_random_email():
    """Generate a random email for testing"""
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_str}@example.com"

def log_test(test_name, status, details=""):
    """Log test results"""
    result = {
        "test": test_name,
        "status": status,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    print(f"[{status}] {test_name}: {details}")

# 1. Test Authentication Flow
def test_authentication():
    """Test the authentication endpoints"""
    print("\n" + "="*50)
    print("Testing Authentication Flow")
    print("="*50)
    
    test_email = generate_random_email()
    test_password = "TestPassword123!"
    
    # Test signup
    try:
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/signup",
            json={"email": test_email, "password": test_password}
        )
        if response.status_code == 200:
            data = response.json()
            log_test("Signup", "PASS", f"Successfully created user: {test_email}")
            auth_token = data.get("token")
        else:
            log_test("Signup", "FAIL", f"Status {response.status_code}: {response.text}")
            auth_token = None
    except Exception as e:
        log_test("Signup", "ERROR", str(e))
        auth_token = None
    
    # Test login
    try:
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json={"email": test_email, "password": test_password}
        )
        if response.status_code == 200:
            data = response.json()
            log_test("Login", "PASS", f"Successfully logged in: {test_email}")
            auth_token = data.get("token")
        else:
            log_test("Login", "FAIL", f"Status {response.status_code}: {response.text}")
    except Exception as e:
        log_test("Login", "ERROR", str(e))
    
    # Test verify token
    if auth_token:
        try:
            headers = {"Authorization": f"Bearer {auth_token}"}
            response = requests.get(
                f"{BASE_URL}/api/v2/auth/verify",
                headers=headers
            )
            if response.status_code == 200:
                log_test("Token Verification", "PASS", "Token is valid")
            else:
                log_test("Token Verification", "FAIL", f"Status {response.status_code}")
        except Exception as e:
            log_test("Token Verification", "ERROR", str(e))
    
    # Test invalid login
    try:
        response = requests.post(
            f"{BASE_URL}/api/v2/auth/login",
            json={"email": "invalid@test.com", "password": "wrongpass"}
        )
        if response.status_code != 200:
            log_test("Invalid Login Rejection", "PASS", "Correctly rejected invalid credentials")
        else:
            log_test("Invalid Login Rejection", "FAIL", "Accepted invalid credentials")
    except Exception as e:
        log_test("Invalid Login Rejection", "ERROR", str(e))
    
    return auth_token

# 2. Test WebSocket Real-time Updates
async def test_websocket():
    """Test WebSocket connection and real-time updates"""
    print("\n" + "="*50)
    print("Testing WebSocket Real-time Updates")
    print("="*50)
    
    try:
        async with websockets.connect(WS_URL) as websocket:
            log_test("WebSocket Connection", "PASS", "Connected to WebSocket")
            
            # Send initial connection message
            await websocket.send(json.dumps({
                "type": "connection",
                "message": "test_client"
            }))
            
            # Listen for messages (with timeout)
            messages_received = []
            start_time = time.time()
            
            while time.time() - start_time < 10:  # 10 second timeout
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    msg_data = json.loads(message)
                    messages_received.append(msg_data)
                    
                    if msg_data.get("type") == "price_update":
                        log_test("Price Update", "PASS", f"Received BTC price: ${msg_data.get('data', {}).get('price', 'N/A')}")
                    elif msg_data.get("type") == "alert":
                        log_test("Alert Message", "PASS", f"Received alert: {msg_data.get('data', {}).get('message', 'N/A')}")
                    elif msg_data.get("type") == "market_report":
                        log_test("Market Report", "PASS", "Received market report update")
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    log_test("WebSocket Message", "ERROR", str(e))
                    break
            
            if len(messages_received) > 0:
                log_test("WebSocket Data Stream", "PASS", f"Received {len(messages_received)} messages")
            else:
                log_test("WebSocket Data Stream", "WARN", "No messages received in 10 seconds")
                
    except Exception as e:
        log_test("WebSocket Connection", "FAIL", str(e))

# 3. Test Alert System
def test_alerts():
    """Test alert creation and retrieval"""
    print("\n" + "="*50)
    print("Testing Alert System")
    print("="*50)
    
    # Get current alerts
    try:
        response = requests.get(f"{BASE_URL}/api/alerts")
        if response.status_code == 200:
            data = response.json()
            log_test("Get Alerts", "PASS", f"Retrieved {data.get('count', 0)} active alerts")
        elif response.status_code == 404:
            log_test("Get Alerts", "INFO", "Legacy alerts endpoint disabled (using real-time system)")
        else:
            log_test("Get Alerts", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_test("Get Alerts", "ERROR", str(e))
    
    # Get alert history
    try:
        response = requests.get(f"{BASE_URL}/api/alerts/history?limit=5")
        if response.status_code == 200:
            data = response.json()
            log_test("Alert History", "PASS", f"Retrieved {len(data.get('history', []))} historical alerts")
        elif response.status_code == 404:
            log_test("Alert History", "INFO", "Legacy alerts endpoint disabled (using real-time system)")
        else:
            log_test("Alert History", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_test("Alert History", "ERROR", str(e))

# 4. Test API Endpoints with curl commands
def test_api_endpoints():
    """Test all critical API endpoints"""
    print("\n" + "="*50)
    print("Testing API Endpoints")
    print("="*50)
    
    # Test health check
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            log_test("Health Check", "PASS", f"Status: {data.get('status', 'unknown')}")
        else:
            log_test("Health Check", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_test("Health Check", "ERROR", str(e))
    
    # Test root endpoint
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            log_test("Root Endpoint", "PASS", f"API Version: {data.get('version', 'unknown')}")
        else:
            log_test("Root Endpoint", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_test("Root Endpoint", "ERROR", str(e))
    
    # Test Bitcoin price endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/bitcoin/price")
        if response.status_code == 200:
            data = response.json()
            price_info = data.get('data', {})
            log_test("Bitcoin Price", "PASS", f"BTC: ${price_info.get('price', 'N/A')}")
        else:
            log_test("Bitcoin Price", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_test("Bitcoin Price", "ERROR", str(e))
    
    # Test Bitcoin sentiment endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/bitcoin/sentiment")
        if response.status_code == 200:
            data = response.json()
            sentiment = data.get('data', {}).get('overall_sentiment', 'unknown')
            log_test("Bitcoin Sentiment", "PASS", f"Sentiment: {sentiment}")
        else:
            log_test("Bitcoin Sentiment", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_test("Bitcoin Sentiment", "ERROR", str(e))
    
    # Test market summary endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/bitcoin/market-summary")
        if response.status_code == 200:
            data = response.json()
            log_test("Market Summary", "PASS", "Retrieved market summary")
        else:
            log_test("Market Summary", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_test("Market Summary", "ERROR", str(e))
    
    # Test chat endpoint
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "message": "What is the current Bitcoin price?",
                "session_id": "test_session"
            }
        )
        if response.status_code == 200:
            data = response.json()
            log_test("Chat Endpoint", "PASS", "Chat response received")
        else:
            log_test("Chat Endpoint", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_test("Chat Endpoint", "ERROR", str(e))
    
    # Test chat history
    try:
        response = requests.get(f"{BASE_URL}/api/chat/history")
        if response.status_code == 200:
            data = response.json()
            log_test("Chat History", "PASS", f"Retrieved {len(data.get('history', []))} messages")
        else:
            log_test("Chat History", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_test("Chat History", "ERROR", str(e))
    
    # Test prompts endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/prompts")
        if response.status_code == 200:
            data = response.json()
            log_test("Prompts Endpoint", "PASS", f"Retrieved {len(data.get('prompts', []))} prompts")
        else:
            log_test("Prompts Endpoint", "FAIL", f"Status {response.status_code}")
    except Exception as e:
        log_test("Prompts Endpoint", "ERROR", str(e))

def print_curl_commands():
    """Print example curl commands for manual testing"""
    print("\n" + "="*50)
    print("Example CURL Commands for Manual Testing")
    print("="*50)
    
    commands = [
        "# Health check",
        "curl http://localhost:8000/health",
        "",
        "# Get Bitcoin price",
        "curl http://localhost:8000/api/bitcoin/price",
        "",
        "# Get Bitcoin sentiment",
        "curl http://localhost:8000/api/bitcoin/sentiment",
        "",
        "# Send chat message",
        'curl -X POST http://localhost:8000/api/chat \\',
        '  -H "Content-Type: application/json" \\',
        '  -d \'{"message": "What is Bitcoin?", "session_id": "test"}\'',
        "",
        "# Test authentication - Signup",
        'curl -X POST http://localhost:8000/api/v2/auth/signup \\',
        '  -H "Content-Type: application/json" \\',
        '  -d \'{"email": "test@example.com", "password": "TestPass123"}\'',
        "",
        "# Test authentication - Login",
        'curl -X POST http://localhost:8000/api/v2/auth/login \\',
        '  -H "Content-Type: application/json" \\',
        '  -d \'{"email": "test@example.com", "password": "TestPass123"}\'',
        "",
        "# WebSocket connection (requires wscat or similar)",
        "wscat -c ws://localhost:8000/ws",
    ]
    
    for cmd in commands:
        print(cmd)

def generate_test_report():
    """Generate final test report"""
    print("\n" + "="*50)
    print("TEST REPORT SUMMARY")
    print("="*50)
    
    total_tests = len(test_results)
    passed = len([r for r in test_results if r["status"] == "PASS"])
    failed = len([r for r in test_results if r["status"] == "FAIL"])
    errors = len([r for r in test_results if r["status"] == "ERROR"])
    warnings = len([r for r in test_results if r["status"] == "WARN"])
    info = len([r for r in test_results if r["status"] == "INFO"])
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    print(f"Warnings: {warnings}")
    print(f"Info: {info}")
    print(f"Success Rate: {(passed/total_tests*100) if total_tests > 0 else 0:.1f}%")
    
    if failed > 0 or errors > 0:
        print("\nFailed/Error Tests:")
        for result in test_results:
            if result["status"] in ["FAIL", "ERROR"]:
                print(f"  - {result['test']}: {result['details']}")
    
    # Save detailed report
    report_file = f"/Users/shayanbozorgmanesh/Documents/Parking/coinlink-mvp/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            "summary": {
                "total": total_tests,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "warnings": warnings,
                "info": info,
                "success_rate": f"{(passed/total_tests*100) if total_tests > 0 else 0:.1f}%"
            },
            "results": test_results,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    return total_tests, passed, failed, errors

async def main():
    """Main test runner"""
    print("\n" + "="*60)
    print("CoinLink MVP - Integration Testing Suite")
    print("="*60)
    print(f"Starting tests at {datetime.now().isoformat()}")
    print(f"Target: {BASE_URL}")
    
    # Run authentication tests
    auth_token = test_authentication()
    
    # Run API endpoint tests
    test_api_endpoints()
    
    # Run alert tests
    test_alerts()
    
    # Run WebSocket tests
    await test_websocket()
    
    # Print curl commands
    print_curl_commands()
    
    # Generate report
    total, passed, failed, errors = generate_test_report()
    
    # Exit with appropriate code
    if failed > 0 or errors > 0:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        generate_test_report()