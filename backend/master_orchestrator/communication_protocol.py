"""
Inter-Agent Communication Protocol - Real-time Agent Coordination

Advanced communication system enabling real-time coordination between all agents
across departments with message routing, event broadcasting, and synchronized execution.
"""

import asyncio
import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import hashlib

logger = logging.getLogger(__name__)

class MessageType(Enum):
    """Types of inter-agent messages"""
    REQUEST = "request"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    EVENT = "event"
    COMMAND = "command"
    SYNC = "sync"
    HEARTBEAT = "heartbeat"

class MessagePriority(Enum):
    """Message priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3
    CRITICAL = 4

@dataclass
class AgentMessage:
    """Inter-agent message structure"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    sender_department: str = ""
    recipient_id: Optional[str] = None  # None for broadcasts
    recipient_department: Optional[str] = None
    
    message_type: MessageType = MessageType.REQUEST
    priority: MessagePriority = MessagePriority.NORMAL
    
    subject: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    timestamp: datetime = field(default_factory=datetime.utcnow)
    expiry: Optional[datetime] = None
    requires_response: bool = False
    correlation_id: Optional[str] = None  # For request-response pairing
    
    # Delivery tracking
    delivered: bool = False
    acknowledged: bool = False
    response_received: bool = False
    delivery_attempts: int = 0

@dataclass
class CommunicationChannel:
    """Communication channel between agents/departments"""
    channel_id: str
    channel_type: str  # direct, department, broadcast
    participants: List[str]  # Agent or department IDs
    created_at: datetime = field(default_factory=datetime.utcnow)
    message_count: int = 0
    last_activity: Optional[datetime] = None
    is_active: bool = True

