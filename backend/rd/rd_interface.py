"""
R&D Agent Interface System
Specialized interface for R&D department agents with innovation-focused capabilities
"""

import os
import json
import asyncio
import logging
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path
import uuid

logger = logging.getLogger(__name__)

@dataclass
class RDAgentInfo:
    """Information about an R&D agent"""
    name: str
    description: str
    tools: List[str]
    file_path: str
    department: str = "rd"
    specialization: str = ""
    status: str = "available"
    last_invoked: Optional[datetime] = None
    total_invocations: int = 0
    success_rate: float = 0.0

@dataclass
class InnovationTask:
    """Task specific to R&D innovation cycles"""
    id: str
    agent_name: str
    task_type: str  # intelligence, analysis, strategy, prototype, integration, feedback
    description: str
    parameters: Dict[str, Any]
    created_at: datetime
    priority: str = "medium"  # low, medium, high, critical
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    innovation_cycle_id: Optional[str] = None

@dataclass
class InnovationCycle:
    """Weekly innovation cycle tracking"""
    id: str
    start_date: datetime
    end_date: datetime
    status: str = "active"  # active, completed, cancelled
    tasks: List[str] = None  # Task IDs
    intelligence_summary: Optional[Dict[str, Any]] = None
    insights_generated: int = 0
    prototypes_created: int = 0
    recommendations_count: int = 0

