"""Strategy documentation and changelog endpoints."""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any

from ..services.strategy_service import StrategyService

router = APIRouter()
strategy_service = StrategyService()


@router.get("/strategy")
async def get_strategy():
    """Get current strategy documentation.
    
    Returns:
        Dictionary with strategy documentation including:
        - Models (spread_model, bands_model)
        - Trading strategy (edge calculation, position sizing, etc.)
    """
    try:
        return strategy_service.get_strategy_documentation()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load strategy documentation: {str(e)}")


@router.get("/strategy/changelog")
async def get_changelog(
    limit: Optional[int] = Query(None, description="Maximum number of entries to return"),
    category: Optional[str] = Query(None, description="Filter by category (model, configuration, feature, documentation)"),
    type_filter: Optional[str] = Query(None, description="Filter by type (added, changed, removed, fixed, initial)"),
):
    """Get strategy changelog.
    
    Returns all changes to models, features, and configurations.
    Use category and type_filter to narrow down results.
    
    Args:
        limit: Maximum number of entries to return
        category: Filter by category
        type_filter: Filter by type
    
    Returns:
        Dictionary with changelog entries
    """
    try:
        return strategy_service.get_changelog(
            limit=limit,
            category=category,
            type_filter=type_filter,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load changelog: {str(e)}")


@router.get("/strategy/changelog/configuration")
async def get_configuration_changelog(
    limit: Optional[int] = Query(None, description="Maximum number of entries to return"),
):
    """Get trading configuration changelog (separate from model changes).
    
    This endpoint returns only configuration changes (edge_min, kelly_cap, etc.),
    separate from model/feature changes.
    
    Args:
        limit: Maximum number of entries to return
    
    Returns:
        Dictionary with configuration changelog entries
    """
    try:
        return strategy_service.get_configuration_changelog(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load configuration changelog: {str(e)}")


@router.post("/strategy/changelog")
async def add_changelog_entry(
    title: str,
    description: str,
    category: str,
    entry_type: str = "changed",
    affected_components: Optional[list[str]] = None,
    changes: Optional[list[Dict[str, str]]] = None,
    author: Optional[str] = None,
):
    """Add a new changelog entry (for manual logging of model/feature changes).
    
    Use this endpoint to manually log changes to models or features.
    Configuration changes are automatically logged via the config service.
    
    Args:
        title: Short title for the change
        description: Detailed description of what changed
        category: Category of change ('model', 'configuration', 'feature', 'documentation')
        entry_type: Type of change ('added', 'changed', 'removed', 'fixed', 'initial')
        affected_components: List of component names affected
        changes: List of detailed changes, each with 'component' and 'change' keys
        author: Optional author name
    
    Returns:
        The created changelog entry
    """
    try:
        return strategy_service.add_changelog_entry(
            title=title,
            description=description,
            category=category,
            entry_type=entry_type,
            affected_components=affected_components,
            changes=changes,
            author=author,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add changelog entry: {str(e)}")

