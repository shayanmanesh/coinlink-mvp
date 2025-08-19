# 📡 COINLINK API DOCUMENTATION

*Generated: August 19, 2025 - Version 2.0.0-ultra*

## 🎯 API OVERVIEW

The CoinLink API provides comprehensive access to the multi-agent orchestration system, offering real-time monitoring, agent control, and system metrics through RESTful endpoints and WebSocket connections.

**Base URLs:**
- **Production**: `https://coinlink-backend.onrender.com`
- **Development**: `http://localhost:8000`
- **Dashboard**: `http://localhost:8080`
- **Monitoring API**: `http://localhost:8081`

---

## 🔍 CORE ENDPOINTS

### 1. System Health & Status

#### `GET /health`
**Description**: Primary health check endpoint  
**Response Time**: <200ms  
**Authentication**: None required

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-19T09:43:15.920Z",
  "version": "2.0.0-ultra",
  "uptime_seconds": 3600,
  "system": {
    "cpu_usage": 24.5,
    "memory_usage": 68.2,
    "active_agents": 14,
    "response_time_ms": 85
  }
}
```

#### `GET /api/system/status`
**Description**: Comprehensive system status  
**Authentication**: None required

**Response:**
```json
{
  "system": {
    "name": "CoinLink Ultra Production System",
    "version": "2.0.0-ultra", 
    "status": "operational",
    "uptime_hours": 0.18843379583333333,
    "initialization_complete": true
  },
  "departments": {
    "growth": {
      "total_growth_agents": 5,
      "bd_agents": 5,
      "marketing_agents": 5,
      "active_tasks": 12,
      "completed_tasks": 847,
      "system_performance": {
        "overall_success_rate": 94.2
      }
    },
    "frontend": {
      "status": "operational",
      "active_components": 3,
      "performance_score": 91.5
    },
    "backend": {
      "status": "operational", 
      "active_services": 3,
      "optimization_score": 88.7
    },
    "rnd": {
      "status": "operational",
      "active_research": 3,
      "innovation_score": 92.3
    }
  }
}
```

---

## 🤖 AGENT MANAGEMENT

### 2. Agent Status & Control

#### `GET /api/agents/activity`
**Description**: Real-time agent activity matrix  
**Authentication**: None required

**Response:**
```json
{
  "agents": {
    "growth": {
      "apollo_prospector": {
        "status": "active",
        "productivity": 95.2,
        "last_action": "Lead Generation",
        "tasks_completed": 42,
        "uptime": "07:23:15"
      },
      "hermes_qualifier": {
        "status": "active",
        "productivity": 87.5,
        "last_action": "Lead Qualification",
        "tasks_completed": 38,
        "uptime": "07:23:15"
      }
    },
    "frontend": {
      "athena_ux": {
        "status": "active",
        "productivity": 88.3,
        "last_action": "UI Optimization"
      }
    },
    "backend": {
      "athena_api": {
        "status": "active",
        "productivity": 94.7,
        "last_action": "API Optimization"
      }
    },
    "rnd": {
      "performance_analyst": {
        "status": "active", 
        "productivity": 86.4,
        "last_action": "Performance Analysis"
      }
    }
  }
}
```

#### `GET /api/departments/status`
**Description**: Department-level status overview  
**Authentication**: None required

**Response:**
```json
{
  "growth": {
    "status": "operational",
    "agents_active": 5,
    "performance_score": 91.8
  },
  "frontend": {
    "status": "operational",
    "agents_active": 3,
    "performance_score": 90.2
  },
  "backend": {
    "status": "operational",
    "agents_active": 3,
    "performance_score": 92.1
  },
  "rnd": {
    "status": "operational",
    "agents_active": 3,
    "performance_score": 88.9
  }
}
```

---

## 📊 METRICS & KPI TRACKING

### 3. Performance Metrics

#### `GET /api/kpis/progress`
**Description**: Real-time KPI achievement tracking  
**Authentication**: None required

**Response:**
```json
{
  "kpis": {
    "weekly_revenue": {
      "current": 156750,
      "target": 1000000,
      "progress": 15.675,
      "rate_per_second": 4.17
    },
    "system_uptime": {
      "current": 99.87,
      "target": 99.99,
      "progress": 99.88
    },
    "response_time": {
      "current": 85,
      "target": 100,
      "progress": 85.0,
      "unit": "ms"
    },
    "concurrent_users": {
      "current": 2847,
      "target": 50000,
      "progress": 5.694
    }
  }
}
```

#### `GET /api/metrics/live`
**Description**: Live system metrics  
**Authentication**: None required

**Response:**
```json
{
  "timestamp": "2025-08-19T09:43:15.920Z",
  "system_metrics": {
    "cpu_usage": 24.5,
    "memory_usage": 68.2,
    "network_io": {
      "bytes_in": 1247856,
      "bytes_out": 2847291
    },
    "response_times": {
      "avg": 85,
      "p95": 145,
      "p99": 298
    }
  },
  "agent_metrics": {
    "total_active": 14,
    "avg_productivity": 91.2,
    "tasks_per_second": 2.3
  }
}
```

---

## ⚠️ ALERTS & MONITORING

### 4. Alert Management

#### `GET /api/alerts/active`
**Description**: Current active alerts  
**Authentication**: None required

**Response:**
```json
{
  "total": 2,
  "unacknowledged": 1,
  "alerts": [
    {
      "id": "alert_001",
      "severity": "warning",
      "title": "System Response Time",
      "message": "Response time at 60.8% of target threshold",
      "timestamp": "2025-08-19T09:38:15.920Z",
      "acknowledged": false
    },
    {
      "id": "alert_002", 
      "severity": "info",
      "title": "Revenue Milestone",
      "message": "Weekly revenue at 75.0% of target",
      "timestamp": "2025-08-19T09:35:22.445Z", 
      "acknowledged": true
    }
  ]
}
```

#### `GET /api/alerts/history`
**Description**: Historical alert data  
**Parameters**: `?limit=50&offset=0`

---

## 🔄 REAL-TIME COMMUNICATION

### 5. WebSocket Endpoints

#### `WS /ws/live-data`
**Description**: Real-time system data streaming  
**Authentication**: None required

**Message Format:**
```json
{
  "timestamp": "2025-08-19T09:43:15.920Z",
  "system_status": {
    "cpu": 24.5,
    "memory": 68.2,
    "response_time": 85,
    "uptime": 0.188,
    "revenue": 156750
  },
  "metrics": {
    "agents_active": 14,
    "tasks_completed": 2847,
    "alerts_active": 2
  },
  "alerts": {
    "total": 2,
    "unacknowledged": 1
  }
}
```

**Update Frequency**: Every 2 seconds

---

## 🏢 DEPARTMENT-SPECIFIC ENDPOINTS

### 6. Growth Department

#### `GET /api/growth/agents`
**Description**: Growth department agent status

#### `GET /api/growth/metrics`  
**Description**: Growth-specific KPIs

#### `POST /api/growth/campaign`
**Description**: Launch new growth campaign  
**Authentication**: Required

### 7. R&D Department

#### `GET /api/rd/status`
**Description**: R&D department status

#### `GET /api/rd/innovations`
**Description**: Current innovation pipeline

---

## 🔐 AUTHENTICATION

### JWT Authentication
Most write operations require JWT authentication:

```http
Authorization: Bearer <jwt_token>
```

**Token Endpoint**: `POST /api/auth/token`

**Request:**
```json
{
  "username": "admin",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 📝 REQUEST/RESPONSE FORMATS

### Standard Response Structure
```json
{
  "success": true,
  "data": { /* response data */ },
  "timestamp": "2025-08-19T09:43:15.920Z",
  "version": "2.0.0-ultra"
}
```

### Error Response Structure
```json
{
  "success": false,
  "error": {
    "code": "AGENT_UNAVAILABLE",
    "message": "Agent athena_ux is currently unavailable",
    "details": "Agent is in maintenance mode"
  },
  "timestamp": "2025-08-19T09:43:15.920Z"
}
```

---

## 🚀 RATE LIMITING

- **General Endpoints**: 1000 requests/hour
- **Real-time Metrics**: 300 requests/minute  
- **WebSocket Connections**: 10 concurrent per IP
- **Authentication**: 5 attempts/minute

---

## 📚 SDK & EXAMPLES

### Python SDK Example
```python
import asyncio
import aiohttp

class CoinLinkAPI:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    async def get_system_status(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/system/status") as resp:
                return await resp.json()

# Usage
api = CoinLinkAPI()
status = await api.get_system_status()
```

### JavaScript/Node.js Example
```javascript
const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:8080/ws/live-data');

ws.on('message', function(data) {
    const metrics = JSON.parse(data);
    console.log('Live metrics:', metrics);
});
```

---

## 🐛 ERROR CODES

| Code | Description |
|------|-------------|
| `SYSTEM_UNAVAILABLE` | System is in maintenance mode |
| `AGENT_UNAVAILABLE` | Requested agent is offline |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `INVALID_TOKEN` | Authentication token invalid |
| `DEPARTMENT_OFFLINE` | Entire department is offline |
| `METRICS_UNAVAILABLE` | Metrics collection temporarily down |

---

## 📞 SUPPORT

- **API Status**: Monitor at `/health`
- **Documentation**: This document  
- **WebSocket Testing**: Use built-in dashboard at `/dashboard`
- **Metrics Dashboard**: Available at `:8080/dashboard`

---

*For technical support or API questions, refer to the system administrators or check the real-time dashboard for current system status.*