class RDAgentInterface:
    """Specialized interface for R&D department agents"""
    
    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.rd_agents_dir = os.path.join(self.project_root, ".claude", "agents", "rd")
        self.agents: Dict[str, RDAgentInfo] = {}
        self.active_tasks: Dict[str, InnovationTask] = {}
        self.innovation_cycles: Dict[str, InnovationCycle] = {}
        self.current_cycle_id: Optional[str] = None
        
        # R&D specific metrics
        self.innovation_metrics = {
            "total_features_ideated": 0,
            "total_prototypes_created": 0,
            "total_research_papers_analyzed": 0,
            "total_competitor_insights": 0,
            "innovation_cycles_completed": 0,
            "average_cycle_success_rate": 0.0
        }
        
        # Load R&D agents on initialization
        self._discover_rd_agents()
        
    def _discover_rd_agents(self):
        """Discover available R&D agents"""
        try:
            if not os.path.exists(self.rd_agents_dir):
                logger.warning(f"R&D agents directory not found: {self.rd_agents_dir}")
                return
            
            for file_path in Path(self.rd_agents_dir).glob("*.md"):
                agent_info = self._parse_rd_agent_file(file_path)
                if agent_info:
                    self.agents[agent_info.name] = agent_info
                    logger.info(f"Discovered R&D agent: {agent_info.name}")
            
            logger.info(f"Total R&D agents discovered: {len(self.agents)}")
            
        except Exception as e:
            logger.error(f"Error discovering R&D agents: {e}")
    
    def _parse_rd_agent_file(self, file_path: Path) -> Optional[RDAgentInfo]:
        """Parse R&D agent markdown file to extract agent information"""
        try:
            content = file_path.read_text()
            
            # Extract YAML frontmatter
            if content.startswith("---"):
                end_marker = content.find("---", 3)
                if end_marker != -1:
                    frontmatter = content[3:end_marker].strip()
                    
                    # Parse YAML frontmatter
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
                    
                    # Determine specialization based on agent name
                    specialization = self._determine_specialization(agent_data.get("name", ""))
                    
                    return RDAgentInfo(
                        name=agent_data.get("name", file_path.stem),
                        description=agent_data.get("description", ""),
                        tools=agent_data.get("tools", []),
                        file_path=str(file_path),
                        specialization=specialization
                    )
        except Exception as e:
            logger.error(f"Error parsing R&D agent file {file_path}: {e}")
        
        return None
    
    def _determine_specialization(self, agent_name: str) -> str:
        """Determine agent specialization based on name"""
        specializations = {
            "apollo-rd-orchestrator": "orchestration",
            "argus-competitor": "competitive_intelligence", 
            "minerva-research": "research_analysis",
            "vulcan-strategy": "feature_strategy",
            "daedalus-prototype": "prototyping",
            "mercury-integration": "integration_planning",
            "echo-feedback": "user_feedback_analysis"
        }
        return specializations.get(agent_name, "general")
    
    def get_rd_agents(self) -> List[Dict[str, Any]]:
        """Get list of all R&D agents with their information"""
        return [
            {
                "name": agent.name,
                "description": agent.description,
                "tools": agent.tools,
                "specialization": agent.specialization,
                "status": agent.status,
                "total_invocations": agent.total_invocations,
                "success_rate": agent.success_rate,
                "last_invoked": agent.last_invoked.isoformat() if agent.last_invoked else None
            }
            for agent in self.agents.values()
        ]
    
    def get_rd_system_status(self) -> Dict[str, Any]:
        """Get overall R&D system status"""
        return {
            "total_rd_agents": len(self.agents),
            "available_agents": len([a for a in self.agents.values() if a.status == "available"]),
            "active_innovation_tasks": len([t for t in self.active_tasks.values() if t.status == "in_progress"]),
            "completed_innovation_tasks": len([t for t in self.active_tasks.values() if t.status == "completed"]),
            "current_innovation_cycle": self.current_cycle_id,
            "rd_agents_directory": self.rd_agents_dir,
            "last_discovery": datetime.now().isoformat(),
            "innovation_metrics": self.innovation_metrics
        }
    
    def get_rd_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific R&D agent"""
        if agent_name not in self.agents:
            return None
        
        agent = self.agents[agent_name]
        active_tasks = [
            task_id for task_id, task in self.active_tasks.items()
            if task.agent_name == agent_name and task.status in ["pending", "in_progress"]
        ]
        
        return {
            "name": agent.name,
            "description": agent.description,
            "specialization": agent.specialization,
            "tools": agent.tools,
            "status": agent.status,
            "active_tasks": len(active_tasks),
            "total_invocations": agent.total_invocations,
            "success_rate": agent.success_rate,
            "last_invoked": agent.last_invoked.isoformat() if agent.last_invoked else None
        }
    
    async def invoke_rd_agent(self, agent_name: str, task_type: str, 
                             description: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Invoke a specific R&D agent with innovation task"""
        if agent_name not in self.agents:
            raise ValueError(f"R&D agent '{agent_name}' not found")
        
        agent = self.agents[agent_name]
        task_id = str(uuid.uuid4())
        
        # Create innovation task
        task = InnovationTask(
            id=task_id,
            agent_name=agent_name,
            task_type=task_type,
            description=description,
            parameters=parameters or {},
            created_at=datetime.now(),
            innovation_cycle_id=self.current_cycle_id
        )
        
        self.active_tasks[task_id] = task
        
        try:
            # Update agent status
            agent.status = "busy"
            task.status = "in_progress"
            
            # Simulate agent execution (in production, this would call actual Claude Code agent)
            await asyncio.sleep(1)  # Simulated processing time
            
            # Mock successful result based on agent specialization
            result = self._generate_mock_result(agent, task)
            
            # Update task and agent
            task.status = "completed"
            task.result = result
            agent.status = "available"
            agent.last_invoked = datetime.now()
            agent.total_invocations += 1
            
            # Update success rate
            successful_tasks = len([
                t for t in self.active_tasks.values() 
                if t.agent_name == agent_name and t.status == "completed"
            ])
            agent.success_rate = successful_tasks / agent.total_invocations
            
            logger.info(f"R&D agent {agent_name} completed task {task_id}")
            
            return {
                "task_id": task_id,
                "agent_name": agent_name,
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            agent.status = "available"
            logger.error(f"R&D agent {agent_name} failed task {task_id}: {e}")
            
            return {
                "task_id": task_id,
                "agent_name": agent_name,
                "status": "failed",
                "error": str(e)
            }
    
    def _generate_mock_result(self, agent: RDAgentInfo, task: InnovationTask) -> Dict[str, Any]:
        """Generate mock result based on agent specialization"""
        base_result = {
            "task_type": task.task_type,
            "agent_specialization": agent.specialization,
            "timestamp": datetime.now().isoformat(),
            "success": True
        }
        
        if agent.specialization == "competitive_intelligence":
            return {
                **base_result,
                "competitors_analyzed": 5,
                "new_features_detected": 3,
                "threat_level": "medium",
                "opportunities_identified": 2,
                "intelligence_summary": "Competitive analysis completed with actionable insights"
            }
        elif agent.specialization == "research_analysis":
            return {
                **base_result,
                "papers_analyzed": 8,
                "breakthrough_technologies": 2,
                "implementation_opportunities": 4,
                "innovation_potential": "high",
                "research_summary": "Cutting-edge research analysis with practical applications identified"
            }
        elif agent.specialization == "feature_strategy":
            return {
                **base_result,
                "features_ideated": 6,
                "market_opportunities": 3,
                "strategic_recommendations": 4,
                "competitive_advantage_score": 85,
                "strategy_summary": "Strategic feature concepts with market validation"
            }
        elif agent.specialization == "prototyping":
            return {
                **base_result,
                "prototypes_created": 2,
                "technical_validation": "successful",
                "user_experience_score": 82,
                "implementation_complexity": "medium",
                "prototype_summary": "Functional prototypes ready for stakeholder review"
            }
        elif agent.specialization == "integration_planning":
            return {
                **base_result,
                "integration_complexity": "medium",
                "timeline_estimate": "2-3 weeks",
                "resource_requirements": "standard",
                "risk_assessment": "low",
                "integration_summary": "Production integration plan with risk mitigation"
            }
        elif agent.specialization == "user_feedback_analysis":
            return {
                **base_result,
                "feedback_sources_analyzed": 12,
                "user_insights_generated": 8,
                "feature_requests_identified": 5,
                "satisfaction_trends": "positive",
                "feedback_summary": "User intelligence with actionable feature recommendations"
            }
        else:  # orchestration
            return {
                **base_result,
                "coordination_tasks": 6,
                "cycle_progress": "on_track",
                "team_utilization": "optimal",
                "strategic_insights": 4,
                "orchestration_summary": "R&D cycle coordination with strategic oversight"
            }
    
    def start_innovation_cycle(self) -> str:
        """Start a new weekly innovation cycle"""
        cycle_id = str(uuid.uuid4())
        cycle = InnovationCycle(
            id=cycle_id,
            start_date=datetime.now(),
            end_date=datetime.now().replace(hour=23, minute=59, second=59),  # End of day
            tasks=[]
        )
        
        self.innovation_cycles[cycle_id] = cycle
        self.current_cycle_id = cycle_id
        
        logger.info(f"Started innovation cycle {cycle_id}")
        return cycle_id
    
    def get_innovation_cycle_status(self, cycle_id: str = None) -> Optional[Dict[str, Any]]:
        """Get status of innovation cycle"""
        cycle_id = cycle_id or self.current_cycle_id
        if not cycle_id or cycle_id not in self.innovation_cycles:
            return None
        
        cycle = self.innovation_cycles[cycle_id]
        cycle_tasks = [
            task for task in self.active_tasks.values()
            if task.innovation_cycle_id == cycle_id
        ]
        
        return {
            "cycle_id": cycle.id,
            "start_date": cycle.start_date.isoformat(),
            "end_date": cycle.end_date.isoformat(),
            "status": cycle.status,
            "total_tasks": len(cycle_tasks),
            "completed_tasks": len([t for t in cycle_tasks if t.status == "completed"]),
            "in_progress_tasks": len([t for t in cycle_tasks if t.status == "in_progress"]),
            "insights_generated": cycle.insights_generated,
            "prototypes_created": cycle.prototypes_created,
            "recommendations_count": cycle.recommendations_count
        }
    
    def get_innovation_metrics(self) -> Dict[str, Any]:
        """Get comprehensive innovation metrics"""
        return {
            **self.innovation_metrics,
            "active_agents": len([a for a in self.agents.values() if a.status == "available"]),
            "current_cycle_tasks": len([
                t for t in self.active_tasks.values()
                if t.innovation_cycle_id == self.current_cycle_id
            ]),
            "agent_specializations": {
                spec: len([a for a in self.agents.values() if a.specialization == spec])
                for spec in set(agent.specialization for agent in self.agents.values())
            }
        }

# Global R&D agent interface instance
rd_agents = RDAgentInterface()