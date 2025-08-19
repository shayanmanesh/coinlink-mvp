"""
Base agent classes for the CoinLink optimization framework
"""

import asyncio
import time
import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class AgentRole(Enum):
    """Agent role definitions"""
    ORCHESTRATOR = "orchestrator"
    STRATEGIST = "strategist"  # Prometheus
    BUILDER = "builder"        # Hephaestus
    VERIFIER = "verifier"      # Athena

class AgentDomain(Enum):
    """Agent domain focus"""
    FRONTEND = "frontend"
    BACKEND = "backend"
    FULLSTACK = "fullstack"

@dataclass
class AgentTask:
    """Represents a task assigned to an agent"""
    id: str
    type: str
    priority: int
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    assigned_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@dataclass
class AgentMetrics:
    """Agent performance metrics"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_execution_time: float = 0.0
    success_rate: float = 0.0
    last_active: Optional[datetime] = None
    learning_rate: float = 0.0

class BaseAgent(ABC):
    """Base class for all CoinLink agents"""
    
    def __init__(self, 
                 name: str,
                 role: AgentRole,
                 domain: AgentDomain,
                 tools: List[str] = None):
        self.name = name
        self.role = role
        self.domain = domain
        self.tools = tools or []
        self.metrics = AgentMetrics()
        self.task_queue = asyncio.Queue()
        self.running = False
        self.learning_data = []
        
        # Set up logging
        self.logger = logging.getLogger(f"agent.{name}")
        
    async def start(self):
        """Start the agent execution loop"""
        self.running = True
        self.logger.info(f"Agent {self.name} starting...")
        
        # Start the main execution loop
        await self.execution_loop()
    
    async def stop(self):
        """Stop the agent"""
        self.running = False
        self.logger.info(f"Agent {self.name} stopping...")
    
    async def execution_loop(self):
        """Main agent execution loop"""
        while self.running:
            try:
                # Check for new tasks
                try:
                    task = await asyncio.wait_for(
                        self.task_queue.get(), 
                        timeout=1.0
                    )
                    await self.execute_task(task)
                except asyncio.TimeoutError:
                    # No task available, do background work
                    await self.background_work()
                    
            except Exception as e:
                self.logger.error(f"Error in execution loop: {e}")
                await asyncio.sleep(1)
    
    async def execute_task(self, task: AgentTask):
        """Execute a single task"""
        start_time = time.time()
        task.started_at = datetime.now()
        
        try:
            self.logger.info(f"Executing task: {task.description}")
            
            # Call the specific task implementation
            result = await self.process_task(task)
            
            # Record success
            task.completed_at = datetime.now()
            task.result = result
            
            execution_time = time.time() - start_time
            self.update_metrics(success=True, execution_time=execution_time)
            
            # Learn from successful execution
            await self.learn_from_task(task, success=True)
            
            self.logger.info(f"Task completed successfully in {execution_time:.2f}s")
            
        except Exception as e:
            # Record failure
            task.error = str(e)
            execution_time = time.time() - start_time
            self.update_metrics(success=False, execution_time=execution_time)
            
            # Learn from failure
            await self.learn_from_task(task, success=False)
            
            self.logger.error(f"Task failed: {e}")
    
    @abstractmethod
    async def process_task(self, task: AgentTask) -> Dict[str, Any]:
        """Process a specific task - must be implemented by subclasses"""
        pass
    
    async def background_work(self):
        """Background work when no tasks are queued"""
        # Default: sleep briefly
        await asyncio.sleep(0.1)
    
    async def assign_task(self, task: AgentTask):
        """Assign a task to this agent"""
        await self.task_queue.put(task)
    
    def update_metrics(self, success: bool, execution_time: float):
        """Update agent performance metrics"""
        if success:
            self.metrics.tasks_completed += 1
        else:
            self.metrics.tasks_failed += 1
        
        total_tasks = self.metrics.tasks_completed + self.metrics.tasks_failed
        self.metrics.success_rate = self.metrics.tasks_completed / total_tasks if total_tasks > 0 else 0
        
        # Update average execution time
        if self.metrics.tasks_completed > 0:
            old_avg = self.metrics.average_execution_time
            n = self.metrics.tasks_completed
            self.metrics.average_execution_time = (old_avg * (n - 1) + execution_time) / n
        
        self.metrics.last_active = datetime.now()
    
    async def learn_from_task(self, task: AgentTask, success: bool):
        """Learn from task execution for self-improvement"""
        learning_point = {
            "task_type": task.type,
            "parameters": task.parameters,
            "success": success,
            "execution_time": (task.completed_at - task.started_at).total_seconds() if task.completed_at else None,
            "timestamp": datetime.now().isoformat()
        }
        
        self.learning_data.append(learning_point)
        
        # Keep only recent learning data (last 1000 points)
        if len(self.learning_data) > 1000:
            self.learning_data = self.learning_data[-1000:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "name": self.name,
            "role": self.role.value,
            "domain": self.domain.value,
            "running": self.running,
            "queue_size": self.task_queue.qsize(),
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "success_rate": self.metrics.success_rate,
                "average_execution_time": self.metrics.average_execution_time,
                "last_active": self.metrics.last_active.isoformat() if self.metrics.last_active else None
            }
        }


class AgentSwarm:
    """Manages a group of related agents"""
    
    def __init__(self, name: str, domain: AgentDomain):
        self.name = name
        self.domain = domain
        self.agents: Dict[str, BaseAgent] = {}
        self.running = False
        
    def add_agent(self, agent: BaseAgent):
        """Add an agent to the swarm"""
        self.agents[agent.name] = agent
    
    async def start_all(self):
        """Start all agents in the swarm"""
        self.running = True
        tasks = [agent.start() for agent in self.agents.values()]
        await asyncio.gather(*tasks)
    
    async def stop_all(self):
        """Stop all agents in the swarm"""
        self.running = False
        tasks = [agent.stop() for agent in self.agents.values()]
        await asyncio.gather(*tasks)
    
    async def assign_task_to_agent(self, agent_name: str, task: AgentTask):
        """Assign a task to a specific agent"""
        if agent_name in self.agents:
            await self.agents[agent_name].assign_task(task)
        else:
            raise ValueError(f"Agent {agent_name} not found in swarm")
    
    async def assign_task_to_role(self, role: AgentRole, task: AgentTask):
        """Assign a task to the first available agent with the specified role"""
        for agent in self.agents.values():
            if agent.role == role:
                await agent.assign_task(task)
                return
        raise ValueError(f"No agent with role {role.value} found in swarm")
    
    def get_swarm_status(self) -> Dict[str, Any]:
        """Get status of all agents in the swarm"""
        return {
            "name": self.name,
            "domain": self.domain.value,
            "running": self.running,
            "agent_count": len(self.agents),
            "agents": {name: agent.get_status() for name, agent in self.agents.items()}
        }


class SpecializedAgent(BaseAgent):
    """Base class for specialized agents with domain-specific functionality"""
    
    def __init__(self, name: str, role: AgentRole, domain: AgentDomain, specialization: str):
        super().__init__(name, role, domain)
        self.specialization = specialization
        self.optimization_history = []
        
    async def optimize(self, target: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main optimization method for specialized agents"""
        task = AgentTask(
            id=f"{self.name}_{int(time.time())}",
            type="optimization",
            priority=1,
            description=f"Optimize {target}",
            parameters={"target": target, **(parameters or {})}
        )
        
        await self.assign_task(task)
        
        # Wait for task completion
        while task.completed_at is None and task.error is None:
            await asyncio.sleep(0.1)
        
        if task.error:
            raise Exception(f"Optimization failed: {task.error}")
        
        return task.result
    
    def record_optimization(self, optimization_type: str, before: Dict, after: Dict):
        """Record optimization results for learning"""
        record = {
            "type": optimization_type,
            "before": before,
            "after": after,
            "improvement": self.calculate_improvement(before, after),
            "timestamp": datetime.now().isoformat()
        }
        
        self.optimization_history.append(record)
        
        # Keep only recent history
        if len(self.optimization_history) > 500:
            self.optimization_history = self.optimization_history[-500:]
    
    def calculate_improvement(self, before: Dict, after: Dict) -> Dict[str, float]:
        """Calculate improvement metrics"""
        improvements = {}
        
        for key in before:
            if key in after and isinstance(before[key], (int, float)) and isinstance(after[key], (int, float)):
                if before[key] != 0:
                    improvement = ((after[key] - before[key]) / before[key]) * 100
                    improvements[key] = improvement
        
        return improvements