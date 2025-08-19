"""
Simple R&D status endpoint for production verification
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/api/rd", tags=["rd-status"])

@router.get("/status")
async def rd_system_status():
    """Simple R&D system status check"""
    try:
        # Try to import R&D modules
        from ...rd.scheduler import rd_scheduler
        from ...rd.rd_orchestrator import rd_orchestrator
        from ...rd.notification_system import email_notifier
        
        return {
            "status": "available",
            "message": "R&D system modules loaded successfully",
            "scheduler_running": getattr(rd_scheduler, 'is_running', False),
            "email_recipient": getattr(email_notifier, 'default_recipient', 'unknown'),
            "timestamp": datetime.now().isoformat()
        }
    except ImportError as e:
        return {
            "status": "module_import_error", 
            "message": f"R&D modules failed to import: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"R&D system error: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@router.post("/test-immediate-report")
async def trigger_test_report():
    """Trigger an immediate test report"""
    try:
        from ...rd.scheduler import rd_scheduler
        await rd_scheduler.trigger_immediate_report()
        return {
            "status": "triggered",
            "message": "Test report generation triggered",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to trigger test report: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }