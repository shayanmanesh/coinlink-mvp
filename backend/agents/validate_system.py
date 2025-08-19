#!/usr/bin/env python3
"""
Agent System Validation Script
Comprehensive validation of the Claude Code agent system
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from agents.claude_agent_interface import claude_agents
from agents.monitoring import agent_monitor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentSystemValidator:
    """Comprehensive validation of the agent system"""
    
    def __init__(self):
        self.validation_results = {
            "directory_structure": {},
            "agent_files": {},
            "agent_discovery": {},
            "api_integration": {},
            "monitoring_system": {},
            "overall_status": "unknown"
        }
    
    async def run_validation(self) -> Dict[str, Any]:
        """Run complete validation suite"""
        logger.info("🚀 Starting Agent System Validation")
        
        try:
            # 1. Validate directory structure
            await self._validate_directory_structure()
            
            # 2. Validate agent files
            await self._validate_agent_files()
            
            # 3. Validate agent discovery
            await self._validate_agent_discovery()
            
            # 4. Validate API integration
            await self._validate_api_integration()
            
            # 5. Validate monitoring system
            await self._validate_monitoring_system()
            
            # 6. Calculate overall status
            self._calculate_overall_status()
            
            logger.info("✅ Agent System Validation Complete")
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            self.validation_results["overall_status"] = "failed"
            self.validation_results["error"] = str(e)
        
        return self.validation_results
    
    async def _validate_directory_structure(self):
        """Validate the .claude/agents directory structure"""
        logger.info("📁 Validating directory structure...")
        
        project_root = Path.cwd()
        claude_dir = project_root / ".claude"
        agents_dir = claude_dir / "agents"
        settings_file = claude_dir / "settings.json"
        
        results = {
            "project_root_exists": project_root.exists(),
            "claude_directory_exists": claude_dir.exists(),
            "agents_directory_exists": agents_dir.exists(),
            "settings_file_exists": settings_file.exists(),
            "permissions": "unknown"
        }
        
        if agents_dir.exists():
            try:
                # Test write permissions
                test_file = agents_dir / ".test_permissions"
                test_file.write_text("test")
                test_file.unlink()
                results["permissions"] = "writable"
            except Exception as e:
                results["permissions"] = f"read_only: {e}"
        
        self.validation_results["directory_structure"] = results
        
        if all([results["claude_directory_exists"], results["agents_directory_exists"], results["settings_file_exists"]]):
            logger.info("✅ Directory structure validation passed")
        else:
            logger.warning("⚠️ Directory structure validation failed")
    
    async def _validate_agent_files(self):
        """Validate individual agent files"""
        logger.info("📄 Validating agent files...")
        
        expected_agents = [
            "helios-orchestrator.md",
            "prometheus-frontend.md",
            "hephaestus-frontend.md", 
            "athena-ux.md",
            "prometheus-backend.md",
            "hephaestus-backend.md",
            "athena-api.md"
        ]
        
        agents_dir = Path.cwd() / ".claude" / "agents"
        results = {}
        
        for agent_file in expected_agents:
            file_path = agents_dir / agent_file
            agent_name = agent_file.replace(".md", "")
            
            file_result = {
                "exists": file_path.exists(),
                "readable": False,
                "has_frontmatter": False,
                "valid_yaml": False,
                "file_size": 0
            }
            
            if file_path.exists():
                try:
                    content = file_path.read_text()
                    file_result["readable"] = True
                    file_result["file_size"] = len(content)
                    
                    # Check for YAML frontmatter
                    if content.startswith("---"):
                        end_marker = content.find("---", 3)
                        if end_marker != -1:
                            file_result["has_frontmatter"] = True
                            
                            # Basic YAML validation
                            frontmatter = content[3:end_marker].strip()
                            if "name:" in frontmatter and "description:" in frontmatter:
                                file_result["valid_yaml"] = True
                
                except Exception as e:
                    file_result["error"] = str(e)
            
            results[agent_name] = file_result
        
        self.validation_results["agent_files"] = results
        
        valid_files = sum(1 for r in results.values() if r["valid_yaml"])
        logger.info(f"✅ Agent files validation: {valid_files}/{len(expected_agents)} valid")
    
    async def _validate_agent_discovery(self):
        """Validate agent discovery system"""
        logger.info("🔍 Validating agent discovery...")
        
        try:
            # Test agent discovery
            claude_agents._discover_agents()
            
            discovered_agents = list(claude_agents.agents.keys())
            expected_agents = [
                "helios-orchestrator",
                "prometheus-frontend",
                "hephaestus-frontend",
                "athena-ux",
                "prometheus-backend", 
                "hephaestus-backend",
                "athena-api"
            ]
            
            results = {
                "discovery_successful": True,
                "agents_discovered": len(discovered_agents),
                "expected_agents": len(expected_agents),
                "missing_agents": [a for a in expected_agents if a not in discovered_agents],
                "extra_agents": [a for a in discovered_agents if a not in expected_agents],
                "agent_details": {}
            }
            
            # Get details for each discovered agent
            for agent_name, agent_info in claude_agents.agents.items():
                results["agent_details"][agent_name] = {
                    "name": agent_info.name,
                    "description": agent_info.description[:100] + "..." if len(agent_info.description) > 100 else agent_info.description,
                    "tools_count": len(agent_info.tools),
                    "tools": agent_info.tools,
                    "status": agent_info.status
                }
            
            self.validation_results["agent_discovery"] = results
            
            if len(discovered_agents) == len(expected_agents) and len(results["missing_agents"]) == 0:
                logger.info("✅ Agent discovery validation passed")
            else:
                logger.warning(f"⚠️ Agent discovery issues: {len(results['missing_agents'])} missing agents")
        
        except Exception as e:
            self.validation_results["agent_discovery"] = {
                "discovery_successful": False,
                "error": str(e)
            }
            logger.error(f"❌ Agent discovery failed: {e}")
    
    async def _validate_api_integration(self):
        """Validate API integration"""
        logger.info("🌐 Validating API integration...")
        
        try:
            # Test basic agent interface methods
            system_status = claude_agents.get_system_status()
            available_agents = claude_agents.get_available_agents()
            
            results = {
                "interface_functional": True,
                "system_status": system_status,
                "available_agents_count": len(available_agents),
                "agents_list": [agent["name"] for agent in available_agents],
                "api_methods_working": True
            }
            
            # Test individual agent status
            agent_statuses = {}
            for agent_name in claude_agents.agents.keys():
                status = claude_agents.get_agent_status(agent_name)
                agent_statuses[agent_name] = status is not None
            
            results["individual_agent_status"] = agent_statuses
            
            self.validation_results["api_integration"] = results
            logger.info("✅ API integration validation passed")
        
        except Exception as e:
            self.validation_results["api_integration"] = {
                "interface_functional": False,
                "error": str(e)
            }
            logger.error(f"❌ API integration failed: {e}")
    
    async def _validate_monitoring_system(self):
        """Validate monitoring system"""
        logger.info("📊 Validating monitoring system...")
        
        try:
            # Test monitoring system
            system_health = agent_monitor.get_system_health()
            all_metrics = agent_monitor.get_all_agent_metrics()
            alerts = agent_monitor.get_performance_alerts()
            
            results = {
                "monitoring_functional": True,
                "system_health": system_health,
                "metrics_available": len(all_metrics) > 0,
                "alerts_system_working": isinstance(alerts, list),
                "health_score": system_health.get("health_score", 0)
            }
            
            self.validation_results["monitoring_system"] = results
            logger.info("✅ Monitoring system validation passed")
        
        except Exception as e:
            self.validation_results["monitoring_system"] = {
                "monitoring_functional": False,
                "error": str(e)
            }
            logger.error(f"❌ Monitoring system failed: {e}")
    
    def _calculate_overall_status(self):
        """Calculate overall validation status"""
        
        # Count successful validations
        validations = [
            self.validation_results["directory_structure"].get("agents_directory_exists", False),
            self.validation_results["agent_files"] and len([r for r in self.validation_results["agent_files"].values() if r.get("valid_yaml", False)]) >= 7,
            self.validation_results["agent_discovery"].get("discovery_successful", False),
            self.validation_results["api_integration"].get("interface_functional", False),
            self.validation_results["monitoring_system"].get("monitoring_functional", False)
        ]
        
        passed_validations = sum(validations)
        total_validations = len(validations)
        
        success_rate = passed_validations / total_validations
        
        if success_rate == 1.0:
            self.validation_results["overall_status"] = "excellent"
        elif success_rate >= 0.8:
            self.validation_results["overall_status"] = "good"
        elif success_rate >= 0.6:
            self.validation_results["overall_status"] = "acceptable"
        else:
            self.validation_results["overall_status"] = "failed"
        
        self.validation_results["success_rate"] = success_rate
        self.validation_results["passed_validations"] = passed_validations
        self.validation_results["total_validations"] = total_validations
    
    def print_validation_summary(self):
        """Print a formatted validation summary"""
        print("\n" + "="*80)
        print("🤖 CLAUDE CODE AGENT SYSTEM VALIDATION REPORT")
        print("="*80)
        
        status = self.validation_results["overall_status"]
        if status == "excellent":
            print("✅ OVERALL STATUS: EXCELLENT - All systems operational")
        elif status == "good":
            print("✅ OVERALL STATUS: GOOD - Minor issues detected")
        elif status == "acceptable":
            print("⚠️  OVERALL STATUS: ACCEPTABLE - Some issues need attention")
        else:
            print("❌ OVERALL STATUS: FAILED - Critical issues detected")
        
        print(f"\n📊 Success Rate: {self.validation_results.get('success_rate', 0):.1%}")
        print(f"✅ Passed: {self.validation_results.get('passed_validations', 0)}/{self.validation_results.get('total_validations', 0)} validations")
        
        # Directory Structure
        print(f"\n📁 Directory Structure: {'✅' if self.validation_results['directory_structure'].get('agents_directory_exists') else '❌'}")
        
        # Agent Files
        agent_files = self.validation_results.get("agent_files", {})
        valid_files = len([r for r in agent_files.values() if r.get("valid_yaml", False)])
        print(f"📄 Agent Files: {'✅' if valid_files >= 7 else '❌'} ({valid_files}/7 valid)")
        
        # Agent Discovery
        discovery = self.validation_results.get("agent_discovery", {})
        print(f"🔍 Agent Discovery: {'✅' if discovery.get('discovery_successful') else '❌'}")
        if discovery.get("agents_discovered"):
            print(f"   Discovered {discovery['agents_discovered']} agents")
        
        # API Integration
        api = self.validation_results.get("api_integration", {})
        print(f"🌐 API Integration: {'✅' if api.get('interface_functional') else '❌'}")
        
        # Monitoring System
        monitoring = self.validation_results.get("monitoring_system", {})
        print(f"📊 Monitoring System: {'✅' if monitoring.get('monitoring_functional') else '❌'}")
        
        print("\n" + "="*80)
        
        # Show discovered agents
        if discovery.get("agent_details"):
            print("\n🤖 DISCOVERED AGENTS:")
            print("-" * 80)
            for agent_name, details in discovery["agent_details"].items():
                print(f"  {agent_name}")
                print(f"    Tools: {', '.join(details['tools'][:5])}{'...' if len(details['tools']) > 5 else ''}")
                print(f"    Status: {details['status']}")
                print()

async def main():
    """Main validation function"""
    validator = AgentSystemValidator()
    results = await validator.run_validation()
    
    # Print summary
    validator.print_validation_summary()
    
    # Save detailed results
    output_file = Path.cwd() / "agent_validation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📄 Detailed results saved to: {output_file}")
    
    # Return appropriate exit code
    if results["overall_status"] in ["excellent", "good"]:
        return 0
    else:
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())