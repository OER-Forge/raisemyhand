"""
Admin configuration management routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session as DBSession
from typing import List, Optional
from datetime import datetime

from database import get_db
from models_config import SystemConfig
from schemas_v2 import ConfigUpdateRequest, ConfigResponse, RegistrationToggleRequest
from routes_admin import verify_admin  # Reuse the admin verification
from logging_config import get_logger, log_security_event

router = APIRouter(prefix="/api/admin/config", tags=["admin-config"])
logger = get_logger(__name__)

# Import manager for broadcasting
manager = None

def set_manager(connection_manager):
    global manager
    manager = connection_manager


@router.get("/all", response_model=List[ConfigResponse])
async def list_all_config(
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Get all system configuration settings."""
    configs = db.query(SystemConfig).order_by(SystemConfig.key).all()
    
    # Add parsed values for display
    result = []
    for config in configs:
        result.append({
            "key": config.key,
            "value": config.value,
            "value_type": config.value_type,
            "parsed_value": str(config.parsed_value),
            "description": config.description,
            "created_at": config.created_at,
            "updated_at": config.updated_at,
            "updated_by": config.updated_by
        })
    
    return result


@router.get("/{key}", response_model=ConfigResponse)
async def get_config(
    key: str,
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Get a specific configuration setting."""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuration key not found")
    
    return {
        "key": config.key,
        "value": config.value,
        "value_type": config.value_type,
        "parsed_value": str(config.parsed_value),
        "description": config.description,
        "created_at": config.created_at,
        "updated_at": config.updated_at,
        "updated_by": config.updated_by
    }


@router.put("/{key}")
async def update_config(
    key: str,
    request: ConfigUpdateRequest,
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Update a system configuration setting."""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration key not found")
    
    # Store old value for logging
    old_value = str(config.value)
    
    try:
        # Use set_value method to properly update the configuration
        SystemConfig.set_value(
            db=db,
            key=key,
            value=request.value,
            value_type=str(config.value_type),
            description=request.description or str(config.description or ""),
            updated_by=admin
        )
        
        log_security_event(
            logger, "CONFIG_UPDATED",
            f"Admin updated config {key}: '{old_value}' -> '{request.value}'",
            severity="info"
        )
        
        # Broadcast maintenance mode changes to all connected clients
        if key == "system_maintenance_mode" and manager:
            # Convert string value to boolean for broadcast
            enabled_bool = request.value in [True, "true", "True", "1", 1]
            await manager.broadcast_to_all({
                "type": "maintenance_mode_changed",
                "enabled": enabled_bool
            })
        
        return {"message": f"Configuration '{key}' updated successfully"}
    except Exception as e:
        logger.error(f"Failed to update config {key}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update configuration")


@router.post("/registration/toggle")
async def toggle_instructor_registration(
    request: RegistrationToggleRequest,
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Toggle instructor registration on/off."""
    
    # Set the registration enabled flag
    SystemConfig.set_value(
        db=db,
        key="instructor_registration_enabled",
        value=request.enabled,
        value_type="boolean",
        description="Controls whether new instructors can register accounts",
        updated_by=admin
    )
    
    # Set the reason if provided
    if request.reason:
        SystemConfig.set_value(
            db=db,
            key="instructor_registration_disabled_reason",
            value=request.reason,
            value_type="string",
            description="Reason for disabling instructor registration",
            updated_by=admin
        )
    
    action = "enabled" if request.enabled else "disabled"
    log_security_event(
        logger, f"REGISTRATION_{action.upper()}",
        f"Admin {action} instructor registration" + (f": {request.reason}" if request.reason else ""),
        severity="warning" if not request.enabled else "info"
    )
    
    return {
        "message": f"Instructor registration {action} successfully",
        "enabled": request.enabled,
        "reason": request.reason
    }


@router.get("/registration/status")
async def get_registration_status(
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Get current instructor registration status."""
    enabled = SystemConfig.get_value(db, "instructor_registration_enabled", default=True)  # Default to enabled
    reason = SystemConfig.get_value(db, "instructor_registration_disabled_reason", default="")
    
    return {
        "enabled": enabled,
        "reason": reason if not enabled else ""
    }


@router.post("/initialize-defaults")
async def initialize_default_config(
    db: DBSession = Depends(get_db),
    admin: str = Depends(verify_admin)
):
    """Initialize default system configuration settings."""
    
    defaults = [
        {
            "key": "instructor_registration_enabled",
            "value": True,
            "value_type": "boolean",
            "description": "Controls whether new instructors can register accounts"
        },
        {
            "key": "max_questions_per_session",
            "value": 1000,
            "value_type": "integer", 
            "description": "Maximum number of questions allowed per session"
        },
        {
            "key": "session_timeout_hours",
            "value": 24,
            "value_type": "integer",
            "description": "Hours after which inactive sessions are automatically ended"
        },
        {
            "key": "profanity_filter_enabled",
            "value": True,
            "value_type": "boolean",
            "description": "Enable automatic profanity filtering for questions"
        },
        {
            "key": "system_maintenance_mode",
            "value": False,
            "value_type": "boolean",
            "description": "Put system in maintenance mode (blocks most operations)"
        }
    ]
    
    created_count = 0
    for default_config in defaults:
        existing = db.query(SystemConfig).filter(SystemConfig.key == default_config["key"]).first()
        if not existing:
            SystemConfig.set_value(
                db=db,
                key=default_config["key"],
                value=default_config["value"],
                value_type=default_config["value_type"],
                description=default_config["description"],
                updated_by=admin
            )
            created_count += 1
    
    log_security_event(
        logger, "CONFIG_INITIALIZED",
        f"Admin initialized {created_count} default configuration settings",
        severity="info"
    )
    
    return {
        "message": f"Initialized {created_count} default configuration settings",
        "created_count": created_count
    }