class CommunicationProtocol:
    """Inter-agent communication protocol system"""
    
    def __init__(self):
        self.protocol_id = "communication_protocol"
        
        # Message routing
        self.message_queue: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.priority_queue: Dict[MessagePriority, deque] = {
            priority: deque() for priority in MessagePriority
        }
        
        # Channels
        self.channels: Dict[str, CommunicationChannel] = {}
        self.agent_channels: Dict[str, List[str]] = defaultdict(list)  # agent_id -> channel_ids
        
        # Message tracking
        self.pending_messages: Dict[str, AgentMessage] = {}
        self.message_history: deque = deque(maxlen=10000)
        self.response_callbacks: Dict[str, Callable] = {}
        
        # Event system
        self.event_subscribers: Dict[str, List[str]] = defaultdict(list)  # event_type -> subscriber_ids
        self.event_handlers: Dict[str, Callable] = {}
        
        # Agent registry
        self.registered_agents: Dict[str, Dict[str, Any]] = {}
        self.agent_status: Dict[str, str] = {}  # agent_id -> status
        self.last_heartbeat: Dict[str, datetime] = {}
        
        # Protocol configuration
        self.max_retry_attempts = 3
        self.message_timeout_seconds = 300
        self.heartbeat_interval_seconds = 30
        self.channel_cleanup_interval = 3600
        
        # Metrics
        self.communication_metrics = {
            "total_messages_sent": 0,
            "total_messages_delivered": 0,
            "total_broadcasts": 0,
            "average_delivery_time": 0.0,
            "failed_deliveries": 0
        }
        
        # Initialize default channels
        self._initialize_default_channels()
        
        logger.info("Communication Protocol initialized")

    def _initialize_default_channels(self):
        """Initialize default communication channels"""
        
        # Department channels
        departments = ["frontend", "backend", "rnd", "growth"]
        for dept in departments:
            channel = CommunicationChannel(
                channel_id=f"channel_{dept}",
                channel_type="department",
                participants=[]
            )
            self.channels[channel.channel_id] = channel
        
        # Cross-department channel
        cross_dept_channel = CommunicationChannel(
            channel_id="channel_cross_department",
            channel_type="broadcast",
            participants=departments
        )
        self.channels[cross_dept_channel.channel_id] = cross_dept_channel
        
        # Emergency channel
        emergency_channel = CommunicationChannel(
            channel_id="channel_emergency",
            channel_type="broadcast",
            participants=[]
        )
        self.channels[emergency_channel.channel_id] = emergency_channel

    async def register_agent(self, agent_id: str, department: str, capabilities: List[str]) -> bool:
        """Register an agent with the communication system"""
        
        self.registered_agents[agent_id] = {
            "department": department,
            "capabilities": capabilities,
            "registered_at": datetime.utcnow(),
            "status": "online"
        }
        
        self.agent_status[agent_id] = "online"
        self.last_heartbeat[agent_id] = datetime.utcnow()
        
        # Add to department channel
        dept_channel_id = f"channel_{department}"
        if dept_channel_id in self.channels:
            channel = self.channels[dept_channel_id]
            if agent_id not in channel.participants:
                channel.participants.append(agent_id)
            
            if dept_channel_id not in self.agent_channels[agent_id]:
                self.agent_channels[agent_id].append(dept_channel_id)
        
        # Subscribe to default events
        await self.subscribe_to_event(agent_id, f"{department}_task")
        await self.subscribe_to_event(agent_id, "system_broadcast")
        
        logger.info(f"Agent {agent_id} registered with department {department}")
        
        return True

    async def send_message(self, message: AgentMessage) -> bool:
        """Send a message between agents"""
        
        # Validate message
        if not message.sender_id or not message.subject:
            logger.error("Invalid message: missing sender_id or subject")
            return False
        
        # Set expiry if not set
        if not message.expiry:
            message.expiry = datetime.utcnow() + timedelta(seconds=self.message_timeout_seconds)
        
        # Add to appropriate queue
        if message.message_type == MessageType.BROADCAST:
            await self._handle_broadcast(message)
        elif message.recipient_id:
            await self._route_direct_message(message)
        elif message.recipient_department:
            await self._route_department_message(message)
        else:
            logger.error(f"Cannot route message {message.message_id}: no recipient specified")
            return False
        
        # Track message
        self.pending_messages[message.message_id] = message
        self.message_history.append(message)
        
        # Add to priority queue
        self.priority_queue[message.priority].append(message.message_id)
        
        # Update metrics
        self.communication_metrics["total_messages_sent"] += 1
        
        logger.debug(f"Message {message.message_id} sent from {message.sender_id} to {message.recipient_id or 'broadcast'}")
        
        return True

    async def _route_direct_message(self, message: AgentMessage) -> None:
        """Route a direct message to specific agent"""
        
        if message.recipient_id not in self.registered_agents:
            logger.warning(f"Recipient {message.recipient_id} not registered")
            return
        
        # Check if recipient is online
        if self.agent_status.get(message.recipient_id) != "online":
            logger.warning(f"Recipient {message.recipient_id} is offline")
            # Queue for later delivery
            self.message_queue[message.recipient_id].append(message)
            return
        
        # Deliver message
        await self._deliver_message(message.recipient_id, message)

    async def _route_department_message(self, message: AgentMessage) -> None:
        """Route message to all agents in a department"""
        
        dept_channel_id = f"channel_{message.recipient_department}"
        
        if dept_channel_id not in self.channels:
            logger.error(f"Department channel {dept_channel_id} not found")
            return
        
        channel = self.channels[dept_channel_id]
        
        # Deliver to all participants in department
        for agent_id in channel.participants:
            if agent_id != message.sender_id:  # Don't send to self
                await self._deliver_message(agent_id, message)

    async def _handle_broadcast(self, message: AgentMessage) -> None:
        """Handle broadcast messages"""
        
        # Determine broadcast scope
        if message.metadata.get("scope") == "emergency":
            channel_id = "channel_emergency"
        else:
            channel_id = "channel_cross_department"
        
        if channel_id in self.channels:
            channel = self.channels[channel_id]
            
            # Broadcast to all online agents
            for agent_id in self.registered_agents:
                if agent_id != message.sender_id and self.agent_status.get(agent_id) == "online":
                    await self._deliver_message(agent_id, message)
        
        self.communication_metrics["total_broadcasts"] += 1

    async def _deliver_message(self, recipient_id: str, message: AgentMessage) -> bool:
        """Deliver message to recipient"""
        
        try:
            # Add to recipient's queue
            self.message_queue[recipient_id].append(message)
            
            # Mark as delivered
            message.delivered = True
            message.delivery_attempts += 1
            
            # Trigger handler if exists
            if recipient_id in self.event_handlers:
                handler = self.event_handlers[recipient_id]
                await handler(message)
            
            # Update metrics
            self.communication_metrics["total_messages_delivered"] += 1
            
            logger.debug(f"Message {message.message_id} delivered to {recipient_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to deliver message {message.message_id}: {e}")
            
            # Retry if attempts remaining
            if message.delivery_attempts < self.max_retry_attempts:
                await asyncio.sleep(1)  # Brief delay before retry
                return await self._deliver_message(recipient_id, message)
            else:
                self.communication_metrics["failed_deliveries"] += 1
                return False

    async def send_response(self, original_message: AgentMessage, response_content: Dict[str, Any]) -> bool:
        """Send a response to a message"""
        
        if not original_message.requires_response:
            logger.warning(f"Message {original_message.message_id} does not require response")
            return False
        
        response = AgentMessage(
            sender_id=original_message.recipient_id,
            sender_department=self.registered_agents.get(original_message.recipient_id, {}).get("department", ""),
            recipient_id=original_message.sender_id,
            recipient_department=original_message.sender_department,
            message_type=MessageType.RESPONSE,
            priority=original_message.priority,
            subject=f"Re: {original_message.subject}",
            content=response_content,
            correlation_id=original_message.message_id
        )
        
        # Mark original as responded
        original_message.response_received = True
        
        # Trigger callback if exists
        if original_message.message_id in self.response_callbacks:
            callback = self.response_callbacks[original_message.message_id]
            await callback(response)
            del self.response_callbacks[original_message.message_id]
        
        return await self.send_message(response)

    async def broadcast_event(self, event_type: str, event_data: Dict[str, Any], 
                            sender_id: str = "system") -> None:
        """Broadcast an event to all subscribers"""
        
        if event_type not in self.event_subscribers:
            logger.debug(f"No subscribers for event {event_type}")
            return
        
        event_message = AgentMessage(
            sender_id=sender_id,
            sender_department="system",
            message_type=MessageType.EVENT,
            priority=MessagePriority.HIGH,
            subject=f"Event: {event_type}",
            content=event_data,
            metadata={"event_type": event_type}
        )
        
        # Send to all subscribers
        for subscriber_id in self.event_subscribers[event_type]:
            event_message.recipient_id = subscriber_id
            await self.send_message(event_message)
        
        logger.info(f"Event {event_type} broadcast to {len(self.event_subscribers[event_type])} subscribers")

    async def subscribe_to_event(self, agent_id: str, event_type: str) -> bool:
        """Subscribe an agent to an event type"""
        
        if agent_id not in self.registered_agents:
            logger.error(f"Agent {agent_id} not registered")
            return False
        
        if agent_id not in self.event_subscribers[event_type]:
            self.event_subscribers[event_type].append(agent_id)
            logger.debug(f"Agent {agent_id} subscribed to event {event_type}")
        
        return True

    async def create_channel(self, channel_type: str, participants: List[str]) -> str:
        """Create a new communication channel"""
        
        channel_id = f"channel_{uuid.uuid4().hex[:8]}"
        
        channel = CommunicationChannel(
            channel_id=channel_id,
            channel_type=channel_type,
            participants=participants
        )
        
        self.channels[channel_id] = channel
        
        # Update agent channel mappings
        for agent_id in participants:
            if agent_id in self.registered_agents:
                self.agent_channels[agent_id].append(channel_id)
        
        logger.info(f"Created {channel_type} channel {channel_id} with {len(participants)} participants")
        
        return channel_id

    async def send_heartbeat(self, agent_id: str) -> None:
        """Send heartbeat from agent"""
        
        if agent_id not in self.registered_agents:
            return
        
        self.last_heartbeat[agent_id] = datetime.utcnow()
        self.agent_status[agent_id] = "online"
        
        # Process any queued messages
        if agent_id in self.message_queue:
            while self.message_queue[agent_id]:
                message = self.message_queue[agent_id].popleft()
                if message.expiry and message.expiry > datetime.utcnow():
                    await self._deliver_message(agent_id, message)

    async def check_agent_health(self) -> Dict[str, Any]:
        """Check health status of all agents"""
        
        current_time = datetime.utcnow()
        health_report = {
            "online": [],
            "offline": [],
            "unresponsive": []
        }
        
        for agent_id, last_heartbeat_time in self.last_heartbeat.items():
            time_since_heartbeat = (current_time - last_heartbeat_time).total_seconds()
            
            if time_since_heartbeat < self.heartbeat_interval_seconds * 2:
                health_report["online"].append(agent_id)
                self.agent_status[agent_id] = "online"
            elif time_since_heartbeat < self.heartbeat_interval_seconds * 5:
                health_report["unresponsive"].append(agent_id)
                self.agent_status[agent_id] = "unresponsive"
            else:
                health_report["offline"].append(agent_id)
                self.agent_status[agent_id] = "offline"
        
        return health_report

    async def synchronize_agents(self, agent_ids: List[str], sync_data: Dict[str, Any]) -> bool:
        """Synchronize state between multiple agents"""
        
        sync_message = AgentMessage(
            sender_id="system",
            sender_department="system",
            message_type=MessageType.SYNC,
            priority=MessagePriority.HIGH,
            subject="Agent Synchronization",
            content=sync_data,
            metadata={"sync_id": str(uuid.uuid4())}
        )
        
        # Send sync message to all specified agents
        success_count = 0
        for agent_id in agent_ids:
            if agent_id in self.registered_agents:
                sync_message.recipient_id = agent_id
                if await self.send_message(sync_message):
                    success_count += 1
        
        logger.info(f"Synchronized {success_count}/{len(agent_ids)} agents")
        
        return success_count == len(agent_ids)

    def get_agent_messages(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent messages for an agent"""
        
        if agent_id not in self.message_queue:
            return []
        
        messages = list(self.message_queue[agent_id])[-limit:]
        
        return [
            {
                "message_id": msg.message_id,
                "sender": msg.sender_id,
                "subject": msg.subject,
                "type": msg.message_type.value,
                "priority": msg.priority.value,
                "timestamp": msg.timestamp.isoformat(),
                "content": msg.content
            }
            for msg in messages
        ]

    def get_protocol_status(self) -> Dict[str, Any]:
        """Get communication protocol status"""
        
        return {
            "protocol_id": self.protocol_id,
            "registered_agents": len(self.registered_agents),
            "active_channels": len([c for c in self.channels.values() if c.is_active]),
            "pending_messages": len(self.pending_messages),
            "agent_status_summary": {
                "online": len([a for a in self.agent_status.values() if a == "online"]),
                "offline": len([a for a in self.agent_status.values() if a == "offline"]),
                "unresponsive": len([a for a in self.agent_status.values() if a == "unresponsive"])
            },
            "event_subscriptions": {event: len(subs) for event, subs in self.event_subscribers.items()},
            "metrics": self.communication_metrics
        }

    async def cleanup_expired_messages(self) -> int:
        """Clean up expired messages"""
        
        current_time = datetime.utcnow()
        expired_count = 0
        
        # Clean up pending messages
        expired_ids = [
            msg_id for msg_id, msg in self.pending_messages.items()
            if msg.expiry and msg.expiry < current_time
        ]
        
        for msg_id in expired_ids:
            del self.pending_messages[msg_id]
            expired_count += 1
        
        # Clean up from queues
        for agent_id in list(self.message_queue.keys()):
            cleaned_queue = deque([
                msg for msg in self.message_queue[agent_id]
                if not msg.expiry or msg.expiry >= current_time
            ])
            
            expired_count += len(self.message_queue[agent_id]) - len(cleaned_queue)
            self.message_queue[agent_id] = cleaned_queue
        
        logger.info(f"Cleaned up {expired_count} expired messages")
        
        return expired_count

    async def start_maintenance_loop(self) -> None:
        """Start background maintenance loop"""
        
        while True:
            try:
                # Check agent health
                await self.check_agent_health()
                
                # Clean up expired messages
                await self.cleanup_expired_messages()
                
                # Process priority queue
                await self._process_priority_queue()
                
                await asyncio.sleep(30)  # Run every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in maintenance loop: {e}")
                await asyncio.sleep(60)

    async def _process_priority_queue(self) -> None:
        """Process messages by priority"""
        
        # Process from highest to lowest priority
        for priority in reversed(list(MessagePriority)):
            queue = self.priority_queue[priority]
            
            while queue:
                message_id = queue.popleft()
                
                if message_id in self.pending_messages:
                    message = self.pending_messages[message_id]
                    
                    # Re-attempt delivery if not delivered
                    if not message.delivered and message.recipient_id:
                        await self._deliver_message(message.recipient_id, message)

# Global communication protocol instance
communication_protocol = CommunicationProtocol()