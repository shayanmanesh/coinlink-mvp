#!/usr/bin/env python3
"""
OPUS-4 SWARM COORDINATOR
Real-time monitoring and coordination for parallel Claude agents
"""

import os
import json
import time
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import asyncio
from dataclasses import dataclass, asdict

@dataclass
class AgentStatus:
    id: str
    role: str
    status: str  # spawned, running, complete, failed
    started_at: str
    completed_at: Optional[str] = None
    output_summary: Optional[str] = None
    files_modified: List[str] = None
    
    def __post_init__(self):
        if self.files_modified is None:
            self.files_modified = []

class SwarmCoordinator:
    def __init__(self, project_root: str = "/Users/shayanbozorgmanesh/Documents/Parking/coinlink-mvp"):
        self.project_root = Path(project_root)
        self.swarm_state = self.project_root / "swarm-state"
        self.logs_dir = self.project_root / "swarm-logs"
        self.agents: Dict[str, AgentStatus] = {}
        
        # Ensure directories exist
        self.swarm_state.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        # State file for persistence
        self.state_file = self.swarm_state / "coordinator-state.json"
    
    def launch_agent(self, agent_id: str, role: str, task: str) -> bool:
        """Launch a single agent with specific task"""
        prompt_file = self.swarm_state / f"{agent_id}.prompt"
        
        # Write prompt file
        prompt_content = f"""You are {agent_id}, specialized in {role}.

PROJECT: Coinlink-MVP Production Deployment
TARGET: www.coin.link
TIMELINE: Complete ASAP

YOUR TASK:
{task}

COORDINATION:
- Write status updates to: {self.swarm_state}/{agent_id}.status
- Write completion summary to: {self.swarm_state}/{agent_id}.complete
- Log modified files to: {self.swarm_state}/{agent_id}.files

Be concise, be fast, be precise.
"""
        prompt_file.write_text(prompt_content)
        
        # Launch in tmux
        cmd = f"""tmux new-session -d -s "{agent_id}" -c "{self.project_root}" \
                 'claude < "{prompt_file}" 2>&1 | tee "{self.logs_dir}/{agent_id}.log"'"""
        
        try:
            subprocess.run(cmd, shell=True, check=True)
            self.agents[agent_id] = AgentStatus(
                id=agent_id,
                role=role,
                status="spawned",
                started_at=datetime.now().isoformat()
            )
            self.save_state()
            return True
        except subprocess.CalledProcessError:
            return False
    
    def check_agent_status(self, agent_id: str) -> str:
        """Check if agent is still running"""
        try:
            result = subprocess.run(
                f"tmux has-session -t {agent_id} 2>/dev/null",
                shell=True,
                capture_output=True
            )
            
            if result.returncode == 0:
                # Check if complete file exists
                complete_file = self.swarm_state / f"{agent_id}.complete"
                if complete_file.exists():
                    return "complete"
                return "running"
            else:
                return "terminated"
        except:
            return "unknown"
    
    def update_all_statuses(self):
        """Update status for all agents"""
        for agent_id, agent in self.agents.items():
            current_status = self.check_agent_status(agent_id)
            
            if current_status != agent.status:
                agent.status = current_status
                
                if current_status == "complete":
                    agent.completed_at = datetime.now().isoformat()
                    
                    # Read completion summary if available
                    complete_file = self.swarm_state / f"{agent_id}.complete"
                    if complete_file.exists():
                        agent.output_summary = complete_file.read_text().strip()
                    
                    # Read modified files if tracked
                    files_file = self.swarm_state / f"{agent_id}.files"
                    if files_file.exists():
                        agent.files_modified = files_file.read_text().strip().split('\n')
        
        self.save_state()
    
    def save_state(self):
        """Save current state to JSON"""
        state = {
            "last_updated": datetime.now().isoformat(),
            "agents": {
                agent_id: asdict(agent) 
                for agent_id, agent in self.agents.items()
            }
        }
        self.state_file.write_text(json.dumps(state, indent=2))
    
    def load_state(self):
        """Load state from JSON"""
        if self.state_file.exists():
            state = json.loads(self.state_file.read_text())
            for agent_id, agent_data in state.get("agents", {}).items():
                self.agents[agent_id] = AgentStatus(**agent_data)
    
    def get_summary(self) -> Dict:
        """Get swarm summary statistics"""
        self.update_all_statuses()
        
        total = len(self.agents)
        complete = sum(1 for a in self.agents.values() if a.status == "complete")
        running = sum(1 for a in self.agents.values() if a.status == "running")
        failed = sum(1 for a in self.agents.values() if a.status in ["failed", "terminated"])
        
        return {
            "total_agents": total,
            "complete": complete,
            "running": running,
            "failed": failed,
            "progress_percent": (complete / total * 100) if total > 0 else 0,
            "agents": self.agents
        }
    
    def monitor(self, interval: int = 5):
        """Monitor swarm progress"""
        print("🚀 SWARM MONITOR ACTIVE")
        print("=" * 50)
        
        try:
            while True:
                os.system('clear')
                summary = self.get_summary()
                
                print(f"📊 SWARM STATUS - {datetime.now().strftime('%H:%M:%S')}")
                print("=" * 50)
                print(f"Progress: {summary['progress_percent']:.1f}% [{summary['complete']}/{summary['total_agents']}]")
                print(f"Running: {summary['running']} | Complete: {summary['complete']} | Failed: {summary['failed']}")
                print("\n📋 AGENTS:")
                print("-" * 50)
                
                for agent_id, agent in summary['agents'].items():
                    status_icon = {
                        "complete": "✅",
                        "running": "⚡",
                        "spawned": "🔄",
                        "failed": "❌",
                        "terminated": "⛔"
                    }.get(agent.status, "❓")
                    
                    print(f"{status_icon} {agent.id:<20} [{agent.role:<25}] {agent.status.upper()}")
                    
                    if agent.output_summary and len(agent.output_summary) > 0:
                        summary_preview = agent.output_summary[:60] + "..." if len(agent.output_summary) > 60 else agent.output_summary
                        print(f"   └─ {summary_preview}")
                
                print("\n" + "=" * 50)
                print("Press Ctrl+C to exit monitor")
                
                if summary['complete'] == summary['total_agents']:
                    print("\n🎉 ALL AGENTS COMPLETE!")
                    break
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Monitor stopped")
    
    def kill_all(self):
        """Terminate all agents"""
        for agent_id in self.agents.keys():
            subprocess.run(f"tmux kill-session -t {agent_id} 2>/dev/null", shell=True)
        print(f"🛑 Terminated {len(self.agents)} agents")

def main():
    import sys
    
    coordinator = SwarmCoordinator()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "monitor":
            coordinator.load_state()
            coordinator.monitor()
        
        elif command == "status":
            coordinator.load_state()
            summary = coordinator.get_summary()
            print(json.dumps(summary, indent=2))
        
        elif command == "kill":
            coordinator.load_state()
            coordinator.kill_all()
        
        else:
            print(f"Unknown command: {command}")
            print("Usage: swarm-coordinator.py [monitor|status|kill]")
    else:
        print("Swarm Coordinator Ready")
        print("Commands:")
        print("  monitor - Live monitoring dashboard")
        print("  status  - JSON status output")
        print("  kill    - Terminate all agents")

if __name__ == "__main__":
    main()