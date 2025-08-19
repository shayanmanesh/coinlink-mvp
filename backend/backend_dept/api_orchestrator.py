"""
API Orchestrator - Backend Agent Coordination System

Ultra-intelligent orchestration system that coordinates Athena-API,
Hephaestus-Backend, and Prometheus-Backend agents for maximum
API performance, system reliability, and infrastructure efficiency.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json

from .backend_interface import backend_agents, BackendInterface, BackendTask, TaskPriority

logger = logging.getLogger(__name__)

class OrchestrationMode(Enum):
    """Backend orchestration execution modes"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    INTELLIGENT = "intelligent"
    EMERGENCY = "emergency"

class BackendWorkflowType(Enum):
    """Types of backend workflows"""
    FULL_OPTIMIZATION = "full_optimization"
    API_DEPLOYMENT = "api_deployment"
    DATABASE_MIGRATION = "database_migration"
    INFRASTRUCTURE_SCALING = "infrastructure_scaling"
    SECURITY_AUDIT = "security_audit"
    PERFORMANCE_TUNING = "performance_tuning"
    DISASTER_RECOVERY = "disaster_recovery"
    MONITORING_SETUP = "monitoring_setup"

@dataclass
class BackendWorkflow:
    """Coordinated backend workflow definition"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_type: BackendWorkflowType = BackendWorkflowType.FULL_OPTIMIZATION
    name: str = ""
    description: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    
    # Orchestration settings
    execution_mode: OrchestrationMode = OrchestrationMode.INTELLIGENT
    max_parallel_agents: int = 3
    timeout_minutes: int = 90
    
    # Workflow steps
    workflow_steps: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    
    # Execution tracking
    status: str = "pending"  # pending, running, completed, failed, cancelled
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percentage: float = 0.0
    
    # Results and metrics
    execution_results: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    reliability_scores: Dict[str, float] = field(default_factory=dict)
    
    # Agent coordination
    agents_involved: List[str] = field(default_factory=list)
    agent_assignments: Dict[str, str] = field(default_factory=dict)
    coordination_log: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class OrchestrationMetrics:
    """Backend orchestration performance metrics"""
    total_workflows_executed: int = 0
    successful_workflows: int = 0
    failed_workflows: int = 0
    average_execution_time: float = 0.0
    average_performance_improvement: float = 0.0
    average_reliability_improvement: float = 0.0
    agent_utilization_rate: Dict[str, float] = field(default_factory=dict)
    coordination_efficiency: float = 0.0

class APIOrchestrator:
    """Advanced API and backend orchestration system"""
    
    def __init__(self, backend_interface: BackendInterface = None):
        self.orchestrator_id = "api_orchestrator"
        self.backend_interface = backend_interface or backend_agents
        
        # Workflow management
        self.active_workflows: Dict[str, BackendWorkflow] = {}
        self.workflow_queue: deque = deque()
        self.completed_workflows: List[BackendWorkflow] = []
        self.workflow_templates: Dict[BackendWorkflowType, Dict[str, Any]] = {}
        
        # Agent coordination
        self.agent_coordination_matrix: Dict[str, Dict[str, float]] = {}
        self.agent_load_balancer: Dict[str, int] = defaultdict(int)
        self.coordination_rules: List[Dict[str, Any]] = []
        
        # Orchestration metrics
        self.metrics = OrchestrationMetrics()
        self.performance_history: deque = deque(maxlen=100)
        
        # Orchestration settings
        self.max_concurrent_workflows = 5
        self.coordination_interval = 15  # seconds
        self.performance_threshold = 85.0
        self.reliability_threshold = 99.0
        
        # Initialize workflow templates
        self._initialize_workflow_templates()
        
        # Initialize agent coordination matrix
        self._initialize_coordination_matrix()
        
        logger.info("API Orchestrator initialized with intelligent backend coordination")

    def _initialize_workflow_templates(self):
        """Initialize predefined workflow templates"""
        
        # Full Backend Optimization Workflow
        self.workflow_templates[BackendWorkflowType.FULL_OPTIMIZATION] = {
            "name": "Complete Backend Optimization Sprint",
            "description": "Comprehensive backend optimization involving all backend agents",
            "execution_mode": OrchestrationMode.INTELLIGENT,
            "timeout_minutes": 120,
            "steps": [
                {
                    "id": "infrastructure_assessment",
                    "agent": "prometheus_backend",
                    "task": "infrastructure_optimization",
                    "priority": "high",
                    "dependencies": [],
                    "parameters": {
                        "assessment_type": "comprehensive",
                        "focus_areas": ["monitoring", "scaling", "security"]
                    }
                },
                {
                    "id": "database_optimization",
                    "agent": "hephaestus_backend",
                    "task": "backend_optimization",
                    "priority": "high",
                    "dependencies": ["infrastructure_assessment"],
                    "parameters": {
                        "optimization_type": "database",
                        "target_metrics": ["query_time", "connection_pool", "indexing"]
                    }
                },
                {
                    "id": "api_optimization",
                    "agent": "athena_api",
                    "task": "api_optimization",
                    "priority": "high",
                    "dependencies": ["database_optimization"],
                    "parameters": {
                        "optimization_type": "performance",
                        "target_metrics": ["response_time", "throughput", "error_rate"]
                    }
                },
                {
                    "id": "system_integration_test",
                    "agent": "prometheus_backend",
                    "task": "integration_validation",
                    "priority": "medium",
                    "dependencies": ["api_optimization"],
                    "parameters": {
                        "validation_type": "full_system",
                        "test_scenarios": ["load_test", "stress_test", "failover_test"]
                    }
                }
            ]
        }
        
        # API Deployment Workflow
        self.workflow_templates[BackendWorkflowType.API_DEPLOYMENT] = {
            "name": "API Deployment Pipeline",
            "description": "Complete API deployment with testing and monitoring",
            "execution_mode": OrchestrationMode.SEQUENTIAL,
            "timeout_minutes": 60,
            "steps": [
                {
                    "id": "api_preparation",
                    "agent": "athena_api",
                    "task": "api_deployment_prep",
                    "priority": "critical",
                    "dependencies": [],
                    "parameters": {
                        "deployment_type": "production",
                        "validation": ["schema", "authentication", "rate_limiting"]
                    }
                },
                {
                    "id": "database_migration",
                    "agent": "hephaestus_backend",
                    "task": "database_migration",
                    "priority": "critical",
                    "dependencies": ["api_preparation"],
                    "parameters": {
                        "migration_type": "schema_update",
                        "rollback_strategy": "automatic"
                    }
                },
                {
                    "id": "deployment_monitoring",
                    "agent": "prometheus_backend",
                    "task": "deployment_monitoring",
                    "priority": "high",
                    "dependencies": ["database_migration"],
                    "parameters": {
                        "monitoring_type": "deployment",
                        "alert_thresholds": {"error_rate": 0.1, "response_time": 500}
                    }
                }
            ]
        }
        
        # Performance Tuning Workflow
        self.workflow_templates[BackendWorkflowType.PERFORMANCE_TUNING] = {
            "name": "Performance Tuning Sprint",
            "description": "Focused performance optimization across all backend layers",
            "execution_mode": OrchestrationMode.PARALLEL,
            "timeout_minutes": 90,
            "steps": [
                {
                    "id": "api_performance_tuning",
                    "agent": "athena_api",
                    "task": "api_performance_optimization",
                    "priority": "high",
                    "dependencies": [],
                    "parameters": {
                        "optimization_focus": ["response_time", "throughput", "caching"]
                    }
                },
                {
                    "id": "database_performance_tuning",
                    "agent": "hephaestus_backend",
                    "task": "database_performance_optimization",
                    "priority": "high",
                    "dependencies": [],
                    "parameters": {
                        "optimization_focus": ["query_optimization", "indexing", "connection_pooling"]
                    }
                },
                {
                    "id": "infrastructure_tuning",
                    "agent": "prometheus_backend",
                    "task": "infrastructure_performance_optimization",
                    "priority": "high",
                    "dependencies": [],
                    "parameters": {
                        "optimization_focus": ["server_config", "load_balancing", "caching"]
                    }
                }
            ]
        }

    def _initialize_coordination_matrix(self):
        """Initialize agent coordination compatibility matrix"""
        # Coordination effectiveness scores (0.0 to 1.0)
        self.agent_coordination_matrix = {
            "athena_api": {
                "hephaestus_backend": 0.98,  # Very high - API->Backend coordination
                "prometheus_backend": 0.90   # High - API->Infrastructure coordination
            },
            "hephaestus_backend": {
                "athena_api": 0.95,          # High - Backend->API coordination
                "prometheus_backend": 0.92   # High - Backend->Infrastructure coordination
            },
            "prometheus_backend": {
                "athena_api": 0.85,          # Good - Infrastructure->API coordination
                "hephaestus_backend": 0.95   # High - Infrastructure->Backend coordination
            }
        }

    async def execute_workflow(self, workflow_type: BackendWorkflowType, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a coordinated backend workflow"""
        
        if workflow_type not in self.workflow_templates:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        template = self.workflow_templates[workflow_type]
        
        # Create workflow instance
        workflow = BackendWorkflow(
            workflow_type=workflow_type,
            name=template["name"],
            description=template["description"],
            execution_mode=OrchestrationMode(template["execution_mode"]),
            timeout_minutes=template["timeout_minutes"],
            workflow_steps=template["steps"]
        )
        
        # Apply custom parameters
        if parameters:
            for step in workflow.workflow_steps:
                step["parameters"].update(parameters.get(step["id"], {}))
        
        self.active_workflows[workflow.id] = workflow
        
        logger.info(f"Starting backend workflow: {workflow.name} ({workflow.id})")
        
        try:
            workflow.status = "running"
            workflow.started_at = datetime.utcnow()
            
            # Execute workflow based on mode
            if workflow.execution_mode == OrchestrationMode.SEQUENTIAL:
                result = await self._execute_sequential_workflow(workflow)
            elif workflow.execution_mode == OrchestrationMode.PARALLEL:
                result = await self._execute_parallel_workflow(workflow)
            elif workflow.execution_mode == OrchestrationMode.INTELLIGENT:
                result = await self._execute_intelligent_workflow(workflow)
            else:
                result = await self._execute_emergency_workflow(workflow)
            
            # Complete workflow
            workflow.status = "completed"
            workflow.completed_at = datetime.utcnow()
            workflow.execution_results = result
            
            # Calculate final metrics
            execution_time = (workflow.completed_at - workflow.started_at).total_seconds() / 60
            workflow.performance_metrics = await self._calculate_workflow_metrics(workflow)
            
            # Update orchestration metrics
            await self._update_orchestration_metrics(workflow, execution_time)
            
            # Move to completed
            self.completed_workflows.append(workflow)
            del self.active_workflows[workflow.id]
            
            logger.info(f"Backend workflow completed: {workflow.name} in {execution_time:.1f} minutes")
            
            return {
                "success": True,
                "workflow_id": workflow.id,
                "workflow_type": workflow_type.value,
                "execution_time_minutes": execution_time,
                "results": result,
                "performance_metrics": workflow.performance_metrics,
                "performance_improvement": workflow.performance_metrics.get("performance_improvement", 0),
                "reliability_improvement": workflow.performance_metrics.get("reliability_improvement", 0)
            }
            
        except Exception as e:
            # Handle workflow failure
            workflow.status = "failed"
            workflow.completed_at = datetime.utcnow()
            
            logger.error(f"Backend workflow failed: {workflow.name} - {str(e)}")
            
            return {
                "success": False,
                "workflow_id": workflow.id,
                "error": str(e)
            }

    async def _execute_sequential_workflow(self, workflow: BackendWorkflow) -> Dict[str, Any]:
        """Execute workflow steps sequentially"""
        results = {}
        
        for step in workflow.workflow_steps:
            # Check dependencies
            if not await self._check_dependencies(step, results):
                raise Exception(f"Dependencies not met for step: {step['id']}")
            
            # Execute step
            step_result = await self._execute_workflow_step(workflow, step)
            results[step["id"]] = step_result
            
            # Update progress
            workflow.progress_percentage = (len(results) / len(workflow.workflow_steps)) * 100
            
            # Log coordination
            workflow.coordination_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "step": step["id"],
                "agent": step["agent"],
                "status": "completed",
                "result_summary": step_result.get("summary", "")
            })
        
        return results

    async def _execute_parallel_workflow(self, workflow: BackendWorkflow) -> Dict[str, Any]:
        """Execute workflow steps in parallel where possible"""
        results = {}
        pending_steps = workflow.workflow_steps.copy()
        
        while pending_steps:
            # Find steps that can execute (dependencies met)
            executable_steps = []
            for step in pending_steps:
                if await self._check_dependencies(step, results):
                    executable_steps.append(step)
            
            if not executable_steps:
                raise Exception("Workflow deadlock - no executable steps found")
            
            # Execute steps in parallel
            step_tasks = [
                self._execute_workflow_step(workflow, step)
                for step in executable_steps
            ]
            
            step_results = await asyncio.gather(*step_tasks, return_exceptions=True)
            
            # Process results
            for i, step in enumerate(executable_steps):
                if isinstance(step_results[i], Exception):
                    raise step_results[i]
                
                results[step["id"]] = step_results[i]
                pending_steps.remove(step)
                
                # Log coordination
                workflow.coordination_log.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "step": step["id"],
                    "agent": step["agent"],
                    "status": "completed",
                    "execution_mode": "parallel"
                })
            
            # Update progress
            workflow.progress_percentage = (len(results) / len(workflow.workflow_steps)) * 100
        
        return results

    async def _execute_intelligent_workflow(self, workflow: BackendWorkflow) -> Dict[str, Any]:
        """Execute workflow with intelligent agent coordination"""
        results = {}
        
        # Optimize execution order based on agent coordination matrix
        optimized_order = await self._optimize_execution_order(workflow.workflow_steps)
        
        # Group steps by coordination compatibility
        execution_groups = await self._create_execution_groups(optimized_order)
        
        for group in execution_groups:
            if len(group) == 1:
                # Execute single step
                step = group[0]
                if await self._check_dependencies(step, results):
                    step_result = await self._execute_workflow_step(workflow, step)
                    results[step["id"]] = step_result
            else:
                # Execute group in parallel with coordination
                group_tasks = []
                for step in group:
                    if await self._check_dependencies(step, results):
                        group_tasks.append(self._execute_coordinated_step(workflow, step))
                
                if group_tasks:
                    group_results = await asyncio.gather(*group_tasks, return_exceptions=True)
                    
                    for i, step in enumerate(group):
                        if not isinstance(group_results[i], Exception):
                            results[step["id"]] = group_results[i]
            
            # Update progress
            workflow.progress_percentage = (len(results) / len(workflow.workflow_steps)) * 100
        
        return results

    async def _execute_emergency_workflow(self, workflow: BackendWorkflow) -> Dict[str, Any]:
        """Execute workflow in emergency mode - fastest possible execution"""
        results = {}
        
        # Execute all possible steps immediately in parallel
        all_tasks = [
            self._execute_workflow_step(workflow, step)
            for step in workflow.workflow_steps
        ]
        
        all_results = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        for i, step in enumerate(workflow.workflow_steps):
            if not isinstance(all_results[i], Exception):
                results[step["id"]] = all_results[i]
            else:
                logger.error(f"Emergency step {step['id']} failed: {all_results[i]}")
        
        return results

    async def _execute_workflow_step(self, workflow: BackendWorkflow, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        agent_id = step["agent"]
        task_type = step["task"]
        parameters = step.get("parameters", {})
        
        # Add workflow context to parameters
        parameters["workflow_id"] = workflow.id
        parameters["workflow_type"] = workflow.workflow_type.value
        parameters["step_id"] = step["id"]
        
        try:
            # Execute task with the backend interface
            result = await self.backend_interface.execute_agent_task(
                agent_id=agent_id,
                task_type=task_type,
                parameters=parameters
            )
            
            return {
                "step_id": step["id"],
                "agent_id": agent_id,
                "task_type": task_type,
                "success": result.get("success", False),
                "result": result.get("result", {}),
                "execution_time": datetime.utcnow().isoformat(),
                "summary": f"Step {step['id']} completed by {agent_id}"
            }
            
        except Exception as e:
            logger.error(f"Workflow step {step['id']} failed: {str(e)}")
            raise

    async def _execute_coordinated_step(self, workflow: BackendWorkflow, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute step with enhanced coordination"""
        # Add coordination metadata
        coordination_data = await self._get_coordination_metadata(step, workflow)
        step["parameters"]["coordination"] = coordination_data
        
        return await self._execute_workflow_step(workflow, step)

    async def _check_dependencies(self, step: Dict[str, Any], completed_results: Dict[str, Any]) -> bool:
        """Check if step dependencies are satisfied"""
        dependencies = step.get("dependencies", [])
        return all(dep in completed_results for dep in dependencies)

    async def _optimize_execution_order(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Optimize step execution order based on coordination matrix"""
        def coordination_score(step):
            agent = step["agent"]
            score = 0
            for other_step in steps:
                if other_step["agent"] != agent:
                    other_agent = other_step["agent"]
                    score += self.agent_coordination_matrix.get(agent, {}).get(other_agent, 0.5)
            return score
        
        return sorted(steps, key=coordination_score, reverse=True)

    async def _create_execution_groups(self, steps: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Create execution groups based on compatibility"""
        groups = []
        remaining_steps = steps.copy()
        
        while remaining_steps:
            current_group = [remaining_steps.pop(0)]
            
            # Find compatible steps to add to group
            i = 0
            while i < len(remaining_steps):
                step = remaining_steps[i]
                if await self._can_execute_together(current_group[0], step):
                    current_group.append(remaining_steps.pop(i))
                else:
                    i += 1
            
            groups.append(current_group)
        
        return groups

    async def _can_execute_together(self, step1: Dict[str, Any], step2: Dict[str, Any]) -> bool:
        """Check if two steps can execute together"""
        agent1, agent2 = step1["agent"], step2["agent"]
        
        if agent1 == agent2:
            return False  # Same agent can't execute multiple tasks simultaneously
        
        # Check coordination compatibility
        compatibility = self.agent_coordination_matrix.get(agent1, {}).get(agent2, 0.5)
        return compatibility > 0.8  # High compatibility threshold for backend systems

    async def _get_coordination_metadata(self, step: Dict[str, Any], workflow: BackendWorkflow) -> Dict[str, Any]:
        """Get coordination metadata for enhanced step execution"""
        return {
            "workflow_context": {
                "id": workflow.id,
                "type": workflow.workflow_type.value,
                "progress": workflow.progress_percentage
            },
            "agent_coordination": {
                "compatibility_scores": self.agent_coordination_matrix.get(step["agent"], {}),
                "load_balance_factor": self.agent_load_balancer[step["agent"]]
            },
            "optimization_hints": {
                "priority_boost": step.get("priority") == "critical",
                "parallel_safe": step.get("parallel_safe", True)
            }
        }

    async def _calculate_workflow_metrics(self, workflow: BackendWorkflow) -> Dict[str, float]:
        """Calculate comprehensive workflow metrics"""
        return {
            "execution_time_minutes": (workflow.completed_at - workflow.started_at).total_seconds() / 60,
            "success_rate": 100.0,  # Simplified
            "performance_improvement": 28.5,  # Simulated
            "reliability_improvement": 15.8,  # Simulated
            "agent_efficiency": 94.0,         # Simulated
            "coordination_effectiveness": 91.2  # Simulated
        }

    async def _update_orchestration_metrics(self, workflow: BackendWorkflow, execution_time: float):
        """Update orchestration performance metrics"""
        self.metrics.total_workflows_executed += 1
        
        if workflow.status == "completed":
            self.metrics.successful_workflows += 1
        else:
            self.metrics.failed_workflows += 1
        
        # Update average execution time
        total_time = self.metrics.average_execution_time * (self.metrics.total_workflows_executed - 1) + execution_time
        self.metrics.average_execution_time = total_time / self.metrics.total_workflows_executed

    # Public Interface Methods

    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator status"""
        return {
            "orchestrator_id": self.orchestrator_id,
            "status": "operational",
            "active_workflows": len(self.active_workflows),
            "queued_workflows": len(self.workflow_queue),
            "completed_workflows": len(self.completed_workflows),
            "available_workflow_types": [wt.value for wt in BackendWorkflowType],
            "coordination_modes": [om.value for om in OrchestrationMode],
            "performance_metrics": {
                "total_executed": self.metrics.total_workflows_executed,
                "success_rate": (self.metrics.successful_workflows / max(1, self.metrics.total_workflows_executed)) * 100,
                "average_execution_time": self.metrics.average_execution_time,
                "coordination_efficiency": self.metrics.coordination_efficiency
            },
            "agent_coordination": {
                "coordination_matrix": self.agent_coordination_matrix,
                "load_distribution": dict(self.agent_load_balancer)
            }
        }

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
        else:
            # Check completed workflows
            workflow = next((w for w in self.completed_workflows if w.id == workflow_id), None)
        
        if not workflow:
            return None
        
        return {
            "workflow_id": workflow.id,
            "workflow_type": workflow.workflow_type.value,
            "name": workflow.name,
            "status": workflow.status,
            "progress_percentage": workflow.progress_percentage,
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "agents_involved": workflow.agents_involved,
            "execution_results": workflow.execution_results,
            "performance_metrics": workflow.performance_metrics,
            "coordination_log": workflow.coordination_log[-10:]  # Last 10 entries
        }

    async def schedule_workflow(self, workflow_type: BackendWorkflowType, priority: TaskPriority = TaskPriority.MEDIUM,
                              parameters: Dict[str, Any] = None) -> str:
        """Schedule a workflow for execution"""
        template = self.workflow_templates[workflow_type]
        
        workflow = BackendWorkflow(
            workflow_type=workflow_type,
            name=template["name"],
            description=template["description"],
            priority=priority,
            execution_mode=OrchestrationMode(template["execution_mode"]),
            timeout_minutes=template["timeout_minutes"],
            workflow_steps=template["steps"]
        )
        
        # Apply custom parameters
        if parameters:
            for step in workflow.workflow_steps:
                step["parameters"].update(parameters.get(step["id"], {}))
        
        self.workflow_queue.append(workflow)
        
        logger.info(f"Scheduled backend workflow: {workflow.name} ({workflow.id})")
        
        return workflow.id

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel an active workflow"""
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
            workflow.status = "cancelled"
            workflow.completed_at = datetime.utcnow()
            
            # Move to completed
            self.completed_workflows.append(workflow)
            del self.active_workflows[workflow_id]
            
            logger.info(f"Cancelled backend workflow: {workflow.name}")
            return True
        
        return False

    async def start_orchestration_loop(self):
        """Start the orchestration background loop"""
        logger.info("Starting backend orchestration loop")
        
        while True:
            try:
                # Process workflow queue
                while self.workflow_queue and len(self.active_workflows) < self.max_concurrent_workflows:
                    workflow = self.workflow_queue.popleft()
                    
                    # Execute workflow in background
                    asyncio.create_task(self.execute_workflow(workflow.workflow_type))
                
                # Wait for next coordination cycle
                await asyncio.sleep(self.coordination_interval)
                
            except Exception as e:
                logger.error(f"Error in orchestration loop: {e}")
                await asyncio.sleep(self.coordination_interval * 2)

# Global API orchestrator instance
api_orchestrator = APIOrchestrator()