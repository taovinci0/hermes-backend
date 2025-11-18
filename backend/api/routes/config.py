"""Configuration management endpoints."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from ..services.config_service import ConfigService

router = APIRouter()
config_service = ConfigService()


@router.get("")
async def get_config():
    """Get current configuration.
    
    Returns:
        Dictionary with all configuration values
    """
    return config_service.get_config()


@router.put("")
async def update_config(updates: Dict[str, Any]):
    """Update configuration.
    
    Args:
        updates: Dictionary with configuration updates
        
    Returns:
        Dictionary with success status and updated fields
        
    Raises:
        HTTPException: If validation fails
    """
    result = config_service.update_config(updates)
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Configuration validation failed",
                "errors": result["errors"]
            }
        )
    
    return result


@router.post("/validate")
async def validate_config(config: Dict[str, Any]):
    """Validate configuration without saving.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Dictionary with validation result and errors
    """
    is_valid, errors = config_service.validate_config(config)
    
    return {
        "valid": is_valid,
        "errors": errors,
    }


@router.post("/reload")
async def reload_config():
    """Reload configuration from disk.
    
    Returns:
        Current configuration
    """
    return config_service.reload_config()


@router.get("/defaults")
async def get_default_config():
    """Get default configuration values.
    
    Returns:
        Dictionary with default configuration values
    """
    return config_service.get_default_config()


@router.post("/reset")
async def reset_config():
    """Reset configuration to defaults.
    
    Returns:
        Dictionary with success status
        
    Raises:
        HTTPException: If reset fails
    """
    result = config_service.reset_to_defaults()
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail=result.get("errors", ["Failed to reset configuration"])
        )
    
    return result

