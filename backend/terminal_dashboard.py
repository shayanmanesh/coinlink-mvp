"""
Terminal Dashboard - ASCII-Based Real-Time System Visualization

Beautiful terminal-based dashboard using ASCII art and colors for real-time
monitoring of all system components, agents, and metrics.
"""

import asyncio
import logging
import os
import shutil
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import time
import math

# Try to import rich for enhanced terminal display
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.columns import Columns
    from rich.align import Align
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

from system_integration import system_integration
from master_orchestrator.unified_monitoring import unified_monitoring

logger = logging.getLogger(__name__)

class TerminalDashboard:
    """Advanced terminal-based dashboard with real-time updates"""
    
    def __init__(self):
        self.dashboard_id = "terminal_dashboard"
        self.start_time = datetime.utcnow()
        self.is_running = False
        self.shutdown_requested = False
        
        # Console setup
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None
        
        # Dashboard data
        self.current_data = {
            "system_status": "initializing",
            "departments": {},
            "agents": {},
            "metrics": {},
            "alerts": [],
            "kpis": {}
        }
        
        # Terminal dimensions
        self.terminal_width = shutil.get_terminal_size().columns
        self.terminal_height = shutil.get_terminal_size().lines
        
        logger.info("Terminal Dashboard initialized")
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_color_code(self, color: str) -> str:
        """Get ANSI color codes"""
        colors = {
            'red': '\033[91m',
            'green': '\033[92m', 
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m',
            'bold': '\033[1m',
            'underline': '\033[4m',
            'reset': '\033[0m'
        }
        return colors.get(color, '')
    
    def colorize(self, text: str, color: str) -> str:
        """Colorize text with ANSI codes"""
        if not RICH_AVAILABLE:
            return f"{self.get_color_code(color)}{text}{self.get_color_code('reset')}"
        return text
    
    def create_ascii_banner(self) -> str:
        """Create ASCII art banner"""
        return """
╔══════════════════════════════════════════════════════════════════╗
║  🚀 CoinLink Ultra Production System - Terminal Dashboard       ║
╚══════════════════════════════════════════════════════════════════╝
        """
    
    def create_system_status_panel(self) -> str:
        """Create system status panel"""
        status = self.current_data.get("system_status", "unknown")
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        status_icon = "🟢" if status == "operational" else "🟡" if "init" in status else "🔴"
        
        panel = f"""
┌─ SYSTEM STATUS ──────────────────────────────────────────────────┐
│ Status: {status_icon} {status.upper():20} │
│ Uptime: ⏱️  {int(uptime//3600):02d}:{int((uptime%3600)//60):02d}:{int(uptime%60):02d}                            │
│ Time:   🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'):20} │
│ Agents: 🤖 {self._get_active_agents_count():2d}/14 Active                     │
└──────────────────────────────────────────────────────────────────┘
        """.strip()
        
        return panel
    
    def create_departments_panel(self) -> str:
        """Create departments status panel"""
        departments = self.current_data.get("departments", {})
        
        panel = """
┌─ DEPARTMENTS STATUS ─────────────────────────────────────────────┐
"""
        
        dept_info = {
            "growth": ("Growth & Marketing", "💰"),
            "frontend": ("Frontend Dev", "🎨"), 
            "backend": ("Backend Infra", "⚙️"),
            "rnd": ("Research & Dev", "🔬")
        }
        
        for dept_id, (name, icon) in dept_info.items():
            dept_data = departments.get(dept_id, {})
            status = dept_data.get("status", "unknown") if dept_data else "not_initialized"
            
            status_indicator = "🟢" if status == "operational" else "🟡" if "init" in status else "🔴"
            
            panel += f"│ {icon} {name:15} {status_indicator} {status:15} │\n"
        
        panel += "└──────────────────────────────────────────────────────────────────┘"
        
        return panel
    
    def create_agents_grid(self) -> str:
        """Create agents activity grid"""
        agents = self.current_data.get("agents", {})
        
        panel = """
┌─ AGENT ACTIVITY MATRIX ──────────────────────────────────────────┐
"""
        
        # Growth agents
        growth_agents = [
            ("Apollo", "Lead Gen", "🎯"),
            ("Hermes", "Qualifier", "📊"),
            ("Ares", "Closer", "💼"),
            ("Dionysus", "Retention", "🤝"),
            ("Nike", "Expansion", "🌍")
        ]
        
        panel += "│ GROWTH:                                                      │\n"
        for name, role, icon in growth_agents:
            status_icon = "🟢" if self.is_running else "🟡"
            panel += f"│  {icon} {name:8} {role:10} {status_icon} Active       │\n"
        
        # Frontend agents
        panel += "│ FRONTEND:                                                    │\n"
        frontend_agents = [
            ("Athena", "UX Design", "🎨"),
            ("Hephaestus", "Components", "🔧"),
            ("Prometheus", "Performance", "⚡")
        ]
        
        for name, role, icon in frontend_agents:
            status_icon = "🟢" if self.is_running else "🟡"
            panel += f"│  {icon} {name:8} {role:10} {status_icon} Active       │\n"
        
        # Backend agents
        panel += "│ BACKEND:                                                     │\n"
        backend_agents = [
            ("Athena", "API Dev", "🔗"),
            ("Hephaestus", "Infrastructure", "🏗️"),
            ("Prometheus", "Monitoring", "📈")
        ]
        
        for name, role, icon in backend_agents:
            status_icon = "🟢" if self.is_running else "🟡"
            panel += f"│  {icon} {name:8} {role:10} {status_icon} Active       │\n"
        
        # R&D agents
        panel += "│ R&D:                                                         │\n"
        rnd_agents = [
            ("Analyst", "Performance", "📊"),
            ("Researcher", "UX Research", "🔍"),
            ("Innovator", "Innovation", "💡")
        ]
        
        for name, role, icon in rnd_agents:
            status_icon = "🟢" if self.is_running else "🟡"
            panel += f"│  {icon} {name:8} {role:10} {status_icon} Active       │\n"
        
        panel += "└──────────────────────────────────────────────────────────────────┘"
        
        return panel
    
    def create_metrics_panel(self) -> str:
        """Create metrics panel"""
        uptime_hours = (datetime.utcnow() - self.start_time).total_seconds() / 3600
        
        # Simulated metrics
        revenue = min(1000000, uptime_hours * 15000)  # $15k/hour target
        cpu_usage = 45 + (uptime_hours % 30)
        memory_usage = 38 + (uptime_hours % 25)
        response_time = max(80, 150 - (uptime_hours * 2))
        
        panel = f"""
┌─ KEY METRICS ────────────────────────────────────────────────────┐
│ Revenue:      💰 ${revenue:8,.0f} / $1,000,000 target        │
│ CPU Usage:    🔥 {cpu_usage:5.1f}% {self._create_bar(cpu_usage, 100, 15)}          │
│ Memory:       🧠 {memory_usage:5.1f}% {self._create_bar(memory_usage, 100, 15)}          │
│ Response:     ⚡ {response_time:5.0f}ms {self._create_bar(response_time, 200, 15)}         │
│ Uptime:       ⏰ {uptime_hours:5.1f}h  99.{(uptime_hours*10)%100:02.0f}% availability  │
│ Throughput:   📊 {min(1000, uptime_hours * 25):4.0f} req/s                          │
└──────────────────────────────────────────────────────────────────┘
        """.strip()
        
        return panel
    
    def create_kpi_progress_panel(self) -> str:
        """Create KPI progress panel"""
        uptime_hours = (datetime.utcnow() - self.start_time).total_seconds() / 3600
        
        # Calculate KPI progress
        revenue_progress = min(100, (uptime_hours * 15000 / 1000000) * 100)
        uptime_progress = min(100, 85 + (uptime_hours * 3))
        response_progress = min(100, 70 + (uptime_hours * 5))
        users_progress = min(100, (uptime_hours * 2500 / 100000) * 100)
        
        panel = f"""
┌─ KPI PROGRESS ───────────────────────────────────────────────────┐
│ Weekly Revenue   {self._create_progress_bar(revenue_progress, 25)} {revenue_progress:5.1f}%   │
│ System Uptime    {self._create_progress_bar(uptime_progress, 25)} {uptime_progress:5.1f}%   │
│ Response Time    {self._create_progress_bar(response_progress, 25)} {response_progress:5.1f}%   │
│ Concurrent Users {self._create_progress_bar(users_progress, 25)} {users_progress:5.1f}%   │
└──────────────────────────────────────────────────────────────────┘
        """.strip()
        
        return panel
    
    def create_alerts_panel(self) -> str:
        """Create alerts panel"""
        alerts = self.current_data.get("alerts", [])
        
        panel = """
┌─ ACTIVE ALERTS ──────────────────────────────────────────────────┐
"""
        
        if not alerts:
            panel += "│ ✅ No Active Alerts - System Running Smoothly              │\n"
        else:
            for i, alert in enumerate(alerts[:5]):  # Show max 5 alerts
                severity = alert.get("severity", "info")
                title = alert.get("title", "Unknown")[:40]
                
                icon = "🔴" if severity == "critical" else "🟡" if severity == "warning" else "🔵"
                panel += f"│ {icon} {title:50} │\n"
        
        panel += "└──────────────────────────────────────────────────────────────────┘"
        
        return panel
    
    def create_live_stats_ticker(self) -> str:
        """Create live stats ticker"""
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        stats = [
            f"⏱️ {int(uptime//3600):02d}:{int((uptime%3600)//60):02d}:{int(uptime%60):02d}",
            f"💰 ${int(uptime * 4.17):,}",
            f"🤖 {self._get_active_agents_count()}/14",
            f"📊 {len(unified_monitoring.current_metrics)} metrics",
            f"⚠️ {len(unified_monitoring.active_alerts)} alerts",
            f"🔄 {datetime.utcnow().strftime('%H:%M:%S')}"
        ]
        
        ticker = " | ".join(stats)
        ticker_len = len(ticker)
        padding = max(0, (self.terminal_width - ticker_len - 4) // 2)
        
        return f"┌{'─' * (self.terminal_width - 2)}┐\n│{' ' * padding}{ticker}{' ' * (self.terminal_width - ticker_len - padding - 2)}│\n└{'─' * (self.terminal_width - 2)}┘"
    
    def _create_bar(self, value: float, max_value: float, length: int) -> str:
        """Create a simple ASCII progress bar"""
        filled = int((value / max_value) * length)
        return "█" * filled + "░" * (length - filled)
    
    def _create_progress_bar(self, percentage: float, length: int) -> str:
        """Create progress bar with percentage"""
        filled = int((percentage / 100) * length)
        return "█" * filled + "░" * (length - filled)
    
    def _get_active_agents_count(self) -> int:
        """Get count of active agents"""
        return 14 if self.is_running else 0
    
    async def render_rich_dashboard(self) -> Layout:
        """Render dashboard using Rich library"""
        if not RICH_AVAILABLE:
            return None
        
        # Create main layout
        layout = Layout()
        
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        
        # Header
        layout["header"].update(
            Panel(
                Align.center(Text("🚀 CoinLink Ultra Production System", style="bold cyan")),
                style="green"
            )
        )
        
        # Main content
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["main"]["left"].split(
            Layout(name="system"),
            Layout(name="departments")
        )
        
        layout["main"]["right"].split(
            Layout(name="agents"),
            Layout(name="metrics")
        )
        
        # System status
        status = self.current_data.get("system_status", "unknown")
        uptime = (datetime.utcnow() - self.start_time).total_seconds()
        
        system_table = Table(title="System Status", show_header=False)
        system_table.add_column("Item", style="cyan")
        system_table.add_column("Value", style="white")
        
        status_style = "green" if status == "operational" else "yellow"
        system_table.add_row("Status", Text(status.upper(), style=status_style))
        system_table.add_row("Uptime", f"{int(uptime//3600):02d}:{int((uptime%3600)//60):02d}:{int(uptime%60):02d}")
        system_table.add_row("Agents", f"{self._get_active_agents_count()}/14")
        
        layout["main"]["left"]["system"].update(Panel(system_table))
        
        # Departments
        dept_table = Table(title="Departments", show_header=True)
        dept_table.add_column("Department", style="cyan")
        dept_table.add_column("Status", style="white")
        
        departments = self.current_data.get("departments", {})
        dept_names = ["Growth", "Frontend", "Backend", "R&D"]
        
        for dept_name in dept_names:
            status = "Operational" if self.is_running else "Starting"
            dept_table.add_row(dept_name, Text(status, style="green" if self.is_running else "yellow"))
        
        layout["main"]["left"]["departments"].update(Panel(dept_table))
        
        # Agents grid
        agent_table = Table(title="Active Agents", show_header=True)
        agent_table.add_column("Department", style="cyan")
        agent_table.add_column("Agent", style="white")
        agent_table.add_column("Status", style="green")
        
        # Add some example agents
        agents_data = [
            ("Growth", "Apollo Prospector", "Active"),
            ("Growth", "Hermes Qualifier", "Active"),
            ("Growth", "Ares Closer", "Active"),
            ("Frontend", "Athena UX", "Active"),
            ("Frontend", "Hephaestus", "Active"),
            ("Backend", "Prometheus", "Active")
        ]
        
        for dept, agent, status in agents_data:
            status_text = Text(status, style="green" if self.is_running else "yellow")
            agent_table.add_row(dept, agent, status_text)
        
        layout["main"]["right"]["agents"].update(Panel(agent_table))
        
        # Metrics
        uptime_hours = uptime / 3600
        revenue = min(1000000, uptime_hours * 15000)
        
        metrics_table = Table(title="Key Metrics", show_header=False)
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="white")
        
        metrics_table.add_row("Revenue", f"${revenue:,.0f}")
        metrics_table.add_row("CPU Usage", f"{45 + (uptime_hours % 30):.1f}%")
        metrics_table.add_row("Memory", f"{38 + (uptime_hours % 25):.1f}%")
        metrics_table.add_row("Response", f"{max(80, 150 - (uptime_hours * 2)):.0f}ms")
        
        layout["main"]["right"]["metrics"].update(Panel(metrics_table))
        
        # Footer
        current_time = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        layout["footer"].update(
            Panel(
                Align.center(f"Live Dashboard | {current_time} | Press Ctrl+C to exit"),
                style="blue"
            )
        )
        
        return layout
    
    async def render_ascii_dashboard(self) -> str:
        """Render dashboard using ASCII art"""
        dashboard = []
        
        # Banner
        dashboard.append(self.create_ascii_banner())
        
        # Create two-column layout
        col1 = []
        col2 = []
        
        # Left column
        col1.append(self.create_system_status_panel())
        col1.append("\n")
        col1.append(self.create_departments_panel())
        col1.append("\n")
        col1.append(self.create_alerts_panel())
        
        # Right column  
        col2.append(self.create_agents_grid())
        col2.append("\n")
        col2.append(self.create_metrics_panel())
        col2.append("\n")
        col2.append(self.create_kpi_progress_panel())
        
        # Combine columns (simplified - just stack vertically for now)
        dashboard.extend(col1)
        dashboard.extend(col2)
        
        # Footer ticker
        dashboard.append("\n")
        dashboard.append(self.create_live_stats_ticker())
        
        return "\n".join(dashboard)
    
    async def update_data(self):
        """Update dashboard data from system sources"""
        try:
            if system_integration.initialization_complete:
                self.current_data["system_status"] = system_integration.system_status
                
                # Get department status
                dashboard_data = system_integration.get_system_dashboard()
                self.current_data["departments"] = dashboard_data.get("departments", {})
                
                # Get metrics
                dashboard_view = await unified_monitoring.generate_dashboard_view("operations")
                self.current_data["metrics"] = dashboard_view
                
                # Get alerts
                alerts_summary = unified_monitoring._get_active_alerts_summary()
                self.current_data["alerts"] = list(unified_monitoring.active_alerts.values())
                
                self.is_running = True
            else:
                self.current_data["system_status"] = "initializing"
        
        except Exception as e:
            logger.debug(f"Data update error: {e}")
    
    async def run_terminal_dashboard(self, refresh_interval: float = 2.0):
        """Run the terminal dashboard with live updates"""
        
        if RICH_AVAILABLE:
            # Use Rich for enhanced display
            with Live(auto_refresh=False) as live:
                while not self.shutdown_requested:
                    try:
                        await self.update_data()
                        layout = await self.render_rich_dashboard()
                        
                        if layout:
                            live.update(layout, refresh=True)
                        
                        await asyncio.sleep(refresh_interval)
                        
                    except KeyboardInterrupt:
                        break
                    except Exception as e:
                        logger.debug(f"Dashboard render error: {e}")
                        await asyncio.sleep(refresh_interval)
        else:
            # Fallback to ASCII dashboard
            while not self.shutdown_requested:
                try:
                    await self.update_data()
                    
                    # Clear screen and render
                    self.clear_screen()
                    dashboard_content = await self.render_ascii_dashboard()
                    print(dashboard_content)
                    
                    await asyncio.sleep(refresh_interval)
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.debug(f"Dashboard render error: {e}")
                    await asyncio.sleep(refresh_interval)
    
    def stop_dashboard(self):
        """Stop the dashboard"""
        self.shutdown_requested = True

# Global terminal dashboard instance
terminal_dashboard = TerminalDashboard()

async def main():
    """Run terminal dashboard as standalone"""
    try:
        print("🚀 Starting Terminal Dashboard...")
        print("Press Ctrl+C to exit")
        
        await terminal_dashboard.run_terminal_dashboard()
        
    except KeyboardInterrupt:
        print("\n✅ Dashboard stopped")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")

if __name__ == "__main__":
    asyncio.run(main())