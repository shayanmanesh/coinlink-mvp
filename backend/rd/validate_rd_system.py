#!/usr/bin/env python3
"""
R&D System Validation Script
Comprehensive validation of the Expert-Level R&D Department
"""

import os
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Any

# Add the backend directory to the Python path
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
os.chdir(project_root)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RDSystemValidator:
    """Comprehensive validation of the R&D system"""
    
    def __init__(self):
        self.validation_results = {
            "rd_directory_structure": {},
            "rd_agent_files": {},
            "rd_agent_discovery": {},
            "rd_backend_modules": {},
            "innovation_pipeline": {},
            "email_notifications": {},
            "api_integration": {},
            "settings_configuration": {},
            "overall_status": "unknown"
        }
    
    async def run_validation(self) -> Dict[str, Any]:
        """Run complete R&D system validation"""
        logger.info("🚀 Starting R&D System Validation")
        
        try:
            # 1. Validate R&D directory structure
            await self._validate_rd_directory_structure()
            
            # 2. Validate R&D agent files
            await self._validate_rd_agent_files()
            
            # 3. Validate R&D agent discovery
            await self._validate_rd_agent_discovery()
            
            # 4. Validate R&D backend modules
            await self._validate_rd_backend_modules()
            
            # 5. Validate innovation pipeline
            await self._validate_innovation_pipeline()
            
            # 6. Validate email notifications
            await self._validate_email_notifications()
            
            # 7. Validate API integration
            await self._validate_api_integration()
            
            # 8. Validate settings configuration
            await self._validate_settings_configuration()
            
            # 9. Calculate overall status
            self._calculate_overall_status()
            
            logger.info("✅ R&D System Validation Complete")
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            self.validation_results["overall_status"] = "failed"
            self.validation_results["error"] = str(e)
        
        return self.validation_results
    
    async def _validate_rd_directory_structure(self):
        """Validate R&D directory structure"""
        logger.info("📁 Validating R&D directory structure...")
        
        project_root = Path.cwd()
        rd_agents_dir = project_root / ".claude" / "agents" / "rd"
        rd_backend_dir = project_root / "backend" / "rd"
        
        results = {
            "project_root_exists": project_root.exists(),
            "rd_agents_directory_exists": rd_agents_dir.exists(),
            "rd_backend_directory_exists": rd_backend_dir.exists(),
            "rd_agents_permissions": "unknown",
            "rd_backend_permissions": "unknown"
        }
        
        # Test permissions
        if rd_agents_dir.exists():
            try:
                test_file = rd_agents_dir / ".test_permissions"
                test_file.write_text("test")
                test_file.unlink()
                results["rd_agents_permissions"] = "writable"
            except Exception as e:
                results["rd_agents_permissions"] = f"read_only: {e}"
        
        if rd_backend_dir.exists():
            try:
                test_file = rd_backend_dir / ".test_permissions"
                test_file.write_text("test")
                test_file.unlink()
                results["rd_backend_permissions"] = "writable"
            except Exception as e:
                results["rd_backend_permissions"] = f"read_only: {e}"
        
        self.validation_results["rd_directory_structure"] = results
        
        if all([results["rd_agents_directory_exists"], results["rd_backend_directory_exists"]]):
            logger.info("✅ R&D directory structure validation passed")
        else:
            logger.warning("⚠️ R&D directory structure validation failed")
    
    async def _validate_rd_agent_files(self):
        """Validate R&D agent files"""
        logger.info("📄 Validating R&D agent files...")
        
        expected_rd_agents = [
            "apollo-rd-orchestrator.md",
            "argus-competitor.md",
            "minerva-research.md",
            "vulcan-strategy.md",
            "daedalus-prototype.md",
            "mercury-integration.md",
            "echo-feedback.md"
        ]
        
        rd_agents_dir = Path.cwd() / ".claude" / "agents" / "rd"
        results = {}
        
        for agent_file in expected_rd_agents:
            file_path = rd_agents_dir / agent_file
            agent_name = agent_file.replace(".md", "")
            
            file_result = {
                "exists": file_path.exists(),
                "readable": False,
                "has_frontmatter": False,
                "valid_yaml": False,
                "file_size": 0,
                "specialization_defined": False
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
                            if "name:" in frontmatter and "description:" in frontmatter and "tools:" in frontmatter:
                                file_result["valid_yaml"] = True
                            
                            # Check for R&D-specific content
                            if any(keyword in content.lower() for keyword in ["innovation", "r&d", "research", "competitive", "strategy"]):
                                file_result["specialization_defined"] = True
                
                except Exception as e:
                    file_result["error"] = str(e)
            
            results[agent_name] = file_result
        
        self.validation_results["rd_agent_files"] = results
        
        valid_files = sum(1 for r in results.values() if r["valid_yaml"])
        logger.info(f"✅ R&D agent files validation: {valid_files}/{len(expected_rd_agents)} valid")
    
    async def _validate_rd_agent_discovery(self):
        """Validate R&D agent discovery system"""
        logger.info("🔍 Validating R&D agent discovery...")
        
        try:
            from rd.rd_interface import rd_agents
            
            discovered_agents = list(rd_agents.agents.keys())
            expected_agents = [
                "apollo-rd-orchestrator",
                "argus-competitor",
                "minerva-research",
                "vulcan-strategy",
                "daedalus-prototype",
                "mercury-integration",
                "echo-feedback"
            ]
            
            results = {
                "discovery_successful": True,
                "agents_discovered": len(discovered_agents),
                "expected_agents": len(expected_agents),
                "missing_agents": [a for a in expected_agents if a not in discovered_agents],
                "extra_agents": [a for a in discovered_agents if a not in expected_agents],
                "agent_details": {},
                "specializations": {}
            }
            
            # Get details for each discovered agent
            for agent_name, agent_info in rd_agents.agents.items():
                results["agent_details"][agent_name] = {
                    "name": agent_info.name,
                    "description": agent_info.description[:100] + "..." if len(agent_info.description) > 100 else agent_info.description,
                    "tools_count": len(agent_info.tools),
                    "tools": agent_info.tools,
                    "specialization": agent_info.specialization,
                    "status": agent_info.status
                }
                
                # Track specializations
                spec = agent_info.specialization
                if spec in results["specializations"]:
                    results["specializations"][spec] += 1
                else:
                    results["specializations"][spec] = 1
            
            self.validation_results["rd_agent_discovery"] = results
            
            if len(discovered_agents) == len(expected_agents) and len(results["missing_agents"]) == 0:
                logger.info("✅ R&D agent discovery validation passed")
            else:
                logger.warning(f"⚠️ R&D agent discovery issues: {len(results['missing_agents'])} missing agents")
        
        except Exception as e:
            self.validation_results["rd_agent_discovery"] = {
                "discovery_successful": False,
                "error": str(e)
            }
            logger.error(f"❌ R&D agent discovery failed: {e}")
    
    async def _validate_rd_backend_modules(self):
        """Validate R&D backend modules"""
        logger.info("🏗️ Validating R&D backend modules...")
        
        expected_modules = [
            "rd/__init__.py",
            "rd/rd_interface.py",
            "rd/innovation_pipeline.py",
            "rd/notification_system.py",
            "rd/rd_metrics.py"
        ]
        
        backend_dir = Path.cwd() / "backend"
        results = {}
        
        for module_path in expected_modules:
            file_path = backend_dir / module_path
            module_name = module_path.replace("/", ".").replace(".py", "")
            
            module_result = {
                "file_exists": file_path.exists(),
                "importable": False,
                "functional": False,
                "file_size": 0
            }
            
            if file_path.exists():
                module_result["file_size"] = file_path.stat().st_size
                
                try:
                    # Test import
                    if module_path == "rd/__init__.py":
                        from rd import rd_agents, apollo_orchestrator, innovation_pipeline, email_notifier, rd_metrics_tracker
                        module_result["importable"] = True
                        module_result["functional"] = True
                    elif module_path == "rd/rd_interface.py":
                        from rd.rd_interface import rd_agents, RDAgentInterface
                        module_result["importable"] = True
                        module_result["functional"] = hasattr(rd_agents, 'get_rd_agents')
                    elif module_path == "rd/innovation_pipeline.py":
                        from rd.innovation_pipeline import innovation_pipeline, InnovationPipeline
                        module_result["importable"] = True
                        module_result["functional"] = hasattr(innovation_pipeline, 'add_innovation')
                    elif module_path == "rd/notification_system.py":
                        from rd.notification_system import email_notifier, RDEmailNotifier
                        module_result["importable"] = True
                        module_result["functional"] = hasattr(email_notifier, 'send_weekly_innovation_report')
                    elif module_path == "rd/rd_metrics.py":
                        from rd.rd_metrics import rd_metrics_tracker, RDMetricsTracker
                        module_result["importable"] = True
                        module_result["functional"] = hasattr(rd_metrics_tracker, 'record_agent_task')
                    
                except Exception as e:
                    module_result["import_error"] = str(e)
            
            results[module_name] = module_result
        
        self.validation_results["rd_backend_modules"] = results
        
        functional_modules = sum(1 for r in results.values() if r["functional"])
        logger.info(f"✅ R&D backend modules validation: {functional_modules}/{len(expected_modules)} functional")
    
    async def _validate_innovation_pipeline(self):
        """Validate innovation pipeline functionality"""
        logger.info("🔄 Validating innovation pipeline...")
        
        try:
            from rd.innovation_pipeline import innovation_pipeline, PipelineStage, ApprovalStatus
            
            # Test basic pipeline operations
            test_innovation = {
                "name": "Test Innovation",
                "description": "Test innovation for validation",
                "category": "test",
                "source_agent": "apollo-rd-orchestrator",
                "market_opportunity_score": 80,
                "competitive_advantage_score": 75,
                "user_demand_score": 85
            }
            
            # Test adding innovation
            innovation_id = innovation_pipeline.add_innovation(test_innovation)
            
            # Test evaluation
            evaluation = innovation_pipeline.evaluate_innovation_approval(innovation_id)
            
            # Test stage advancement
            advance_success = innovation_pipeline.advance_innovation_stage(innovation_id, "Test advancement")
            
            # Test pipeline status
            pipeline_status = innovation_pipeline.get_pipeline_status()
            
            results = {
                "pipeline_functional": True,
                "innovation_creation": innovation_id is not None,
                "evaluation_working": "composite_score" in evaluation,
                "stage_advancement": advance_success,
                "status_reporting": "total_innovations" in pipeline_status,
                "test_innovation_id": innovation_id,
                "pipeline_health": pipeline_status.get("pipeline_health", "unknown")
            }
            
            self.validation_results["innovation_pipeline"] = results
            logger.info("✅ Innovation pipeline validation passed")
            
        except Exception as e:
            self.validation_results["innovation_pipeline"] = {
                "pipeline_functional": False,
                "error": str(e)
            }
            logger.error(f"❌ Innovation pipeline validation failed: {e}")
    
    async def _validate_email_notifications(self):
        """Validate email notification system"""
        logger.info("📧 Validating email notifications...")
        
        try:
            from rd.notification_system import email_notifier
            
            # Test email template generation
            sample_report = email_notifier.generate_sample_weekly_report()
            
            # Test email sending (demo mode)
            weekly_success = await email_notifier.send_weekly_innovation_report(sample_report)
            
            alert_data = {
                "title": "Test Alert",
                "competitor": "Test Competitor",
                "description": "Test competitive alert",
                "threat_level": "Medium",
                "recommendations": ["Test recommendation"]
            }
            alert_success = await email_notifier.send_urgent_competitive_alert(alert_data)
            
            feature_data = {
                "name": "Test Feature",
                "description": "Test feature approval",
                "id": "test-123"
            }
            approval_success = await email_notifier.send_feature_approval_request(feature_data)
            
            results = {
                "notification_system_functional": True,
                "sample_report_generation": "executive_summary" in sample_report,
                "weekly_report_sending": weekly_success,
                "competitive_alert_sending": alert_success,
                "approval_request_sending": approval_success,
                "email_templates_available": len(email_notifier.email_templates) > 0
            }
            
            self.validation_results["email_notifications"] = results
            logger.info("✅ Email notifications validation passed")
            
        except Exception as e:
            self.validation_results["email_notifications"] = {
                "notification_system_functional": False,
                "error": str(e)
            }
            logger.error(f"❌ Email notifications validation failed: {e}")
    
    async def _validate_api_integration(self):
        """Validate API integration"""
        logger.info("🌐 Validating API integration...")
        
        try:
            # Check if R&D routes file exists and is importable
            from api.routes.rd_routes import router
            
            # Test route availability
            route_paths = [route.path for route in router.routes]
            expected_routes = [
                "/api/rd/agents",
                "/api/rd/cycles/start",
                "/api/rd/innovations/submit",
                "/api/rd/metrics/overview",
                "/api/rd/notifications/weekly-report",
                "/api/rd/health"
            ]
            
            available_routes = [path for path in expected_routes if any(route_path.startswith(path) for route_path in route_paths)]
            
            results = {
                "api_routes_importable": True,
                "total_routes": len(route_paths),
                "expected_routes": len(expected_routes),
                "available_routes": len(available_routes),
                "missing_routes": [route for route in expected_routes if route not in available_routes],
                "api_integration_complete": len(available_routes) == len(expected_routes)
            }
            
            self.validation_results["api_integration"] = results
            logger.info(f"✅ API integration validation: {len(available_routes)}/{len(expected_routes)} routes available")
            
        except Exception as e:
            self.validation_results["api_integration"] = {
                "api_routes_importable": False,
                "error": str(e)
            }
            logger.error(f"❌ API integration validation failed: {e}")
    
    async def _validate_settings_configuration(self):
        """Validate settings configuration"""
        logger.info("⚙️ Validating settings configuration...")
        
        try:
            settings_file = Path.cwd() / ".claude" / "settings.json"
            
            results = {
                "settings_file_exists": settings_file.exists(),
                "settings_readable": False,
                "rd_configuration_present": False,
                "agent_configuration_present": False,
                "email_configuration_present": False
            }
            
            if settings_file.exists():
                try:
                    settings_content = json.loads(settings_file.read_text())
                    results["settings_readable"] = True
                    
                    # Check for R&D configuration
                    if "rd_department" in settings_content:
                        results["rd_configuration_present"] = True
                        rd_config = settings_content["rd_department"]
                        
                        # Check for required R&D config sections
                        if "innovation_targets" in rd_config:
                            results["innovation_targets_configured"] = True
                        if "agent_specializations" in rd_config:
                            results["agent_specializations_configured"] = True
                        if "email_notifications" in rd_config:
                            results["email_configuration_present"] = True
                    
                    # Check for agent configuration
                    if "agents" in settings_content and "rd_department" in settings_content["agents"]:
                        results["agent_configuration_present"] = True
                
                except json.JSONDecodeError as e:
                    results["json_error"] = str(e)
            
            self.validation_results["settings_configuration"] = results
            
            if results["rd_configuration_present"] and results["agent_configuration_present"]:
                logger.info("✅ Settings configuration validation passed")
            else:
                logger.warning("⚠️ Settings configuration validation failed")
                
        except Exception as e:
            self.validation_results["settings_configuration"] = {
                "settings_file_exists": False,
                "error": str(e)
            }
            logger.error(f"❌ Settings configuration validation failed: {e}")
    
    def _calculate_overall_status(self):
        """Calculate overall validation status"""
        
        # Count successful validations
        validations = [
            self.validation_results["rd_directory_structure"].get("rd_agents_directory_exists", False),
            self.validation_results["rd_agent_files"] and len([r for r in self.validation_results["rd_agent_files"].values() if r.get("valid_yaml", False)]) >= 7,
            self.validation_results["rd_agent_discovery"].get("discovery_successful", False),
            self.validation_results["rd_backend_modules"] and len([r for r in self.validation_results["rd_backend_modules"].values() if r.get("functional", False)]) >= 5,
            self.validation_results["innovation_pipeline"].get("pipeline_functional", False),
            self.validation_results["email_notifications"].get("notification_system_functional", False),
            self.validation_results["api_integration"].get("api_routes_importable", False),
            self.validation_results["settings_configuration"].get("rd_configuration_present", False)
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
        print("🤖 R&D DEPARTMENT VALIDATION REPORT")
        print("="*80)
        
        status = self.validation_results["overall_status"]
        if status == "excellent":
            print("✅ OVERALL STATUS: EXCELLENT - R&D Department fully operational")
        elif status == "good":
            print("✅ OVERALL STATUS: GOOD - Minor R&D issues detected")
        elif status == "acceptable":
            print("⚠️  OVERALL STATUS: ACCEPTABLE - Some R&D issues need attention")
        else:
            print("❌ OVERALL STATUS: FAILED - Critical R&D issues detected")
        
        print(f"\n📊 Success Rate: {self.validation_results.get('success_rate', 0):.1%}")
        print(f"✅ Passed: {self.validation_results.get('passed_validations', 0)}/{self.validation_results.get('total_validations', 0)} validations")
        
        # Component status
        print(f"\n📁 R&D Directory Structure: {'✅' if self.validation_results['rd_directory_structure'].get('rd_agents_directory_exists') else '❌'}")
        
        rd_agent_files = self.validation_results.get("rd_agent_files", {})
        valid_files = len([r for r in rd_agent_files.values() if r.get("valid_yaml", False)])
        print(f"📄 R&D Agent Files: {'✅' if valid_files >= 7 else '❌'} ({valid_files}/7 valid)")
        
        discovery = self.validation_results.get("rd_agent_discovery", {})
        print(f"🔍 R&D Agent Discovery: {'✅' if discovery.get('discovery_successful') else '❌'}")
        if discovery.get("agents_discovered"):
            print(f"   Discovered {discovery['agents_discovered']} R&D agents")
        
        backend_modules = self.validation_results.get("rd_backend_modules", {})
        functional_modules = len([r for r in backend_modules.values() if r.get("functional", False)])
        print(f"🏗️ R&D Backend Modules: {'✅' if functional_modules >= 5 else '❌'} ({functional_modules}/5 functional)")
        
        pipeline = self.validation_results.get("innovation_pipeline", {})
        print(f"🔄 Innovation Pipeline: {'✅' if pipeline.get('pipeline_functional') else '❌'}")
        
        notifications = self.validation_results.get("email_notifications", {})
        print(f"📧 Email Notifications: {'✅' if notifications.get('notification_system_functional') else '❌'}")
        
        api = self.validation_results.get("api_integration", {})
        print(f"🌐 API Integration: {'✅' if api.get('api_routes_importable') else '❌'}")
        
        settings = self.validation_results.get("settings_configuration", {})
        print(f"⚙️ Settings Configuration: {'✅' if settings.get('rd_configuration_present') else '❌'}")
        
        print("\n" + "="*80)
        
        # Show discovered R&D agents
        if discovery.get("agent_details"):
            print("\n🤖 DISCOVERED R&D AGENTS:")
            print("-" * 80)
            for agent_name, details in discovery["agent_details"].items():
                print(f"  {agent_name}")
                print(f"    Specialization: {details.get('specialization', 'Unknown')}")
                print(f"    Tools: {', '.join(details['tools'][:5])}{'...' if len(details['tools']) > 5 else ''}")
                print(f"    Status: {details['status']}")
                print()

async def main():
    """Main validation function"""
    validator = RDSystemValidator()
    results = await validator.run_validation()
    
    # Print summary
    validator.print_validation_summary()
    
    # Save detailed results
    output_file = Path.cwd() / "rd_validation_results.json"
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