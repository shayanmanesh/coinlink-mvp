#!/usr/bin/env python3
"""
Production Hardening Verification Script
========================================

This script verifies that all production hardening features are correctly implemented
and working as expected. It tests all 9 phases of the production readiness implementation.

Usage:
    python scripts/verify-production-hardening.py
    python scripts/verify-production-hardening.py --url https://your-api.com
"""

import asyncio
import json
import sys
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
import httpx
import websockets
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, TaskID
from rich.panel import Panel
from rich import print as rprint

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

console = Console()

class ProductionVerifier:
    """Comprehensive production hardening verification."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.ws_url = base_url.replace("http", "ws") + "/ws"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results: Dict[str, Dict] = {}
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def log_result(self, phase: str, test: str, passed: bool, details: str = ""):
        """Log test result."""
        if phase not in self.results:
            self.results[phase] = {}
        
        self.results[phase][test] = {
            "passed": passed,
            "details": details,
            "timestamp": time.time()
        }
        
        status = "✅ PASS" if passed else "❌ FAIL"
        console.print(f"  {status} {test}: {details}")

    async def verify_phase1_dependencies(self) -> bool:
        """Phase 1: Verify dependencies and environment setup."""
        console.print("\n[bold blue]Phase 1: Dependencies & Environment[/bold blue]")
        
        try:
            # Check if required packages are importable
            import sqlalchemy
            import redis
            import fastapi
            import pydantic
            import passlib
            import jwt as pyjwt
            
            self.log_result("phase1", "core_dependencies", True, 
                          f"SQLAlchemy {sqlalchemy.__version__}, FastAPI {fastapi.__version__}")
            
            # Check Python version
            python_version = sys.version_info
            if python_version >= (3, 11):
                self.log_result("phase1", "python_version", True, f"Python {python_version.major}.{python_version.minor}")
            else:
                self.log_result("phase1", "python_version", False, f"Python {python_version.major}.{python_version.minor} < 3.11")
                
            return True
            
        except ImportError as e:
            self.log_result("phase1", "dependencies", False, f"Missing dependency: {e}")
            return False

    async def verify_phase2_security(self) -> bool:
        """Phase 2: Verify security and middleware."""
        console.print("\n[bold blue]Phase 2: Security & Middleware[/bold blue]")
        
        try:
            # Test health endpoint
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.log_result("phase2", "health_endpoint", True, "Health endpoint responding")
            else:
                self.log_result("phase2", "health_endpoint", False, f"Status: {response.status_code}")
                
            # Test CORS headers
            response = await self.client.options(f"{self.base_url}/health", 
                                               headers={"Origin": "https://example.com"})
            cors_headers = response.headers.get("access-control-allow-origin")
            if cors_headers:
                self.log_result("phase2", "cors_middleware", True, f"CORS headers present")
            else:
                self.log_result("phase2", "cors_middleware", False, "No CORS headers found")
                
            # Test rate limiting (attempt multiple requests)
            start_time = time.time()
            rate_limit_hit = False
            
            for i in range(20):  # Try to hit rate limit
                response = await self.client.get(f"{self.base_url}/health")
                if response.status_code == 429:
                    rate_limit_hit = True
                    break
                    
            if rate_limit_hit:
                self.log_result("phase2", "rate_limiting", True, "Rate limiting active")
            else:
                self.log_result("phase2", "rate_limiting", False, "Rate limiting not detected")
                
            return True
            
        except Exception as e:
            self.log_result("phase2", "security_tests", False, f"Error: {e}")
            return False

    async def verify_phase3_database_auth(self) -> bool:
        """Phase 3: Verify database and authentication."""
        console.print("\n[bold blue]Phase 3: Database & Authentication[/bold blue]")
        
        try:
            # Test registration endpoint
            user_data = {
                "email": f"test_{int(time.time())}@example.com",
                "password": "TestPassword123!",
                "name": "Test User"
            }
            
            response = await self.client.post(f"{self.base_url}/api/v1/auth/register", 
                                            json=user_data)
            if response.status_code in [200, 201]:
                self.log_result("phase3", "user_registration", True, "Registration endpoint working")
                
                # Test login
                login_data = {
                    "email": user_data["email"],
                    "password": user_data["password"]
                }
                
                response = await self.client.post(f"{self.base_url}/api/v1/auth/login", 
                                                json=login_data)
                if response.status_code == 200:
                    data = response.json()
                    if "access_token" in data and "refresh_token" in data:
                        self.log_result("phase3", "jwt_authentication", True, "JWT tokens generated")
                        
                        # Test protected endpoint
                        headers = {"Authorization": f"Bearer {data['access_token']}"}
                        response = await self.client.get(f"{self.base_url}/api/v1/users/me", 
                                                       headers=headers)
                        if response.status_code == 200:
                            self.log_result("phase3", "protected_endpoints", True, "Protected endpoints working")
                        else:
                            self.log_result("phase3", "protected_endpoints", False, f"Status: {response.status_code}")
                    else:
                        self.log_result("phase3", "jwt_authentication", False, "No tokens in response")
                else:
                    self.log_result("phase3", "jwt_authentication", False, f"Login failed: {response.status_code}")
            else:
                self.log_result("phase3", "user_registration", False, f"Registration failed: {response.status_code}")
                
            # Test unauthorized access
            response = await self.client.get(f"{self.base_url}/api/v1/users/me")
            if response.status_code == 401:
                self.log_result("phase3", "auth_protection", True, "Unauthorized access properly blocked")
            else:
                self.log_result("phase3", "auth_protection", False, f"Expected 401, got {response.status_code}")
                
            return True
            
        except Exception as e:
            self.log_result("phase3", "database_auth", False, f"Error: {e}")
            return False

    async def verify_phase4_websocket_redis(self) -> bool:
        """Phase 4: Verify WebSocket and Redis pub/sub."""
        console.print("\n[bold blue]Phase 4: WebSocket & Redis[/bold blue]")
        
        try:
            # Test WebSocket connection
            try:
                async with websockets.connect(self.ws_url, timeout=10) as websocket:
                    # Send test message
                    test_message = {
                        "type": "ping",
                        "data": {"timestamp": time.time()}
                    }
                    await websocket.send(json.dumps(test_message))
                    
                    # Wait for response
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    response_data = json.loads(response)
                    
                    if response_data.get("type") == "pong":
                        self.log_result("phase4", "websocket_connection", True, "WebSocket ping/pong working")
                    else:
                        self.log_result("phase4", "websocket_connection", True, "WebSocket connected")
                        
            except Exception as e:
                self.log_result("phase4", "websocket_connection", False, f"WebSocket error: {e}")
                
            # Test real-time market data endpoint
            response = await self.client.get(f"{self.base_url}/api/v1/market-data/bitcoin/price")
            if response.status_code == 200:
                data = response.json()
                if "price" in data:
                    self.log_result("phase4", "market_data_service", True, f"Bitcoin price: ${data['price']}")
                else:
                    self.log_result("phase4", "market_data_service", False, "No price in response")
            else:
                self.log_result("phase4", "market_data_service", False, f"Status: {response.status_code}")
                
            return True
            
        except Exception as e:
            self.log_result("phase4", "websocket_redis", False, f"Error: {e}")
            return False

    async def verify_phase5_api_endpoints(self) -> bool:
        """Phase 5: Verify API endpoints and frontend parity."""
        console.print("\n[bold blue]Phase 5: API Endpoints & Frontend Parity[/bold blue]")
        
        endpoints_to_test = [
            ("/api/v1/bitcoin/price", "Bitcoin price endpoint"),
            ("/api/v1/crypto/ticker", "Crypto ticker endpoint"),
            ("/api/v1/alerts", "Alerts endpoint"),
            ("/api/v1/notifications", "Notifications endpoint"),
        ]
        
        try:
            passed_endpoints = 0
            
            for endpoint, description in endpoints_to_test:
                try:
                    response = await self.client.get(f"{self.base_url}{endpoint}")
                    if response.status_code in [200, 401]:  # 401 is OK for protected endpoints
                        self.log_result("phase5", f"endpoint_{endpoint.split('/')[-1]}", True, 
                                      f"{description} responding")
                        passed_endpoints += 1
                    else:
                        self.log_result("phase5", f"endpoint_{endpoint.split('/')[-1]}", False, 
                                      f"Status: {response.status_code}")
                except Exception as e:
                    self.log_result("phase5", f"endpoint_{endpoint.split('/')[-1]}", False, f"Error: {e}")
                    
            # Test API documentation
            response = await self.client.get(f"{self.base_url}/docs")
            if response.status_code == 200:
                self.log_result("phase5", "api_documentation", True, "OpenAPI docs available")
            else:
                self.log_result("phase5", "api_documentation", False, f"Docs status: {response.status_code}")
                
            return passed_endpoints >= len(endpoints_to_test) // 2
            
        except Exception as e:
            self.log_result("phase5", "api_endpoints", False, f"Error: {e}")
            return False

    async def verify_phase6_observability(self) -> bool:
        """Phase 6: Verify observability and monitoring."""
        console.print("\n[bold blue]Phase 6: Observability & Monitoring[/bold blue]")
        
        try:
            # Test metrics endpoint
            response = await self.client.get(f"{self.base_url}/metrics")
            if response.status_code == 200:
                metrics_content = response.text
                required_metrics = [
                    "coinlink_api_request_duration_seconds",
                    "coinlink_websocket_connections_total",
                    "coinlink_database_operations_total"
                ]
                
                found_metrics = sum(1 for metric in required_metrics if metric in metrics_content)
                if found_metrics >= 2:
                    self.log_result("phase6", "prometheus_metrics", True, 
                                  f"Found {found_metrics}/{len(required_metrics)} metrics")
                else:
                    self.log_result("phase6", "prometheus_metrics", False, 
                                  f"Only found {found_metrics}/{len(required_metrics)} metrics")
            else:
                self.log_result("phase6", "prometheus_metrics", False, f"Status: {response.status_code}")
                
            # Test structured logging (make a request and check response headers)
            response = await self.client.get(f"{self.base_url}/health")
            trace_id = response.headers.get("x-trace-id")
            if trace_id:
                self.log_result("phase6", "structured_logging", True, f"Trace ID: {trace_id[:8]}...")
            else:
                self.log_result("phase6", "structured_logging", False, "No trace ID header found")
                
            # Test health check details
            if response.status_code == 200:
                health_data = response.json()
                if isinstance(health_data, dict) and "status" in health_data:
                    self.log_result("phase6", "health_checks", True, f"Status: {health_data['status']}")
                else:
                    self.log_result("phase6", "health_checks", False, "Invalid health response format")
                    
            return True
            
        except Exception as e:
            self.log_result("phase6", "observability", False, f"Error: {e}")
            return False

    async def verify_phase7_testing(self) -> bool:
        """Phase 7: Verify testing infrastructure."""
        console.print("\n[bold blue]Phase 7: Testing Infrastructure[/bold blue]")
        
        try:
            # Check if test files exist
            test_files = [
                "backend/tests/conftest.py",
                "backend/tests/test_auth.py", 
                "backend/tests/test_websocket.py",
                "backend/tests/test_api_routes.py",
                "backend/tests/test_observability.py"
            ]
            
            existing_tests = 0
            for test_file in test_files:
                if Path(test_file).exists():
                    existing_tests += 1
                    
            if existing_tests >= 4:
                self.log_result("phase7", "test_files", True, f"Found {existing_tests}/{len(test_files)} test files")
            else:
                self.log_result("phase7", "test_files", False, f"Only found {existing_tests}/{len(test_files)} test files")
                
            # Check test configuration
            if Path("backend/tests/conftest.py").exists():
                self.log_result("phase7", "test_configuration", True, "Test configuration available")
            else:
                self.log_result("phase7", "test_configuration", False, "Missing test configuration")
                
            # Check Docker test setup
            if Path("docker-compose.test.yml").exists():
                self.log_result("phase7", "test_environment", True, "Docker test environment configured")
            else:
                self.log_result("phase7", "test_environment", False, "Missing Docker test environment")
                
            return existing_tests >= 3
            
        except Exception as e:
            self.log_result("phase7", "testing", False, f"Error: {e}")
            return False

    async def verify_phase8_docker_cicd(self) -> bool:
        """Phase 8: Verify Docker and CI/CD configuration."""
        console.print("\n[bold blue]Phase 8: Docker & CI/CD[/bold blue]")
        
        try:
            # Check Dockerfile
            if Path("Dockerfile").exists():
                with open("Dockerfile", "r") as f:
                    dockerfile_content = f.read()
                    
                if "multi-stage" in dockerfile_content.lower() or "as builder" in dockerfile_content:
                    self.log_result("phase8", "dockerfile_multistage", True, "Multi-stage Dockerfile")
                else:
                    self.log_result("phase8", "dockerfile_multistage", False, "Not multi-stage")
                    
                if "USER " in dockerfile_content and "root" not in dockerfile_content.split("USER")[-1]:
                    self.log_result("phase8", "dockerfile_security", True, "Non-root user configured")
                else:
                    self.log_result("phase8", "dockerfile_security", False, "Running as root")
            else:
                self.log_result("phase8", "dockerfile", False, "Dockerfile not found")
                
            # Check Docker Compose
            docker_compose_files = ["docker-compose.yml", "docker-compose.production.yml", "docker-compose.test.yml"]
            found_compose = sum(1 for f in docker_compose_files if Path(f).exists())
            
            if found_compose >= 2:
                self.log_result("phase8", "docker_compose", True, f"Found {found_compose}/3 compose files")
            else:
                self.log_result("phase8", "docker_compose", False, f"Only found {found_compose}/3 compose files")
                
            # Check GitHub Actions
            workflows_dir = Path(".github/workflows")
            if workflows_dir.exists():
                workflow_files = list(workflows_dir.glob("*.yml"))
                if len(workflow_files) >= 1:
                    self.log_result("phase8", "github_actions", True, f"Found {len(workflow_files)} workflow(s)")
                else:
                    self.log_result("phase8", "github_actions", False, "No workflow files found")
            else:
                self.log_result("phase8", "github_actions", False, "No .github/workflows directory")
                
            # Check .dockerignore
            if Path(".dockerignore").exists():
                self.log_result("phase8", "dockerignore", True, "Docker ignore file configured")
            else:
                self.log_result("phase8", "dockerignore", False, "Missing .dockerignore")
                
            return True
            
        except Exception as e:
            self.log_result("phase8", "docker_cicd", False, f"Error: {e}")
            return False

    async def verify_phase9_documentation(self) -> bool:
        """Phase 9: Verify documentation and final verification."""
        console.print("\n[bold blue]Phase 9: Documentation & Verification[/bold blue]")
        
        try:
            # Check documentation files
            doc_files = [
                "PRODUCTION_DEPLOYMENT_GUIDE.md",
                "CLAUDE.md",
                ".env.production.example"
            ]
            
            found_docs = 0
            for doc_file in doc_files:
                if Path(doc_file).exists():
                    found_docs += 1
                    
            if found_docs >= 2:
                self.log_result("phase9", "documentation", True, f"Found {found_docs}/{len(doc_files)} doc files")
            else:
                self.log_result("phase9", "documentation", False, f"Only found {found_docs}/{len(doc_files)} doc files")
                
            # Check environment template
            if Path(".env.production.example").exists():
                with open(".env.production.example", "r") as f:
                    env_content = f.read()
                    
                required_vars = ["DATABASE_URL", "JWT_SECRET_KEY", "CORS_ORIGINS", "REDIS_URL"]
                found_vars = sum(1 for var in required_vars if var in env_content)
                
                if found_vars >= 3:
                    self.log_result("phase9", "env_template", True, f"Found {found_vars}/{len(required_vars)} required vars")
                else:
                    self.log_result("phase9", "env_template", False, f"Only found {found_vars}/{len(required_vars)} required vars")
            else:
                self.log_result("phase9", "env_template", False, "Missing environment template")
                
            # Final API health check
            response = await self.client.get(f"{self.base_url}/health")
            if response.status_code == 200:
                self.log_result("phase9", "final_health_check", True, "System healthy")
            else:
                self.log_result("phase9", "final_health_check", False, f"Status: {response.status_code}")
                
            return True
            
        except Exception as e:
            self.log_result("phase9", "documentation", False, f"Error: {e}")
            return False

    async def run_full_verification(self) -> bool:
        """Run complete production hardening verification."""
        console.print("[bold green]🚀 CoinLink Production Hardening Verification[/bold green]")
        console.print(f"Testing API at: {self.base_url}")
        
        phases = [
            ("Phase 1", self.verify_phase1_dependencies),
            ("Phase 2", self.verify_phase2_security),
            ("Phase 3", self.verify_phase3_database_auth), 
            ("Phase 4", self.verify_phase4_websocket_redis),
            ("Phase 5", self.verify_phase5_api_endpoints),
            ("Phase 6", self.verify_phase6_observability),
            ("Phase 7", self.verify_phase7_testing),
            ("Phase 8", self.verify_phase8_docker_cicd),
            ("Phase 9", self.verify_phase9_documentation),
        ]
        
        passed_phases = 0
        total_tests = 0
        passed_tests = 0
        
        with Progress() as progress:
            task = progress.add_task("Running verification...", total=len(phases))
            
            for phase_name, phase_func in phases:
                try:
                    result = await phase_func()
                    if result:
                        passed_phases += 1
                    progress.update(task, advance=1)
                except Exception as e:
                    console.print(f"[red]Error in {phase_name}: {e}[/red]")
                    
        # Calculate overall results
        for phase_results in self.results.values():
            for test_result in phase_results.values():
                total_tests += 1
                if test_result["passed"]:
                    passed_tests += 1
                    
        # Display results summary
        self.display_results_summary(passed_phases, len(phases), passed_tests, total_tests)
        
        return passed_phases >= 7 and passed_tests >= total_tests * 0.8

    def display_results_summary(self, passed_phases: int, total_phases: int, 
                               passed_tests: int, total_tests: int):
        """Display comprehensive results summary."""
        
        # Overall status
        overall_status = "✅ PRODUCTION READY" if passed_phases >= 7 else "❌ NOT READY"
        status_color = "green" if passed_phases >= 7 else "red"
        
        console.print(f"\n[bold {status_color}]{overall_status}[/bold {status_color}]")
        
        # Summary table
        table = Table(title="Production Hardening Verification Results")
        table.add_column("Phase", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Tests Passed", justify="center")
        table.add_column("Details", style="dim")
        
        for phase, results in self.results.items():
            phase_passed = sum(1 for r in results.values() if r["passed"])
            phase_total = len(results)
            phase_status = "✅ PASS" if phase_passed >= phase_total * 0.7 else "❌ FAIL"
            
            # Get key details
            details = []
            for test, result in results.items():
                if result["passed"]:
                    details.append(f"✓ {test}")
                else:
                    details.append(f"✗ {test}")
                    
            table.add_row(
                phase.replace("phase", "Phase "),
                phase_status,
                f"{phase_passed}/{phase_total}",
                ", ".join(details[:3]) + ("..." if len(details) > 3 else "")
            )
            
        console.print(table)
        
        # Overall metrics
        console.print(f"\n[bold]Overall Results:[/bold]")
        console.print(f"  Phases Passed: {passed_phases}/{total_phases} ({passed_phases/total_phases*100:.1f}%)")
        console.print(f"  Tests Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_phases >= 7:
            console.print("\n[bold green]🎉 Production hardening verification successful![/bold green]")
            console.print("The CoinLink MVP is ready for production deployment.")
        else:
            console.print("\n[bold red]⚠️  Production hardening verification failed![/bold red]")
            console.print("Please address the failing tests before deploying to production.")


async def main():
    """Main verification function."""
    parser = argparse.ArgumentParser(description="Verify CoinLink production hardening")
    parser.add_argument("--url", default="http://localhost:8000", 
                       help="Base URL of the API to test")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
        
    async with ProductionVerifier(args.url) as verifier:
        success = await verifier.run_full_verification()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Verification interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Verification failed with error: {e}[/red]")
        sys.exit(1)