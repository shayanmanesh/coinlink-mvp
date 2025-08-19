"""
Infrastructure Optimizer - Auto-scaling and Resource Management System

Ultra-intelligent infrastructure optimization system that manages auto-scaling,
resource allocation, cost optimization, and infrastructure automation for
maximum efficiency and reliability at scale.
"""

import asyncio
import logging
import uuid
import json
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import psutil

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """Types of infrastructure resources"""
    COMPUTE = "compute"
    MEMORY = "memory"
    STORAGE = "storage"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"

class ScalingAction(Enum):
    """Auto-scaling actions"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    SCALE_OUT = "scale_out"
    SCALE_IN = "scale_in"
    NO_ACTION = "no_action"

class OptimizationStrategy(Enum):
    """Infrastructure optimization strategies"""
    COST_OPTIMIZED = "cost_optimized"
    PERFORMANCE_OPTIMIZED = "performance_optimized"
    BALANCED = "balanced"
    HIGH_AVAILABILITY = "high_availability"
    ENERGY_EFFICIENT = "energy_efficient"

@dataclass
class ResourceMetrics:
    """Resource utilization metrics"""
    resource_type: ResourceType
    current_usage: float
    peak_usage: float
    average_usage: float
    capacity: float
    cost_per_hour: float = 0.0
    efficiency_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def utilization_percentage(self) -> float:
        """Calculate resource utilization percentage"""
        if self.capacity == 0:
            return 0.0
        return (self.current_usage / self.capacity) * 100
    
    @property
    def is_underutilized(self) -> bool:
        """Check if resource is underutilized"""
        return self.utilization_percentage < 30.0
    
    @property
    def is_overutilized(self) -> bool:
        """Check if resource is overutilized"""
        return self.utilization_percentage > 80.0

@dataclass
class ScalingPolicy:
    """Auto-scaling policy configuration"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    resource_type: ResourceType = ResourceType.COMPUTE
    
    # Scaling thresholds
    scale_up_threshold: float = 80.0
    scale_down_threshold: float = 30.0
    scale_out_threshold: float = 75.0
    scale_in_threshold: float = 25.0
    
    # Scaling parameters
    min_instances: int = 1
    max_instances: int = 10
    scale_increment: int = 1
    cooldown_period_seconds: int = 300
    
    # Performance requirements
    target_utilization: float = 60.0
    target_response_time_ms: float = 200.0
    
    # Cost constraints
    max_hourly_cost: float = 100.0
    cost_optimization_enabled: bool = True
    
    # Tracking
    last_scaling_action: Optional[datetime] = None
    scaling_history: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class InfrastructureNode:
    """Infrastructure node representation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_type: str = "compute"
    region: str = "us-west-2"
    availability_zone: str = "us-west-2a"
    
    # Resource specifications
    cpu_cores: int = 4
    memory_gb: int = 16
    storage_gb: int = 100
    network_bandwidth_gbps: float = 10.0
    
    # Status
    status: str = "running"  # running, stopping, stopped, starting, terminating
    health_status: str = "healthy"  # healthy, unhealthy, degraded
    
    # Metrics
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_usage: float = 0.0
    
    # Cost
    hourly_cost: float = 0.0
    total_cost: float = 0.0
    
    # Lifecycle
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_health_check: Optional[datetime] = None
    uptime_hours: float = 0.0

@dataclass
class OptimizationResult:
    """Infrastructure optimization result"""
    optimization_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    strategy: OptimizationStrategy = OptimizationStrategy.BALANCED
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Resource changes
    nodes_added: int = 0
    nodes_removed: int = 0
    nodes_resized: int = 0
    
    # Performance impact
    performance_improvement: float = 0.0
    response_time_improvement: float = 0.0
    throughput_improvement: float = 0.0
    
    # Cost impact
    cost_savings: float = 0.0
    cost_increase: float = 0.0
    roi_percentage: float = 0.0
    
    # Efficiency metrics
    resource_efficiency_improvement: float = 0.0
    energy_savings_percentage: float = 0.0
    
    # Actions taken
    actions: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

class InfrastructureOptimizer:
    """Comprehensive infrastructure optimization and auto-scaling system"""
    
    def __init__(self):
        self.optimizer_id = "infrastructure_optimizer"
        
        # Infrastructure inventory
        self.nodes: Dict[str, InfrastructureNode] = {}
        self.node_groups: Dict[str, List[str]] = defaultdict(list)  # group_name -> node_ids
        
        # Resource metrics
        self.resource_metrics: Dict[ResourceType, ResourceMetrics] = {}
        self.metrics_history: deque = deque(maxlen=1000)
        
        # Scaling policies
        self.scaling_policies: Dict[str, ScalingPolicy] = {}
        self.active_scaling_operations: Set[str] = set()
        
        # Optimization tracking
        self.optimization_history: deque = deque(maxlen=100)
        self.current_strategy = OptimizationStrategy.BALANCED
        
        # Cost management
        self.cost_tracking: Dict[str, float] = defaultdict(float)
        self.budget_alerts: List[Dict[str, Any]] = []
        self.monthly_budget = 10000.0  # USD
        
        # Configuration
        self.optimization_interval_minutes = 15
        self.health_check_interval_seconds = 60
        self.cost_optimization_threshold = 0.7  # 70% of budget
        
        # Performance baselines
        self.performance_baselines = {
            "cpu_baseline": 40.0,
            "memory_baseline": 50.0,
            "response_time_baseline": 200.0,
            "throughput_baseline": 1000.0
        }
        
        # Initialize default policies
        self._initialize_default_policies()
        
        logger.info("Infrastructure Optimizer initialized with intelligent auto-scaling")

    def _initialize_default_policies(self):
        """Initialize default scaling policies"""
        
        # Compute scaling policy
        self.scaling_policies["compute_scaling"] = ScalingPolicy(
            name="Compute Auto-Scaling",
            resource_type=ResourceType.COMPUTE,
            scale_up_threshold=75.0,
            scale_down_threshold=25.0,
            min_instances=2,
            max_instances=20,
            scale_increment=2,
            target_utilization=60.0
        )
        
        # Memory scaling policy
        self.scaling_policies["memory_scaling"] = ScalingPolicy(
            name="Memory Auto-Scaling",
            resource_type=ResourceType.MEMORY,
            scale_up_threshold=80.0,
            scale_down_threshold=30.0,
            min_instances=1,
            max_instances=10,
            target_utilization=65.0
        )
        
        # Database scaling policy
        self.scaling_policies["database_scaling"] = ScalingPolicy(
            name="Database Auto-Scaling",
            resource_type=ResourceType.DATABASE,
            scale_up_threshold=70.0,
            scale_down_threshold=20.0,
            min_instances=1,
            max_instances=5,
            cooldown_period_seconds=600
        )

    async def optimize_infrastructure(self, strategy: OptimizationStrategy = None) -> OptimizationResult:
        """Execute comprehensive infrastructure optimization"""
        
        if strategy:
            self.current_strategy = strategy
        
        logger.info(f"Starting infrastructure optimization with {self.current_strategy.value} strategy")
        
        result = OptimizationResult(strategy=self.current_strategy)
        
        try:
            # Collect current metrics
            await self._collect_infrastructure_metrics()
            
            # Analyze resource utilization
            utilization_analysis = await self._analyze_resource_utilization()
            
            # Determine optimization actions
            optimization_actions = await self._determine_optimization_actions(
                utilization_analysis, self.current_strategy
            )
            
            # Execute optimization actions
            for action in optimization_actions:
                action_result = await self._execute_optimization_action(action)
                result.actions.append(action_result)
                
                # Track changes
                if action_result["type"] == "add_node":
                    result.nodes_added += 1
                elif action_result["type"] == "remove_node":
                    result.nodes_removed += 1
                elif action_result["type"] == "resize_node":
                    result.nodes_resized += 1
            
            # Calculate impact
            result = await self._calculate_optimization_impact(result)
            
            # Generate recommendations
            result.recommendations = await self._generate_optimization_recommendations()
            
            # Update history
            self.optimization_history.append(result)
            
            logger.info(f"Infrastructure optimization completed: {result.nodes_added} added, "
                       f"{result.nodes_removed} removed, {result.cost_savings:.2f} saved")
            
            return result
            
        except Exception as e:
            logger.error(f"Infrastructure optimization failed: {e}")
            result.actions.append({"type": "error", "message": str(e)})
            return result

    async def execute_auto_scaling(self, resource_type: ResourceType = None) -> Dict[str, Any]:
        """Execute auto-scaling based on current metrics"""
        
        scaling_results = []
        
        # Determine which resources to scale
        resources_to_scale = [resource_type] if resource_type else list(ResourceType)
        
        for resource in resources_to_scale:
            if resource not in self.resource_metrics:
                continue
            
            metrics = self.resource_metrics[resource]
            policy_key = f"{resource.value}_scaling"
            
            if policy_key not in self.scaling_policies:
                continue
            
            policy = self.scaling_policies[policy_key]
            
            # Check if in cooldown period
            if policy.last_scaling_action:
                cooldown_elapsed = (datetime.utcnow() - policy.last_scaling_action).total_seconds()
                if cooldown_elapsed < policy.cooldown_period_seconds:
                    logger.debug(f"Scaling policy {policy.name} in cooldown period")
                    continue
            
            # Determine scaling action
            scaling_action = await self._determine_scaling_action(metrics, policy)
            
            if scaling_action != ScalingAction.NO_ACTION:
                # Execute scaling
                scaling_result = await self._execute_scaling_action(scaling_action, policy, metrics)
                scaling_results.append(scaling_result)
                
                # Update policy
                policy.last_scaling_action = datetime.utcnow()
                policy.scaling_history.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "action": scaling_action.value,
                    "metrics": {
                        "utilization": metrics.utilization_percentage,
                        "current_usage": metrics.current_usage,
                        "capacity": metrics.capacity
                    }
                })
        
        return {
            "success": True,
            "scaling_actions": len(scaling_results),
            "results": scaling_results,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _collect_infrastructure_metrics(self):
        """Collect current infrastructure metrics"""
        
        try:
            # Get real system metrics using psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Update resource metrics
            self.resource_metrics[ResourceType.COMPUTE] = ResourceMetrics(
                resource_type=ResourceType.COMPUTE,
                current_usage=cpu_percent,
                peak_usage=max(cpu_percent, self.resource_metrics.get(
                    ResourceType.COMPUTE, ResourceMetrics(ResourceType.COMPUTE, 0, 0, 0, 100)).peak_usage),
                average_usage=cpu_percent,
                capacity=100.0,
                cost_per_hour=0.10 * (cpu_percent / 100),
                efficiency_score=min(100, (cpu_percent / 60) * 100) if cpu_percent > 0 else 0
            )
            
            self.resource_metrics[ResourceType.MEMORY] = ResourceMetrics(
                resource_type=ResourceType.MEMORY,
                current_usage=memory.percent,
                peak_usage=max(memory.percent, self.resource_metrics.get(
                    ResourceType.MEMORY, ResourceMetrics(ResourceType.MEMORY, 0, 0, 0, 100)).peak_usage),
                average_usage=memory.percent,
                capacity=100.0,
                cost_per_hour=0.08 * (memory.percent / 100),
                efficiency_score=min(100, (memory.percent / 65) * 100) if memory.percent > 0 else 0
            )
            
            self.resource_metrics[ResourceType.STORAGE] = ResourceMetrics(
                resource_type=ResourceType.STORAGE,
                current_usage=disk.percent,
                peak_usage=max(disk.percent, self.resource_metrics.get(
                    ResourceType.STORAGE, ResourceMetrics(ResourceType.STORAGE, 0, 0, 0, 100)).peak_usage),
                average_usage=disk.percent,
                capacity=100.0,
                cost_per_hour=0.05 * (disk.percent / 100),
                efficiency_score=min(100, (disk.percent / 70) * 100) if disk.percent > 0 else 0
            )
            
        except Exception as e:
            logger.warning(f"Could not collect real metrics: {e}")
            # Fallback to simulated metrics
            self.resource_metrics[ResourceType.COMPUTE] = ResourceMetrics(
                resource_type=ResourceType.COMPUTE,
                current_usage=65.0,
                peak_usage=85.0,
                average_usage=60.0,
                capacity=100.0,
                cost_per_hour=0.065,
                efficiency_score=92.0
            )

    async def _analyze_resource_utilization(self) -> Dict[str, Any]:
        """Analyze resource utilization patterns"""
        
        analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "resources": {},
            "recommendations": [],
            "optimization_potential": 0.0
        }
        
        total_efficiency = 0.0
        resource_count = 0
        
        for resource_type, metrics in self.resource_metrics.items():
            resource_analysis = {
                "type": resource_type.value,
                "utilization": metrics.utilization_percentage,
                "status": "optimal",
                "action_required": None
            }
            
            if metrics.is_overutilized:
                resource_analysis["status"] = "overutilized"
                resource_analysis["action_required"] = "scale_up"
                analysis["recommendations"].append(
                    f"Scale up {resource_type.value} - utilization at {metrics.utilization_percentage:.1f}%"
                )
            elif metrics.is_underutilized:
                resource_analysis["status"] = "underutilized"
                resource_analysis["action_required"] = "scale_down"
                analysis["recommendations"].append(
                    f"Scale down {resource_type.value} - utilization at {metrics.utilization_percentage:.1f}%"
                )
            
            analysis["resources"][resource_type.value] = resource_analysis
            total_efficiency += metrics.efficiency_score
            resource_count += 1
        
        # Calculate overall optimization potential
        if resource_count > 0:
            average_efficiency = total_efficiency / resource_count
            analysis["optimization_potential"] = max(0, 100 - average_efficiency)
        
        return analysis

    async def _determine_optimization_actions(self, analysis: Dict[str, Any], 
                                            strategy: OptimizationStrategy) -> List[Dict[str, Any]]:
        """Determine optimization actions based on analysis and strategy"""
        
        actions = []
        
        for resource_name, resource_analysis in analysis["resources"].items():
            if resource_analysis["action_required"]:
                action = {
                    "type": "",
                    "resource": resource_name,
                    "reason": resource_analysis["status"],
                    "priority": "medium"
                }
                
                if strategy == OptimizationStrategy.COST_OPTIMIZED:
                    # Prioritize cost savings
                    if resource_analysis["action_required"] == "scale_down":
                        action["type"] = "remove_node"
                        action["priority"] = "high"
                    elif resource_analysis["utilization"] > 90:
                        action["type"] = "add_node"
                        action["priority"] = "low"
                        
                elif strategy == OptimizationStrategy.PERFORMANCE_OPTIMIZED:
                    # Prioritize performance
                    if resource_analysis["action_required"] == "scale_up":
                        action["type"] = "add_node"
                        action["priority"] = "high"
                    elif resource_analysis["utilization"] < 20:
                        action["type"] = "remove_node"
                        action["priority"] = "low"
                        
                elif strategy == OptimizationStrategy.HIGH_AVAILABILITY:
                    # Maintain redundancy
                    if resource_analysis["action_required"] == "scale_up":
                        action["type"] = "add_node"
                        action["priority"] = "high"
                        action["count"] = 2  # Add redundancy
                    # Never scale down for HA
                    
                else:  # BALANCED or ENERGY_EFFICIENT
                    if resource_analysis["action_required"] == "scale_up" and resource_analysis["utilization"] > 80:
                        action["type"] = "add_node"
                        action["priority"] = "medium"
                    elif resource_analysis["action_required"] == "scale_down" and resource_analysis["utilization"] < 30:
                        action["type"] = "remove_node"
                        action["priority"] = "medium"
                
                if action["type"]:
                    actions.append(action)
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        actions.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return actions

    async def _execute_optimization_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single optimization action"""
        
        result = {
            "type": action["type"],
            "resource": action["resource"],
            "success": False,
            "details": {}
        }
        
        try:
            if action["type"] == "add_node":
                # Simulate adding a node
                node = InfrastructureNode(
                    node_type=action["resource"],
                    cpu_cores=4,
                    memory_gb=16,
                    hourly_cost=0.10
                )
                self.nodes[node.id] = node
                self.node_groups[action["resource"]].append(node.id)
                
                result["success"] = True
                result["details"] = {
                    "node_id": node.id,
                    "specifications": f"{node.cpu_cores} cores, {node.memory_gb}GB RAM",
                    "cost": node.hourly_cost
                }
                
            elif action["type"] == "remove_node":
                # Simulate removing a node
                resource_nodes = self.node_groups.get(action["resource"], [])
                if resource_nodes:
                    node_id = resource_nodes[-1]  # Remove last node
                    if node_id in self.nodes:
                        removed_node = self.nodes.pop(node_id)
                        resource_nodes.remove(node_id)
                        
                        result["success"] = True
                        result["details"] = {
                            "node_id": node_id,
                            "cost_saved": removed_node.hourly_cost,
                            "uptime_hours": removed_node.uptime_hours
                        }
                        
            elif action["type"] == "resize_node":
                # Simulate resizing a node
                resource_nodes = self.node_groups.get(action["resource"], [])
                if resource_nodes:
                    node_id = resource_nodes[0]
                    if node_id in self.nodes:
                        node = self.nodes[node_id]
                        # Resize logic
                        old_cores = node.cpu_cores
                        node.cpu_cores = int(node.cpu_cores * 1.5)
                        node.memory_gb = int(node.memory_gb * 1.5)
                        node.hourly_cost *= 1.4
                        
                        result["success"] = True
                        result["details"] = {
                            "node_id": node_id,
                            "old_specs": f"{old_cores} cores",
                            "new_specs": f"{node.cpu_cores} cores",
                            "cost_change": node.hourly_cost / 1.4 * 0.4
                        }
            
            logger.info(f"Executed optimization action: {action['type']} for {action['resource']}")
            
        except Exception as e:
            logger.error(f"Failed to execute optimization action: {e}")
            result["error"] = str(e)
        
        return result

    async def _determine_scaling_action(self, metrics: ResourceMetrics, 
                                       policy: ScalingPolicy) -> ScalingAction:
        """Determine appropriate scaling action based on metrics and policy"""
        
        utilization = metrics.utilization_percentage
        
        # Check for scale up/out conditions
        if utilization >= policy.scale_up_threshold:
            # Determine if we should scale up (vertical) or out (horizontal)
            current_instances = len(self.node_groups.get(metrics.resource_type.value, []))
            
            if current_instances < policy.max_instances:
                if utilization >= policy.scale_out_threshold:
                    return ScalingAction.SCALE_OUT
                else:
                    return ScalingAction.SCALE_UP
            elif metrics.capacity < 100:  # Can still scale up vertically
                return ScalingAction.SCALE_UP
        
        # Check for scale down/in conditions
        elif utilization <= policy.scale_down_threshold:
            current_instances = len(self.node_groups.get(metrics.resource_type.value, []))
            
            if current_instances > policy.min_instances:
                if utilization <= policy.scale_in_threshold:
                    return ScalingAction.SCALE_IN
                else:
                    return ScalingAction.SCALE_DOWN
            elif metrics.capacity > 50:  # Can still scale down vertically
                return ScalingAction.SCALE_DOWN
        
        return ScalingAction.NO_ACTION

    async def _execute_scaling_action(self, action: ScalingAction, policy: ScalingPolicy,
                                     metrics: ResourceMetrics) -> Dict[str, Any]:
        """Execute a scaling action"""
        
        result = {
            "action": action.value,
            "resource": metrics.resource_type.value,
            "policy": policy.name,
            "success": False,
            "details": {}
        }
        
        try:
            if action == ScalingAction.SCALE_OUT:
                # Add new instances
                for _ in range(policy.scale_increment):
                    node = InfrastructureNode(
                        node_type=metrics.resource_type.value,
                        cpu_cores=4,
                        memory_gb=16,
                        hourly_cost=0.10
                    )
                    self.nodes[node.id] = node
                    self.node_groups[metrics.resource_type.value].append(node.id)
                
                result["success"] = True
                result["details"] = {
                    "instances_added": policy.scale_increment,
                    "total_instances": len(self.node_groups[metrics.resource_type.value])
                }
                
            elif action == ScalingAction.SCALE_IN:
                # Remove instances
                resource_nodes = self.node_groups[metrics.resource_type.value]
                instances_to_remove = min(policy.scale_increment, 
                                        len(resource_nodes) - policy.min_instances)
                
                for _ in range(instances_to_remove):
                    if resource_nodes:
                        node_id = resource_nodes.pop()
                        if node_id in self.nodes:
                            del self.nodes[node_id]
                
                result["success"] = True
                result["details"] = {
                    "instances_removed": instances_to_remove,
                    "total_instances": len(resource_nodes)
                }
                
            elif action == ScalingAction.SCALE_UP:
                # Increase capacity of existing instances
                resource_nodes = self.node_groups.get(metrics.resource_type.value, [])
                upgraded_count = 0
                
                for node_id in resource_nodes[:policy.scale_increment]:
                    if node_id in self.nodes:
                        node = self.nodes[node_id]
                        node.cpu_cores = min(node.cpu_cores * 2, 64)
                        node.memory_gb = min(node.memory_gb * 2, 256)
                        node.hourly_cost *= 1.8
                        upgraded_count += 1
                
                result["success"] = True
                result["details"] = {
                    "instances_upgraded": upgraded_count,
                    "capacity_increase": "2x"
                }
                
            elif action == ScalingAction.SCALE_DOWN:
                # Decrease capacity of existing instances
                resource_nodes = self.node_groups.get(metrics.resource_type.value, [])
                downgraded_count = 0
                
                for node_id in resource_nodes[:policy.scale_increment]:
                    if node_id in self.nodes:
                        node = self.nodes[node_id]
                        if node.cpu_cores > 2:
                            node.cpu_cores = max(node.cpu_cores // 2, 2)
                            node.memory_gb = max(node.memory_gb // 2, 4)
                            node.hourly_cost *= 0.6
                            downgraded_count += 1
                
                result["success"] = True
                result["details"] = {
                    "instances_downgraded": downgraded_count,
                    "capacity_decrease": "50%"
                }
            
            logger.info(f"Executed scaling action: {action.value} for {metrics.resource_type.value}")
            
        except Exception as e:
            logger.error(f"Failed to execute scaling action: {e}")
            result["error"] = str(e)
        
        return result

    async def _calculate_optimization_impact(self, result: OptimizationResult) -> OptimizationResult:
        """Calculate the impact of optimization actions"""
        
        # Calculate cost impact
        total_cost_change = 0.0
        for action in result.actions:
            if action.get("success"):
                details = action.get("details", {})
                if "cost_saved" in details:
                    total_cost_change -= details["cost_saved"]
                elif "cost" in details:
                    total_cost_change += details["cost"]
                elif "cost_change" in details:
                    total_cost_change += details["cost_change"]
        
        if total_cost_change < 0:
            result.cost_savings = abs(total_cost_change)
        else:
            result.cost_increase = total_cost_change
        
        # Calculate performance impact (simulated)
        if result.nodes_added > 0:
            result.performance_improvement = result.nodes_added * 15.0
            result.response_time_improvement = result.nodes_added * 10.0
            result.throughput_improvement = result.nodes_added * 20.0
        
        if result.nodes_resized > 0:
            result.performance_improvement += result.nodes_resized * 10.0
            result.response_time_improvement += result.nodes_resized * 5.0
        
        # Calculate efficiency improvement
        result.resource_efficiency_improvement = (result.nodes_removed * 5.0) + (result.nodes_resized * 3.0)
        result.energy_savings_percentage = result.nodes_removed * 8.0
        
        # Calculate ROI
        if result.cost_increase > 0:
            result.roi_percentage = (result.performance_improvement / result.cost_increase) * 100
        elif result.cost_savings > 0:
            result.roi_percentage = 100.0 + (result.cost_savings * 10)
        
        return result

    async def _generate_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on current state"""
        
        recommendations = []
        
        # Analyze current metrics
        for resource_type, metrics in self.resource_metrics.items():
            if metrics.is_overutilized:
                recommendations.append(
                    f"Consider upgrading {resource_type.value} infrastructure - "
                    f"currently at {metrics.utilization_percentage:.1f}% utilization"
                )
            elif metrics.is_underutilized:
                recommendations.append(
                    f"Opportunity to reduce {resource_type.value} costs - "
                    f"only {metrics.utilization_percentage:.1f}% utilized"
                )
            
            if metrics.efficiency_score < 70:
                recommendations.append(
                    f"Improve {resource_type.value} efficiency - "
                    f"current score: {metrics.efficiency_score:.1f}/100"
                )
        
        # Cost recommendations
        total_hourly_cost = sum(node.hourly_cost for node in self.nodes.values())
        if total_hourly_cost > self.monthly_budget / (30 * 24):
            recommendations.append(
                f"Warning: Current hourly cost (${total_hourly_cost:.2f}) "
                f"exceeds budget allocation"
            )
        
        # Performance recommendations
        if self.current_strategy != OptimizationStrategy.PERFORMANCE_OPTIMIZED:
            high_utilization_resources = [
                r for r, m in self.resource_metrics.items() 
                if m.utilization_percentage > 75
            ]
            if high_utilization_resources:
                recommendations.append(
                    "Consider switching to performance-optimized strategy "
                    "due to high resource utilization"
                )
        
        # High availability recommendations
        for group_name, node_ids in self.node_groups.items():
            if len(node_ids) < 2:
                recommendations.append(
                    f"Add redundancy to {group_name} - currently single point of failure"
                )
        
        return recommendations[:5]  # Return top 5 recommendations

    async def predict_scaling_needs(self, hours_ahead: int = 24) -> Dict[str, Any]:
        """Predict future scaling needs based on trends"""
        
        predictions = {
            "timestamp": datetime.utcnow().isoformat(),
            "prediction_window_hours": hours_ahead,
            "resource_predictions": {},
            "recommended_actions": []
        }
        
        for resource_type, metrics in self.resource_metrics.items():
            # Simple linear prediction (would use ML in production)
            growth_rate = 0.02  # 2% per hour growth assumption
            predicted_usage = metrics.current_usage * (1 + growth_rate * hours_ahead)
            
            resource_prediction = {
                "current_usage": metrics.current_usage,
                "predicted_usage": predicted_usage,
                "predicted_utilization": (predicted_usage / metrics.capacity) * 100,
                "action_needed": None
            }
            
            if predicted_usage > metrics.capacity * 0.8:
                resource_prediction["action_needed"] = "scale_out"
                predictions["recommended_actions"].append(
                    f"Plan to scale {resource_type.value} within {hours_ahead} hours"
                )
            
            predictions["resource_predictions"][resource_type.value] = resource_prediction
        
        return predictions

    def get_optimizer_status(self) -> Dict[str, Any]:
        """Get comprehensive optimizer status"""
        
        total_nodes = len(self.nodes)
        healthy_nodes = len([n for n in self.nodes.values() if n.health_status == "healthy"])
        total_hourly_cost = sum(node.hourly_cost for node in self.nodes.values())
        
        # Calculate average utilization
        avg_utilization = 0.0
        if self.resource_metrics:
            avg_utilization = sum(m.utilization_percentage for m in self.resource_metrics.values()) / len(self.resource_metrics)
        
        return {
            "optimizer_id": self.optimizer_id,
            "status": "operational",
            "current_strategy": self.current_strategy.value,
            "infrastructure": {
                "total_nodes": total_nodes,
                "healthy_nodes": healthy_nodes,
                "node_groups": {k: len(v) for k, v in self.node_groups.items()},
                "average_utilization": avg_utilization
            },
            "costs": {
                "hourly_cost": total_hourly_cost,
                "daily_cost": total_hourly_cost * 24,
                "monthly_projection": total_hourly_cost * 24 * 30,
                "budget_remaining": self.monthly_budget - (total_hourly_cost * 24 * 30),
                "budget_utilization_percentage": (total_hourly_cost * 24 * 30 / self.monthly_budget) * 100
            },
            "scaling_policies": {
                policy_name: {
                    "resource_type": policy.resource_type.value,
                    "min_instances": policy.min_instances,
                    "max_instances": policy.max_instances,
                    "last_action": policy.last_scaling_action.isoformat() if policy.last_scaling_action else None
                }
                for policy_name, policy in self.scaling_policies.items()
            },
            "optimization_history": len(self.optimization_history),
            "active_scaling_operations": len(self.active_scaling_operations)
        }

    async def start_optimization_loop(self):
        """Start continuous optimization loop"""
        
        logger.info("Starting infrastructure optimization loop")
        
        while True:
            try:
                # Run optimization
                await self.optimize_infrastructure()
                
                # Run auto-scaling
                await self.execute_auto_scaling()
                
                # Wait for next cycle
                await asyncio.sleep(self.optimization_interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(self.optimization_interval_minutes * 60)

# Global infrastructure optimizer instance
infrastructure_optimizer = InfrastructureOptimizer()