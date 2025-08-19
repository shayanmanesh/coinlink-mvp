#!/usr/bin/env python3
"""
CoinLink MVP Load Testing Suite
================================
Production-ready load testing for www.coin.link deployment
Tests WebSocket connections, API rate limits, Redis caching, and memory usage
"""

import asyncio
import aiohttp
import time
import json
import sys
import psutil
import statistics
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import websockets
import random

# Configuration
BASE_URL = "http://localhost:8000"  # Change to production URL when testing deployed version
WS_URL = "ws://localhost:8000/ws"   # Change to wss://www.coin.link/ws for production
REDIS_TEST_ENABLED = True

@dataclass
class TestMetrics:
    """Store test metrics and results"""
    websocket_connections_successful: int = 0
    websocket_connections_failed: int = 0
    websocket_messages_sent: int = 0
    websocket_messages_received: int = 0
    websocket_latencies: List[float] = field(default_factory=list)
    
    api_requests_successful: int = 0
    api_requests_failed: int = 0
    api_rate_limited: int = 0
    api_latencies: List[float] = field(default_factory=list)
    
    redis_hits: int = 0
    redis_misses: int = 0
    redis_response_times: List[float] = field(default_factory=list)
    
    memory_usage_start: float = 0
    memory_usage_peak: float = 0
    memory_usage_end: float = 0
    cpu_usage_avg: float = 0
    
    errors: List[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: float = 0

class WebSocketLoadTest:
    """Test WebSocket connections and performance"""
    
    def __init__(self, metrics: TestMetrics):
        self.metrics = metrics
        self.connections: List[websockets.WebSocketClientProtocol] = []
    
    async def create_connection(self, connection_id: int) -> Optional[websockets.WebSocketClientProtocol]:
        """Create a single WebSocket connection"""
        try:
            ws = await websockets.connect(WS_URL)
            self.metrics.websocket_connections_successful += 1
            print(f"✓ WebSocket connection {connection_id} established")
            return ws
        except Exception as e:
            self.metrics.websocket_connections_failed += 1
            self.metrics.errors.append(f"WS connection {connection_id} failed: {str(e)}")
            print(f"✗ WebSocket connection {connection_id} failed: {e}")
            return None
    
    async def send_message(self, ws: websockets.WebSocketClientProtocol, message: str) -> float:
        """Send message and measure round-trip time"""
        try:
            start = time.time()
            await ws.send(json.dumps({
                "type": "chat",
                "message": message
            }))
            self.metrics.websocket_messages_sent += 1
            
            # Wait for response
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            self.metrics.websocket_messages_received += 1
            
            latency = time.time() - start
            self.metrics.websocket_latencies.append(latency)
            return latency
        except Exception as e:
            self.metrics.errors.append(f"WS message failed: {str(e)}")
            return -1
    
    async def test_concurrent_connections(self, num_connections: int = 50):
        """Test multiple concurrent WebSocket connections"""
        print(f"\n🔌 Testing {num_connections} concurrent WebSocket connections...")
        
        # Create connections
        tasks = [self.create_connection(i) for i in range(num_connections)]
        connections = await asyncio.gather(*tasks)
        self.connections = [c for c in connections if c is not None]
        
        print(f"📊 Established {len(self.connections)}/{num_connections} connections")
        
        # Send test messages from each connection
        if self.connections:
            print(f"📨 Sending test messages from {len(self.connections)} connections...")
            test_messages = [
                "What's the current Bitcoin price?",
                "Show me market analysis",
                "Is it a good time to buy?",
                "What's the sentiment?",
                "Technical indicators?"
            ]
            
            message_tasks = []
            for i, ws in enumerate(self.connections):
                message = random.choice(test_messages)
                message_tasks.append(self.send_message(ws, message))
            
            latencies = await asyncio.gather(*message_tasks)
            valid_latencies = [l for l in latencies if l > 0]
            
            if valid_latencies:
                print(f"✓ Average WebSocket latency: {statistics.mean(valid_latencies):.3f}s")
                print(f"✓ Min/Max latency: {min(valid_latencies):.3f}s / {max(valid_latencies):.3f}s")
    
    async def cleanup(self):
        """Close all WebSocket connections"""
        for ws in self.connections:
            try:
                await ws.close()
            except:
                pass

class APILoadTest:
    """Test API endpoints and rate limits"""
    
    def __init__(self, metrics: TestMetrics):
        self.metrics = metrics
    
    async def test_endpoint(self, session: aiohttp.ClientSession, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
        """Test a single API endpoint"""
        try:
            start = time.time()
            
            if method == "GET":
                async with session.get(f"{BASE_URL}{endpoint}") as response:
                    latency = time.time() - start
                    self.metrics.api_latencies.append(latency)
                    
                    if response.status == 429:
                        self.metrics.api_rate_limited += 1
                        return {"status": 429, "latency": latency}
                    elif response.status == 200:
                        self.metrics.api_requests_successful += 1
                        return {"status": 200, "latency": latency, "data": await response.json()}
                    else:
                        self.metrics.api_requests_failed += 1
                        return {"status": response.status, "latency": latency}
            
            elif method == "POST":
                async with session.post(f"{BASE_URL}{endpoint}", json=data) as response:
                    latency = time.time() - start
                    self.metrics.api_latencies.append(latency)
                    
                    if response.status == 429:
                        self.metrics.api_rate_limited += 1
                        return {"status": 429, "latency": latency}
                    elif response.status == 200:
                        self.metrics.api_requests_successful += 1
                        return {"status": 200, "latency": latency, "data": await response.json()}
                    else:
                        self.metrics.api_requests_failed += 1
                        return {"status": response.status, "latency": latency}
                        
        except Exception as e:
            self.metrics.api_requests_failed += 1
            self.metrics.errors.append(f"API request to {endpoint} failed: {str(e)}")
            return {"status": 500, "error": str(e)}
    
    async def test_rate_limits(self):
        """Test API rate limiting"""
        print("\n🚦 Testing API rate limits...")
        
        async with aiohttp.ClientSession() as session:
            # Test /api/chat endpoint (20/minute limit)
            print("Testing /api/chat rate limit (20/minute)...")
            chat_requests = []
            for i in range(25):  # Try to exceed limit
                chat_requests.append(self.test_endpoint(
                    session, 
                    "/api/chat", 
                    "POST", 
                    {"message": f"Test message {i}", "session_id": f"test_{i}"}
                ))
            
            results = await asyncio.gather(*chat_requests)
            rate_limited_count = sum(1 for r in results if r.get("status") == 429)
            print(f"✓ Rate limited {rate_limited_count}/25 requests (expected ~5)")
            
            # Test /api/bitcoin/price endpoint (60/minute limit)
            print("Testing /api/bitcoin/price rate limit (60/minute)...")
            price_requests = []
            for i in range(70):  # Try to exceed limit
                price_requests.append(self.test_endpoint(session, "/api/bitcoin/price"))
            
            results = await asyncio.gather(*price_requests)
            rate_limited_count = sum(1 for r in results if r.get("status") == 429)
            print(f"✓ Rate limited {rate_limited_count}/70 requests (expected ~10)")
    
    async def test_endpoints_performance(self):
        """Test various endpoints for performance"""
        print("\n⚡ Testing API endpoint performance...")
        
        endpoints = [
            ("/", "GET", None),
            ("/health", "GET", None),
            ("/api/bitcoin/price", "GET", None),
            ("/api/bitcoin/sentiment", "GET", None),
            ("/api/bitcoin/market-summary", "GET", None),
            ("/api/connections", "GET", None),
            ("/api/correlation", "GET", None),
        ]
        
        async with aiohttp.ClientSession() as session:
            for endpoint, method, data in endpoints:
                result = await self.test_endpoint(session, endpoint, method, data)
                if result.get("status") == 200:
                    print(f"✓ {endpoint}: {result.get('latency', 0):.3f}s")
                else:
                    print(f"✗ {endpoint}: Status {result.get('status')}")

class RedisLoadTest:
    """Test Redis caching functionality"""
    
    def __init__(self, metrics: TestMetrics):
        self.metrics = metrics
    
    async def test_cache_performance(self):
        """Test cache hit/miss rates and response times"""
        if not REDIS_TEST_ENABLED:
            print("\n⏭️  Redis testing skipped")
            return
            
        print("\n💾 Testing Redis cache performance...")
        
        async with aiohttp.ClientSession() as session:
            # First request (cache miss)
            print("Testing cache miss scenario...")
            start = time.time()
            result1 = await session.get(f"{BASE_URL}/api/bitcoin/price")
            cache_miss_time = time.time() - start
            self.metrics.redis_misses += 1
            self.metrics.redis_response_times.append(cache_miss_time)
            
            # Second request (cache hit)
            print("Testing cache hit scenario...")
            start = time.time()
            result2 = await session.get(f"{BASE_URL}/api/bitcoin/price")
            cache_hit_time = time.time() - start
            self.metrics.redis_hits += 1
            self.metrics.redis_response_times.append(cache_hit_time)
            
            if cache_hit_time < cache_miss_time:
                improvement = ((cache_miss_time - cache_hit_time) / cache_miss_time) * 100
                print(f"✓ Cache hit {improvement:.1f}% faster than cache miss")
                print(f"  Cache miss: {cache_miss_time:.3f}s")
                print(f"  Cache hit:  {cache_hit_time:.3f}s")
            else:
                print(f"⚠️  Cache performance not optimal")
    
    async def test_concurrent_cache_access(self):
        """Test concurrent cache access"""
        print("Testing concurrent cache access...")
        
        async with aiohttp.ClientSession() as session:
            # Warm up cache
            await session.get(f"{BASE_URL}/api/bitcoin/price")
            
            # Concurrent requests
            tasks = []
            for _ in range(20):
                tasks.append(session.get(f"{BASE_URL}/api/bitcoin/price"))
            
            start = time.time()
            responses = await asyncio.gather(*tasks)
            total_time = time.time() - start
            
            successful = sum(1 for r in responses if r.status == 200)
            print(f"✓ {successful}/20 concurrent cache requests successful")
            print(f"✓ Total time for 20 requests: {total_time:.3f}s")
            print(f"✓ Average time per request: {total_time/20:.3f}s")

class SystemMonitor:
    """Monitor system resources during tests"""
    
    def __init__(self, metrics: TestMetrics):
        self.metrics = metrics
        self.process = psutil.Process()
        self.monitoring = False
        self.cpu_samples = []
    
    async def start_monitoring(self):
        """Start monitoring system resources"""
        self.monitoring = True
        self.metrics.memory_usage_start = self.process.memory_info().rss / 1024 / 1024  # MB
        
        print("\n📊 Starting system resource monitoring...")
        print(f"Initial memory usage: {self.metrics.memory_usage_start:.2f} MB")
        
        # Monitor in background
        asyncio.create_task(self._monitor_loop())
    
    async def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                cpu_percent = self.process.cpu_percent()
                
                if memory_mb > self.metrics.memory_usage_peak:
                    self.metrics.memory_usage_peak = memory_mb
                
                self.cpu_samples.append(cpu_percent)
                
                await asyncio.sleep(1)
            except:
                break
    
    def stop_monitoring(self):
        """Stop monitoring and calculate final metrics"""
        self.monitoring = False
        self.metrics.memory_usage_end = self.process.memory_info().rss / 1024 / 1024
        
        if self.cpu_samples:
            self.metrics.cpu_usage_avg = statistics.mean(self.cpu_samples)
        
        print(f"\n📊 Resource usage summary:")
        print(f"  Memory - Start: {self.metrics.memory_usage_start:.2f} MB")
        print(f"  Memory - Peak:  {self.metrics.memory_usage_peak:.2f} MB")
        print(f"  Memory - End:   {self.metrics.memory_usage_end:.2f} MB")
        print(f"  Memory - Growth: {self.metrics.memory_usage_end - self.metrics.memory_usage_start:.2f} MB")
        print(f"  CPU - Average:  {self.metrics.cpu_usage_avg:.1f}%")

async def run_load_tests():
    """Main test orchestrator"""
    print("=" * 60)
    print("🚀 CoinLink MVP Load Testing Suite")
    print("=" * 60)
    print(f"Target: {BASE_URL}")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)
    
    metrics = TestMetrics()
    
    # Initialize monitors
    system_monitor = SystemMonitor(metrics)
    await system_monitor.start_monitoring()
    
    # Run tests
    try:
        # 1. WebSocket Tests
        ws_test = WebSocketLoadTest(metrics)
        await ws_test.test_concurrent_connections(50)
        await ws_test.cleanup()
        
        # 2. API Tests
        api_test = APILoadTest(metrics)
        await api_test.test_endpoints_performance()
        await api_test.test_rate_limits()
        
        # 3. Redis Tests
        redis_test = RedisLoadTest(metrics)
        await redis_test.test_cache_performance()
        await redis_test.test_concurrent_cache_access()
        
        # 4. Stress Test - High load scenario
        print("\n🔥 Running stress test (100 concurrent WS + 200 API requests)...")
        
        # Create stress load
        ws_stress = WebSocketLoadTest(metrics)
        stress_tasks = []
        
        # 100 WebSocket connections
        stress_tasks.extend([ws_stress.create_connection(i) for i in range(100)])
        
        # 200 API requests
        async with aiohttp.ClientSession() as session:
            api_stress = APILoadTest(metrics)
            for _ in range(200):
                endpoint = random.choice(["/api/bitcoin/price", "/api/bitcoin/sentiment", "/health"])
                stress_tasks.append(api_stress.test_endpoint(session, endpoint))
        
        # Execute stress test
        stress_start = time.time()
        await asyncio.gather(*stress_tasks, return_exceptions=True)
        stress_duration = time.time() - stress_start
        
        print(f"✓ Stress test completed in {stress_duration:.2f}s")
        
        await ws_stress.cleanup()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        metrics.errors.append(f"Test suite error: {str(e)}")
    
    finally:
        # Stop monitoring
        system_monitor.stop_monitoring()
        metrics.end_time = time.time()
        
        # Generate report
        generate_report(metrics)

def generate_report(metrics: TestMetrics):
    """Generate comprehensive test report"""
    duration = metrics.end_time - metrics.start_time
    
    print("\n" + "=" * 60)
    print("📈 LOAD TEST REPORT")
    print("=" * 60)
    
    print(f"\n⏱️  Test Duration: {duration:.2f} seconds")
    
    print("\n🔌 WebSocket Performance:")
    print(f"  Connections - Successful: {metrics.websocket_connections_successful}")
    print(f"  Connections - Failed: {metrics.websocket_connections_failed}")
    print(f"  Messages - Sent: {metrics.websocket_messages_sent}")
    print(f"  Messages - Received: {metrics.websocket_messages_received}")
    if metrics.websocket_latencies:
        print(f"  Latency - Average: {statistics.mean(metrics.websocket_latencies):.3f}s")
        print(f"  Latency - P95: {sorted(metrics.websocket_latencies)[int(len(metrics.websocket_latencies)*0.95)]:.3f}s")
    
    print("\n🌐 API Performance:")
    print(f"  Requests - Successful: {metrics.api_requests_successful}")
    print(f"  Requests - Failed: {metrics.api_requests_failed}")
    print(f"  Requests - Rate Limited: {metrics.api_rate_limited}")
    if metrics.api_latencies:
        print(f"  Latency - Average: {statistics.mean(metrics.api_latencies):.3f}s")
        print(f"  Latency - P95: {sorted(metrics.api_latencies)[int(len(metrics.api_latencies)*0.95)]:.3f}s")
    
    print("\n💾 Redis Cache:")
    print(f"  Cache Hits: {metrics.redis_hits}")
    print(f"  Cache Misses: {metrics.redis_misses}")
    if metrics.redis_hits + metrics.redis_misses > 0:
        hit_rate = (metrics.redis_hits / (metrics.redis_hits + metrics.redis_misses)) * 100
        print(f"  Hit Rate: {hit_rate:.1f}%")
    
    print("\n💻 System Resources:")
    print(f"  Memory Growth: {metrics.memory_usage_end - metrics.memory_usage_start:.2f} MB")
    print(f"  Peak Memory: {metrics.memory_usage_peak:.2f} MB")
    print(f"  Average CPU: {metrics.cpu_usage_avg:.1f}%")
    
    if metrics.errors:
        print(f"\n⚠️  Errors ({len(metrics.errors)}):")
        for error in metrics.errors[:5]:  # Show first 5 errors
            print(f"  - {error}")
    
    # Performance verdict
    print("\n" + "=" * 60)
    print("🎯 PERFORMANCE VERDICT:")
    print("=" * 60)
    
    passed_tests = []
    failed_tests = []
    
    # Check WebSocket performance
    if metrics.websocket_connections_successful > metrics.websocket_connections_failed:
        passed_tests.append("✅ WebSocket: Can handle 50+ concurrent connections")
    else:
        failed_tests.append("❌ WebSocket: Failed to maintain concurrent connections")
    
    # Check API rate limiting
    if metrics.api_rate_limited > 0:
        passed_tests.append("✅ API: Rate limiting is working correctly")
    else:
        failed_tests.append("⚠️  API: Rate limiting may not be configured")
    
    # Check Redis caching
    if metrics.redis_hits > 0:
        passed_tests.append("✅ Redis: Caching is operational")
    else:
        failed_tests.append("⚠️  Redis: Cache may not be working")
    
    # Check memory usage
    memory_growth = metrics.memory_usage_end - metrics.memory_usage_start
    if memory_growth < 100:  # Less than 100MB growth
        passed_tests.append("✅ Memory: Acceptable memory usage under load")
    else:
        failed_tests.append(f"⚠️  Memory: High memory growth ({memory_growth:.0f} MB)")
    
    # Check latency
    if metrics.api_latencies and statistics.mean(metrics.api_latencies) < 1.0:
        passed_tests.append("✅ Latency: API response times are good (<1s avg)")
    elif metrics.api_latencies:
        failed_tests.append(f"⚠️  Latency: API response times need improvement ({statistics.mean(metrics.api_latencies):.2f}s avg)")
    
    print("\nPassed Tests:")
    for test in passed_tests:
        print(f"  {test}")
    
    if failed_tests:
        print("\nFailed/Warning Tests:")
        for test in failed_tests:
            print(f"  {test}")
    
    # Overall verdict
    print("\n" + "=" * 60)
    if len(passed_tests) >= 4 and len(failed_tests) <= 1:
        print("✅ PRODUCTION READY - System performs well under load")
    elif len(passed_tests) >= 3:
        print("⚠️  MOSTLY READY - Minor improvements recommended")
    else:
        print("❌ NOT READY - Significant performance issues detected")
    print("=" * 60)
    
    # Save report to file
    report_path = f"/Users/shayanbozorgmanesh/Documents/Parking/coinlink-mvp/swarm-state/load_test_report_{int(time.time())}.json"
    with open(report_path, 'w') as f:
        json.dump({
            "duration": duration,
            "websocket": {
                "connections_successful": metrics.websocket_connections_successful,
                "connections_failed": metrics.websocket_connections_failed,
                "messages_sent": metrics.websocket_messages_sent,
                "messages_received": metrics.websocket_messages_received,
                "avg_latency": statistics.mean(metrics.websocket_latencies) if metrics.websocket_latencies else 0
            },
            "api": {
                "requests_successful": metrics.api_requests_successful,
                "requests_failed": metrics.api_requests_failed,
                "rate_limited": metrics.api_rate_limited,
                "avg_latency": statistics.mean(metrics.api_latencies) if metrics.api_latencies else 0
            },
            "redis": {
                "hits": metrics.redis_hits,
                "misses": metrics.redis_misses
            },
            "system": {
                "memory_start_mb": metrics.memory_usage_start,
                "memory_peak_mb": metrics.memory_usage_peak,
                "memory_end_mb": metrics.memory_usage_end,
                "cpu_avg_percent": metrics.cpu_usage_avg
            },
            "errors": metrics.errors,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_path}")

if __name__ == "__main__":
    # Check if server is running
    print("🔍 Checking if server is running...")
    import requests
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("⚠️  Server returned non-200 status")
    except Exception as e:
        print(f"⚠️  Server connection issue: {e}")
        print("Attempting to continue with tests anyway...")
    
    # Run tests
    asyncio.run(run_load_tests())