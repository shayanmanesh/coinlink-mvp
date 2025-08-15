from fastapi import APIRouter, HTTPException, Query
from typing import Dict
import logging
from .registration_state import RegistrationFlow

logger = logging.getLogger(__name__)
router = APIRouter()

# Global registration flow instance
registration_flow = RegistrationFlow()

@router.get("/verify")
async def verify_user(token: str = Query(..., description="Verification token")):
    """Verify user account with token"""
    try:
        email = registration_flow.verify_token(token)
        if not email:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")
        
        if registration_flow.activate_user(email):
            return {
                "success": True,
                "message": f"Account verified successfully! Welcome {email}",
                "email": email
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to activate account")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Verification error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during verification")

@router.get("/status")
async def get_registration_status():
    """Get registration system status (for debugging)"""
    return {
        "active_sessions": len(registration_flow.states),
        "pending_users": len(registration_flow.pending_users),
        "status": "operational"
    }
