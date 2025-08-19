"""
Service Manager - Microservice & API Management System

Ultra-comprehensive service management system that handles microservice
orchestration, API lifecycle management, service discovery, health monitoring,
and automated scaling for maximum system reliability and performance.
"""

import asyncio
import logging
import uuid
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import aiohttp

logger = logging.getLogger(__name__)

class ServiceType(Enum):
    """Types of managed services"""
    API_GATEWAY = "api_gateway"
    MICROSERVICE = "microservice"
    DATABASE = "database"
    CACHE = "cache"
    MESSAGE_QUEUE = "message_queue"
    FILE_STORAGE = "file_storage"
    AUTH_SERVICE = "auth_service"
    MONITORING = "monitoring"

class ServiceStatus(Enum):
    """Service health status"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"
    STARTING = "starting"
    STOPPING = "stopping"

class DeploymentStrategy(Enum):
    """Service deployment strategies"""
    BLUE_GREEN = "blue_green"
    ROLLING = "rolling"
    CANARY = "canary"
    RECREATE = "recreate"

@dataclass
class ServiceDefinition:
    """Service definition and configuration"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    service_type: ServiceType = ServiceType.MICROSERVICE
    version: str = "1.0.0"
    
    # Configuration
    config: Dict[str, Any] = field(default_factory=dict)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    secrets: List[str] = field(default_factory=list)
    
    # Network configuration
    port: int = 8000
    host: str = "0.0.0.0"
    external_ports: List[int] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # Service IDs
    
    # Resource requirements
    cpu_limit: float = 1.0  # CPU cores
    memory_limit: int = 512  # MB
    storage_limit: int = 1024  # MB
    
    # Scaling configuration
    min_replicas: int = 1
    max_replicas: int = 10
    auto_scaling_enabled: bool = False
    scaling_metrics: List[str] = field(default_factory=list)
    
    # Health check configuration
    health_check_path: str = "/health"
    health_check_interval: int = 30  # seconds
    health_check_timeout: int = 10   # seconds
    
    # Deployment configuration
    deployment_strategy: DeploymentStrategy = DeploymentStrategy.ROLLING
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class ServiceInstance:
    """Individual service instance"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_id: str = ""
    instance_name: str = ""
    
    # Runtime information
    status: ServiceStatus = ServiceStatus.STARTING
    host: str = ""
    port: int = 0
    process_id: Optional[int] = None
    
    # Health metrics
    last_health_check: Optional[datetime] = None
    health_check_failures: int = 0
    response_time: float = 0.0
    
    # Resource usage
    cpu_usage: float = 0.0
    memory_usage: int = 0
    network_io: float = 0.0
    
    # Lifecycle
    started_at: Optional[datetime] = None
    last_restart: Optional[datetime] = None
    restart_count: int = 0

@dataclass
class ServiceDeployment:
    """Service deployment tracking"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_id: str = ""
    version: str = ""
    strategy: DeploymentStrategy = DeploymentStrategy.ROLLING
    
    # Deployment state
    status: str = "pending"  # pending, in_progress, completed, failed, rolled_back
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Instance management
    target_instances: int = 0
    healthy_instances: int = 0
    unhealthy_instances: int = 0
    
    # Rollback information
    previous_version: Optional[str] = None
    rollback_enabled: bool = True
    rollback_threshold: float = 0.1  # 10% error rate triggers rollback
    
    # Deployment log
    deployment_log: List[Dict[str, Any]] = field(default_factory=list)

