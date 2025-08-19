"""
Claude Agent Interface
Integration layer for Claude Code agents in the CoinLink system
"""

import os
import json
import asyncio
import logging
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class AgentInfo:
    """Information about a Claude Code agent"""
    name: str
    description: str
    tools: List[str]
    file_path: str
    status: str = "available"
    last_invoked: Optional[datetime] = None

@dataclass
class AgentTask:
    """Task to be executed by an agent"""
    id: str
    agent_name: str
    description: str
    parameters: Dict[str, Any]
    created_at: datetime
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ClaudeAgentInterface:
    """Interface for Claude Code agents"""
    
    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.agents_dir = os.path.join(self.project_root, ".claude", "agents")
        self.agents: Dict[str, AgentInfo] = {}
        self.active_tasks: Dict[str, AgentTask] = {}
        
        # Load agents on initialization
        self._discover_agents()
    
    def _discover_agents(self):
        """Discover available Claude Code agents"""
        try:
            if not os.path.exists(self.agents_dir):
                logger.warning(f"Agents directory not found: {self.agents_dir}")
                return
            
            for file_path in Path(self.agents_dir).glob("*.md"):
                agent_info = self._parse_agent_file(file_path)
                if agent_info:
                    self.agents[agent_info.name] = agent_info
                    logger.info(f"Discovered agent: {agent_info.name}")
            
            logger.info(f"Total agents discovered: {len(self.agents)}")
            
        except Exception as e:
            logger.error(f"Error discovering agents: {e}")
    
    def _parse_agent_file(self, file_path: Path) -> Optional[AgentInfo]:
        """Parse agent markdown file to extract agent information"""
        try:
            content = file_path.read_text()
            
            # Extract YAML frontmatter
            if content.startswith("---"):
                end_marker = content.find("---", 3)
                if end_marker != -1:
                    frontmatter = content[3:end_marker].strip()
                    
                    # Parse YAML frontmatter manually (simple parser)
                    agent_data = {}
                    for line in frontmatter.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            key = key.strip()
                            value = value.strip()
                            
                            if key == "tools":
                                # Parse tools list
                                agent_data[key] = [tool.strip() for tool in value.split(",")]
                            else:
                                agent_data[key] = value
                    
                    return AgentInfo(
                        name=agent_data.get("name", file_path.stem),
                        description=agent_data.get("description", ""),
                        tools=agent_data.get("tools", []),
                        file_path=str(file_path)
                    )
            
        except Exception as e:
            logger.error(f"Error parsing agent file {file_path}: {e}")
        
        return None
    
    async def invoke_agent(self, agent_name: str, task_description: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Invoke a Claude Code agent via Task tool"""
        try:
            if agent_name not in self.agents:
                raise ValueError(f"Agent '{agent_name}' not found")
            
            agent = self.agents[agent_name]
            task_id = f"{agent_name}_{int(datetime.now().timestamp())}"
            
            # Create task record
            task = AgentTask(
                id=task_id,
                agent_name=agent_name,
                description=task_description,
                parameters=parameters or {},
                created_at=datetime.now()
            )
            self.active_tasks[task_id] = task
            
            # Update agent last invoked time
            agent.last_invoked = datetime.now()
            
            logger.info(f"Invoking agent {agent_name} with task: {task_description}")
            
            # In a real implementation, this would use Claude Code's Task tool
            # For now, we'll simulate the agent response
            result = await self._simulate_agent_execution(agent, task)
            
            # Update task with result
            task.status = "completed"
            task.result = result
            
            return {
                "task_id": task_id,
                "agent_name": agent_name,
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Error invoking agent {agent_name}: {e}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id].status = "error"
                self.active_tasks[task_id].error = str(e)
            
            return {
                "task_id": task_id,
                "agent_name": agent_name,
                "status": "error",
                "error": str(e)
            }
    
    async def _simulate_agent_execution(self, agent: AgentInfo, task: AgentTask) -> Dict[str, Any]:
        """Simulate agent execution (placeholder for real Claude Code integration)"""
        # This is a simulation - in production, this would delegate to Claude Code
        await asyncio.sleep(0.5)  # Simulate processing time
        
        return {
            "agent_response": f"Agent {agent.name} processed task: {task.description}",
            "timestamp": datetime.now().isoformat(),
            "agent_tools_used": agent.tools[:2],  # Simulate tools used
            "performance_metrics": {
                "execution_time": 0.5,
                "success": True
            }
        }
    
    def get_available_agents(self) -> List[Dict[str, Any]]:
        """Get list of available agents"""
        return [
            {
                "name": agent.name,
                "description": agent.description,
                "tools": agent.tools,
                "status": agent.status,
                "last_invoked": agent.last_invoked.isoformat() if agent.last_invoked else None
            }
            for agent in self.agents.values()
        ]
    
    def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific agent"""
        if agent_name not in self.agents:
            return None
        
        agent = self.agents[agent_name]
        
        # Count active tasks for this agent
        active_tasks = sum(1 for task in self.active_tasks.values() 
                          if task.agent_name == agent_name and task.status == "pending")
        
        return {
            "name": agent.name,
            "description": agent.description,
            "tools": agent.tools,
            "status": agent.status,
            "active_tasks": active_tasks,
            "last_invoked": agent.last_invoked.isoformat() if agent.last_invoked else None,
            "file_path": agent.file_path
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall agent system status"""
        total_agents = len(self.agents)
        available_agents = sum(1 for agent in self.agents.values() if agent.status == "available")
        active_tasks = sum(1 for task in self.active_tasks.values() if task.status == "pending")
        completed_tasks = sum(1 for task in self.active_tasks.values() if task.status == "completed")
        
        return {
            "total_agents": total_agents,
            "available_agents": available_agents,
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks,
            "agents_directory": self.agents_dir,
            "last_discovery": datetime.now().isoformat()
        }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task"""
        if task_id not in self.active_tasks:
            return None
        
        task = self.active_tasks[task_id]
        return {
            "id": task.id,
            "agent_name": task.agent_name,
            "description": task.description,
            "parameters": task.parameters,
            "status": task.status,
            "created_at": task.created_at.isoformat(),
            "result": task.result,
            "error": task.error
        }
    
    async def invoke_optimization_cycle(self) -> Dict[str, Any]:
        """Invoke a complete optimization cycle using Helios orchestrator"""
        return await self.invoke_agent(
            "helios-orchestrator",
            "Execute optimization cycle for system-wide performance improvements",
            {"type": "optimization", "mode": "comprehensive"}
        )
    
    async def invoke_emergency_response(self) -> Dict[str, Any]:
        """Invoke emergency response via Helios orchestrator"""
        return await self.invoke_agent(
            "helios-orchestrator",
            "Execute emergency response for critical performance issues",
            {"type": "emergency", "threshold": 0.5}
        )
    
    async def optimize_frontend(self, optimization_type: str = "general") -> Dict[str, Any]:
        """Invoke frontend optimization agents"""
        tasks = []
        
        # Prometheus analyzes, Hephaestus implements, Athena verifies
        analysis_task = await self.invoke_agent(
            "prometheus-frontend",
            f"Analyze frontend for {optimization_type} optimization opportunities",
            {"optimization_type": optimization_type}
        )
        tasks.append(analysis_task)
        
        if analysis_task["status"] == "completed":
            implementation_task = await self.invoke_agent(
                "hephaestus-frontend",
                f"Implement {optimization_type} frontend optimizations",
                {"optimization_type": optimization_type, "analysis_result": analysis_task["result"]}
            )
            tasks.append(implementation_task)
            
            if implementation_task["status"] == "completed":
                verification_task = await self.invoke_agent(
                    "athena-ux",
                    f"Verify {optimization_type} frontend optimization results",
                    {"optimization_type": optimization_type, "implementation_result": implementation_task["result"]}
                )
                tasks.append(verification_task)
        
        return {
            "optimization_type": optimization_type,
            "domain": "frontend",
            "tasks": tasks,
            "status": "completed" if all(t["status"] == "completed" for t in tasks) else "partial"
        }
    
    async def optimize_backend(self, optimization_type: str = "general") -> Dict[str, Any]:
        """Invoke backend optimization agents"""
        tasks = []
        
        # Prometheus analyzes, Hephaestus implements, Athena verifies
        analysis_task = await self.invoke_agent(
            "prometheus-backend",
            f"Analyze backend for {optimization_type} optimization opportunities",
            {"optimization_type": optimization_type}
        )
        tasks.append(analysis_task)
        
        if analysis_task["status"] == "completed":
            implementation_task = await self.invoke_agent(
                "hephaestus-backend",
                f"Implement {optimization_type} backend optimizations",
                {"optimization_type": optimization_type, "analysis_result": analysis_task["result"]}
            )
            tasks.append(implementation_task)
            
            if implementation_task["status"] == "completed":
                verification_task = await self.invoke_agent(
                    "athena-api",
                    f"Verify {optimization_type} backend optimization results",
                    {"optimization_type": optimization_type, "implementation_result": implementation_task["result"]}
                )
                tasks.append(verification_task)
        
        return {
            "optimization_type": optimization_type,
            "domain": "backend",
            "tasks": tasks,
            "status": "completed" if all(t["status"] == "completed" for t in tasks) else "partial"
        }

# Global instance
claude_agents = ClaudeAgentInterface()