class ServiceManager:
    """Comprehensive service management system"""
    
    def __init__(self):
        self.manager_id = "service_manager"
        
        # Service registry
        self.services: Dict[str, ServiceDefinition] = {}
        self.service_instances: Dict[str, List[ServiceInstance]] = {}
        self.service_deployments: Dict[str, ServiceDeployment] = {}
        
        # Service discovery
        self.service_registry: Dict[str, Dict[str, Any]] = {}
        self.load_balancer_configs: Dict[str, Dict[str, Any]] = {}
        
        # Health monitoring
        self.health_checks: Dict[str, Dict[str, Any]] = {}
        self.service_metrics: Dict[str, Dict[str, float]] = {}
        
        # Auto-scaling
        self.scaling_policies: Dict[str, Dict[str, Any]] = {}
        self.scaling_history: List[Dict[str, Any]] = []
        
        # Configuration
        self.health_check_interval = 30  # seconds
        self.max_health_failures = 3
        self.auto_restart_enabled = True
        self.load_balancing_algorithm = "round_robin"
        
        # Performance metrics
        self.manager_metrics = {
            "total_services": 0,
            "healthy_services": 0,
            "total_instances": 0,
            "healthy_instances": 0,
            "deployments_completed": 0,
            "average_response_time": 0.0
        }
        
        logger.info("Service Manager initialized with comprehensive service orchestration")

    async def register_service(self, service_definition: ServiceDefinition) -> str:
        """Register a new service"""
        service_definition.updated_at = datetime.utcnow()
        
        self.services[service_definition.id] = service_definition
        self.service_instances[service_definition.id] = []
        
        # Initialize health checks
        self.health_checks[service_definition.id] = {
            "enabled": True,
            "path": service_definition.health_check_path,
            "interval": service_definition.health_check_interval,
            "timeout": service_definition.health_check_timeout,
            "last_check": None,
            "consecutive_failures": 0
        }
        
        # Initialize scaling policy if auto-scaling is enabled
        if service_definition.auto_scaling_enabled:
            await self._create_scaling_policy(service_definition)
        
        # Update registry
        await self._update_service_registry(service_definition)
        
        self.manager_metrics["total_services"] = len(self.services)
        
        logger.info(f"Registered service: {service_definition.name} ({service_definition.id})")
        
        return service_definition.id

    async def deploy_service(self, service_id: str, target_version: str = None,
                           strategy: DeploymentStrategy = None) -> Dict[str, Any]:
        """Deploy a service with specified strategy"""
        if service_id not in self.services:
            raise ValueError(f"Service {service_id} not found")
        
        service = self.services[service_id]
        deployment_strategy = strategy or service.deployment_strategy
        version = target_version or service.version
        
        # Create deployment record
        deployment = ServiceDeployment(
            service_id=service_id,
            version=version,
            strategy=deployment_strategy,
            target_instances=service.min_replicas,
            started_at=datetime.utcnow()
        )
        
        self.service_deployments[deployment.id] = deployment
        
        logger.info(f"Starting deployment: {service.name} v{version} using {deployment_strategy.value}")
        
        try:
            deployment.status = "in_progress"
            
            # Execute deployment based on strategy
            if deployment_strategy == DeploymentStrategy.BLUE_GREEN:
                result = await self._execute_blue_green_deployment(deployment)
            elif deployment_strategy == DeploymentStrategy.ROLLING:
                result = await self._execute_rolling_deployment(deployment)
            elif deployment_strategy == DeploymentStrategy.CANARY:
                result = await self._execute_canary_deployment(deployment)
            else:
                result = await self._execute_recreate_deployment(deployment)
            
            deployment.status = "completed"
            deployment.completed_at = datetime.utcnow()
            
            # Update metrics
            self.manager_metrics["deployments_completed"] += 1
            
            logger.info(f"Deployment completed: {service.name} v{version}")
            
            return {
                "success": True,
                "deployment_id": deployment.id,
                "service_id": service_id,
                "version": version,
                "strategy": deployment_strategy.value,
                "instances_deployed": result.get("instances_deployed", 0),
                "deployment_time": (deployment.completed_at - deployment.started_at).total_seconds()
            }
            
        except Exception as e:
            deployment.status = "failed"
            deployment.completed_at = datetime.utcnow()
            
            logger.error(f"Deployment failed: {service.name} v{version} - {str(e)}")
            
            return {
                "success": False,
                "deployment_id": deployment.id,
                "error": str(e)
            }

    async def _execute_rolling_deployment(self, deployment: ServiceDeployment) -> Dict[str, Any]:
        """Execute rolling deployment strategy"""
        service = self.services[deployment.service_id]
        current_instances = self.service_instances[deployment.service_id]
        
        # Calculate rolling update batches
        batch_size = max(1, len(current_instances) // 3)  # Replace 1/3 at a time
        instances_deployed = 0
        
        # Rolling update in batches
        for i in range(0, len(current_instances), batch_size):
            batch = current_instances[i:i + batch_size]
            
            # Stop old instances in batch
            for instance in batch:
                await self._stop_service_instance(instance)
            
            # Start new instances
            for _ in range(len(batch)):
                new_instance = await self._start_service_instance(service, deployment.version)
                instances_deployed += 1
                
                # Wait for health check
                if not await self._wait_for_healthy_instance(new_instance, timeout=60):
                    raise Exception(f"New instance failed health check: {new_instance.id}")
            
            # Small delay between batches
            await asyncio.sleep(5)
        
        return {"instances_deployed": instances_deployed}

    async def _execute_blue_green_deployment(self, deployment: ServiceDeployment) -> Dict[str, Any]:
        """Execute blue-green deployment strategy"""
        service = self.services[deployment.service_id]
        
        # Start new "green" instances
        green_instances = []
        for _ in range(deployment.target_instances):
            instance = await self._start_service_instance(service, deployment.version)
            green_instances.append(instance)
        
        # Wait for all green instances to be healthy
        healthy_count = 0
        for instance in green_instances:
            if await self._wait_for_healthy_instance(instance, timeout=120):
                healthy_count += 1
        
        if healthy_count < len(green_instances):
            # Cleanup failed instances
            for instance in green_instances:
                await self._stop_service_instance(instance)
            raise Exception("Not all green instances became healthy")
        
        # Switch traffic to green instances (update load balancer)
        await self._update_load_balancer(deployment.service_id, green_instances)
        
        # Stop old "blue" instances
        old_instances = self.service_instances[deployment.service_id].copy()
        for instance in old_instances:
            if instance not in green_instances:
                await self._stop_service_instance(instance)
        
        return {"instances_deployed": len(green_instances)}

    async def _execute_canary_deployment(self, deployment: ServiceDeployment) -> Dict[str, Any]:
        """Execute canary deployment strategy"""
        service = self.services[deployment.service_id]
        current_instances = self.service_instances[deployment.service_id]
        
        # Start one canary instance
        canary_instance = await self._start_service_instance(service, deployment.version)
        
        if not await self._wait_for_healthy_instance(canary_instance, timeout=60):
            await self._stop_service_instance(canary_instance)
            raise Exception("Canary instance failed health check")
        
        # Monitor canary performance for 5 minutes
        canary_metrics = await self._monitor_canary_instance(canary_instance, duration=300)
        
        # Check if canary metrics are acceptable
        if canary_metrics["error_rate"] > 0.01 or canary_metrics["avg_response_time"] > 1000:
            await self._stop_service_instance(canary_instance)
            raise Exception("Canary metrics exceeded acceptable thresholds")
        
        # Gradually replace all instances
        for instance in current_instances:
            if instance.id != canary_instance.id:
                await self._stop_service_instance(instance)
                new_instance = await self._start_service_instance(service, deployment.version)
                
                if not await self._wait_for_healthy_instance(new_instance, timeout=60):
                    raise Exception(f"Instance replacement failed: {new_instance.id}")
                
                await asyncio.sleep(10)  # Gradual rollout
        
        return {"instances_deployed": len(self.service_instances[deployment.service_id])}

    async def _execute_recreate_deployment(self, deployment: ServiceDeployment) -> Dict[str, Any]:
        """Execute recreate deployment strategy"""
        service = self.services[deployment.service_id]
        current_instances = self.service_instances[deployment.service_id]
        
        # Stop all current instances
        for instance in current_instances:
            await self._stop_service_instance(instance)
        
        # Start new instances
        instances_deployed = 0
        for _ in range(deployment.target_instances):
            instance = await self._start_service_instance(service, deployment.version)
            instances_deployed += 1
            
            if not await self._wait_for_healthy_instance(instance, timeout=60):
                raise Exception(f"New instance failed health check: {instance.id}")
        
        return {"instances_deployed": instances_deployed}

    async def _start_service_instance(self, service: ServiceDefinition, version: str) -> ServiceInstance:
        """Start a new service instance"""
        instance = ServiceInstance(
            service_id=service.id,
            instance_name=f"{service.name}-{uuid.uuid4().hex[:8]}",
            host=service.host,
            port=service.port,
            started_at=datetime.utcnow()
        )
        
        # Simulate instance startup
        instance.status = ServiceStatus.STARTING
        await asyncio.sleep(2)  # Simulate startup time
        
        # Add to service instances
        if service.id not in self.service_instances:
            self.service_instances[service.id] = []
        self.service_instances[service.id].append(instance)
        
        # Simulate successful startup
        instance.status = ServiceStatus.HEALTHY
        instance.cpu_usage = 15.5
        instance.memory_usage = 128
        
        logger.info(f"Started service instance: {instance.instance_name}")
        
        return instance

    async def _stop_service_instance(self, instance: ServiceInstance):
        """Stop a service instance"""
        instance.status = ServiceStatus.STOPPING
        
        # Simulate graceful shutdown
        await asyncio.sleep(1)
        
        # Remove from service instances
        if instance.service_id in self.service_instances:
            if instance in self.service_instances[instance.service_id]:
                self.service_instances[instance.service_id].remove(instance)
        
        logger.info(f"Stopped service instance: {instance.instance_name}")

    async def _wait_for_healthy_instance(self, instance: ServiceInstance, timeout: int = 60) -> bool:
        """Wait for instance to become healthy"""
        start_time = datetime.utcnow()
        
        while (datetime.utcnow() - start_time).total_seconds() < timeout:
            if instance.status == ServiceStatus.HEALTHY:
                return True
            
            # Perform health check
            if await self._perform_health_check(instance):
                instance.status = ServiceStatus.HEALTHY
                return True
            
            await asyncio.sleep(5)
        
        return False

    async def _perform_health_check(self, instance: ServiceInstance) -> bool:
        """Perform health check on service instance"""
        try:
            # Simulate health check (in production, this would be an actual HTTP request)
            instance.last_health_check = datetime.utcnow()
            instance.response_time = 0.15  # Simulate 150ms response time
            
            # Simulate occasional failures
            import random
            if random.random() < 0.05:  # 5% failure rate
                instance.health_check_failures += 1
                return False
            
            instance.health_check_failures = 0
            return True
            
        except Exception as e:
            instance.health_check_failures += 1
            logger.warning(f"Health check failed for {instance.instance_name}: {str(e)}")
            return False

    async def _monitor_canary_instance(self, instance: ServiceInstance, duration: int) -> Dict[str, float]:
        """Monitor canary instance performance"""
        start_time = datetime.utcnow()
        metrics = {
            "error_rate": 0.0,
            "avg_response_time": 0.0,
            "request_count": 0
        }
        
        # Simulate monitoring for specified duration
        while (datetime.utcnow() - start_time).total_seconds() < duration:
            await asyncio.sleep(10)
            
            # Simulate metrics collection
            metrics["request_count"] += 100
            metrics["avg_response_time"] = 185.5  # Simulated
            metrics["error_rate"] = 0.005  # 0.5% error rate
        
        return metrics

    async def _update_load_balancer(self, service_id: str, instances: List[ServiceInstance]):
        """Update load balancer configuration"""
        service = self.services[service_id]
        
        backend_config = {
            "service_id": service_id,
            "service_name": service.name,
            "algorithm": self.load_balancing_algorithm,
            "health_check": {
                "path": service.health_check_path,
                "interval": service.health_check_interval
            },
            "backends": [
                {
                    "instance_id": instance.id,
                    "host": instance.host,
                    "port": instance.port,
                    "weight": 1
                }
                for instance in instances if instance.status == ServiceStatus.HEALTHY
            ]
        }
        
        self.load_balancer_configs[service_id] = backend_config
        
        logger.info(f"Updated load balancer for {service.name}: {len(backend_config['backends'])} backends")

    async def _create_scaling_policy(self, service: ServiceDefinition):
        """Create auto-scaling policy for service"""
        policy = {
            "service_id": service.id,
            "min_replicas": service.min_replicas,
            "max_replicas": service.max_replicas,
            "metrics": service.scaling_metrics or ["cpu_usage", "memory_usage"],
            "scale_up_threshold": 80.0,    # CPU/Memory threshold to scale up
            "scale_down_threshold": 30.0,  # CPU/Memory threshold to scale down
            "scale_up_cooldown": 300,      # 5 minutes cooldown after scale up
            "scale_down_cooldown": 600,    # 10 minutes cooldown after scale down
            "last_scale_action": None
        }
        
        self.scaling_policies[service.id] = policy
        
        logger.info(f"Created auto-scaling policy for {service.name}")

    async def _update_service_registry(self, service: ServiceDefinition):
        """Update service discovery registry"""
        registry_entry = {
            "service_id": service.id,
            "service_name": service.name,
            "service_type": service.service_type.value,
            "version": service.version,
            "port": service.port,
            "health_check_path": service.health_check_path,
            "dependencies": service.dependencies,
            "tags": service.tags,
            "updated_at": service.updated_at.isoformat()
        }
        
        self.service_registry[service.id] = registry_entry

    async def scale_service(self, service_id: str, target_replicas: int) -> Dict[str, Any]:
        """Manually scale service to target replica count"""
        if service_id not in self.services:
            raise ValueError(f"Service {service_id} not found")
        
        service = self.services[service_id]
        current_instances = self.service_instances[service_id]
        current_count = len(current_instances)
        
        logger.info(f"Scaling {service.name} from {current_count} to {target_replicas} instances")
        
        if target_replicas > current_count:
            # Scale up
            instances_to_add = target_replicas - current_count
            new_instances = []
            
            for _ in range(instances_to_add):
                instance = await self._start_service_instance(service, service.version)
                new_instances.append(instance)
            
            # Wait for new instances to be healthy
            healthy_count = 0
            for instance in new_instances:
                if await self._wait_for_healthy_instance(instance, timeout=60):
                    healthy_count += 1
            
            return {
                "success": True,
                "action": "scale_up",
                "previous_count": current_count,
                "target_count": target_replicas,
                "healthy_instances": healthy_count
            }
        
        elif target_replicas < current_count:
            # Scale down
            instances_to_remove = current_count - target_replicas
            
            # Remove least healthy instances first
            instances_sorted = sorted(current_instances, 
                                    key=lambda x: (x.health_check_failures, -x.cpu_usage))
            
            for i in range(instances_to_remove):
                await self._stop_service_instance(instances_sorted[i])
            
            return {
                "success": True,
                "action": "scale_down",
                "previous_count": current_count,
                "target_count": target_replicas,
                "instances_removed": instances_to_remove
            }
        
        return {
            "success": True,
            "action": "no_change",
            "current_count": current_count
        }

    async def start_health_monitoring(self):
        """Start continuous health monitoring for all services"""
        logger.info("Starting service health monitoring")
        
        while True:
            try:
                await self._perform_health_monitoring_cycle()
                await asyncio.sleep(self.health_check_interval)
            except Exception as e:
                logger.error(f"Error in health monitoring cycle: {e}")
                await asyncio.sleep(self.health_check_interval * 2)

    async def _perform_health_monitoring_cycle(self):
        """Perform health checks on all service instances"""
        total_instances = 0
        healthy_instances = 0
        
        for service_id, instances in self.service_instances.items():
            for instance in instances:
                total_instances += 1
                
                is_healthy = await self._perform_health_check(instance)
                
                if is_healthy:
                    healthy_instances += 1
                    if instance.status != ServiceStatus.HEALTHY:
                        instance.status = ServiceStatus.HEALTHY
                        logger.info(f"Instance recovered: {instance.instance_name}")
                else:
                    if instance.health_check_failures >= self.max_health_failures:
                        instance.status = ServiceStatus.CRITICAL
                        logger.warning(f"Instance critical: {instance.instance_name}")
                        
                        # Auto-restart if enabled
                        if self.auto_restart_enabled:
                            await self._restart_service_instance(instance)
                    else:
                        instance.status = ServiceStatus.WARNING
        
        # Update metrics
        self.manager_metrics.update({
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "healthy_services": len([s for s in self.services.keys() 
                                   if all(i.status == ServiceStatus.HEALTHY 
                                         for i in self.service_instances.get(s, []))])
        })

    async def _restart_service_instance(self, instance: ServiceInstance):
        """Restart a failed service instance"""
        logger.info(f"Restarting failed instance: {instance.instance_name}")
        
        service = self.services[instance.service_id]
        
        # Stop current instance
        await self._stop_service_instance(instance)
        
        # Start new instance
        new_instance = await self._start_service_instance(service, service.version)
        new_instance.restart_count = instance.restart_count + 1
        new_instance.last_restart = datetime.utcnow()

    def get_manager_status(self) -> Dict[str, Any]:
        """Get comprehensive service manager status"""
        return {
            "manager_id": self.manager_id,
            "status": "operational",
            "services": {
                "total": len(self.services),
                "by_type": {
                    service_type.value: len([s for s in self.services.values() 
                                           if s.service_type == service_type])
                    for service_type in ServiceType
                }
            },
            "instances": {
                "total": sum(len(instances) for instances in self.service_instances.values()),
                "by_status": {
                    status.value: sum(
                        len([i for i in instances if i.status == status])
                        for instances in self.service_instances.values()
                    )
                    for status in ServiceStatus
                }
            },
            "deployments": {
                "total": len(self.service_deployments),
                "completed": len([d for d in self.service_deployments.values() 
                               if d.status == "completed"]),
                "in_progress": len([d for d in self.service_deployments.values() 
                                  if d.status == "in_progress"])
            },
            "load_balancer_configs": len(self.load_balancer_configs),
            "scaling_policies": len(self.scaling_policies),
            "metrics": self.manager_metrics
        }

    def get_service_details(self, service_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific service"""
        if service_id not in self.services:
            return None
        
        service = self.services[service_id]
        instances = self.service_instances.get(service_id, [])
        
        return {
            "service": {
                "id": service.id,
                "name": service.name,
                "type": service.service_type.value,
                "version": service.version,
                "status": "healthy" if all(i.status == ServiceStatus.HEALTHY for i in instances) else "unhealthy",
                "port": service.port,
                "created_at": service.created_at.isoformat(),
                "updated_at": service.updated_at.isoformat()
            },
            "instances": [
                {
                    "id": instance.id,
                    "name": instance.instance_name,
                    "status": instance.status.value,
                    "host": instance.host,
                    "port": instance.port,
                    "cpu_usage": instance.cpu_usage,
                    "memory_usage": instance.memory_usage,
                    "last_health_check": instance.last_health_check.isoformat() if instance.last_health_check else None,
                    "health_failures": instance.health_check_failures,
                    "restart_count": instance.restart_count
                }
                for instance in instances
            ],
            "scaling_policy": self.scaling_policies.get(service_id),
            "load_balancer_config": self.load_balancer_configs.get(service_id)
        }

# Global service manager instance
service_manager = ServiceManager()