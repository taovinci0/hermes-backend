"""Service for managing strategy documentation and changelog."""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ..utils.path_utils import PROJECT_ROOT


class StrategyService:
    """Service for managing strategy documentation and changelog."""
    
    def __init__(self):
        """Initialize strategy service."""
        self.strategy_dir = PROJECT_ROOT / "data" / "strategy"
        self.strategy_dir.mkdir(parents=True, exist_ok=True)
        
        self.docs_file = self.strategy_dir / "strategy_documentation.json"
        self.changelog_file = self.strategy_dir / "changelog.json"
        
        # Initialize files if they don't exist
        self._ensure_files_exist()
    
    def _ensure_files_exist(self):
        """Ensure documentation and changelog files exist."""
        if not self.docs_file.exists():
            self._create_default_docs()
        if not self.changelog_file.exists():
            self._create_default_changelog()
    
    def _create_default_docs(self):
        """Create default documentation file."""
        default_docs = {
            "version": "1.0.0",
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "models": {},
            "trading_strategy": {}
        }
        self._write_json(self.docs_file, default_docs)
    
    def _create_default_changelog(self):
        """Create default changelog file."""
        default_changelog = {
            "version": "1.0.0",
            "entries": []
        }
        self._write_json(self.changelog_file, default_changelog)
    
    def _read_json(self, file_path: Path) -> Dict[str, Any]:
        """Read JSON file."""
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to read {file_path}: {e}")
    
    def _write_json(self, file_path: Path, data: Dict[str, Any]):
        """Write JSON file."""
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def get_strategy_documentation(self) -> Dict[str, Any]:
        """Get current strategy documentation.
        
        Returns:
            Dictionary with strategy documentation including models and trading strategy
        """
        return self._read_json(self.docs_file)
    
    def get_changelog(
        self,
        limit: Optional[int] = None,
        category: Optional[str] = None,
        type_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get strategy changelog.
        
        Args:
            limit: Maximum number of entries to return (None = all)
            category: Filter by category (e.g., 'model', 'configuration', 'feature')
            type_filter: Filter by type (e.g., 'added', 'changed', 'removed')
        
        Returns:
            Dictionary with changelog entries
        """
        changelog = self._read_json(self.changelog_file)
        entries = changelog.get("entries", [])
        
        # Apply filters
        if category:
            entries = [e for e in entries if e.get("category") == category]
        
        if type_filter:
            entries = [e for e in entries if e.get("type") == type_filter]
        
        # Sort by date (newest first)
        entries.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        # Apply limit
        if limit:
            entries = entries[:limit]
        
        return {
            "version": changelog.get("version", "1.0.0"),
            "total_entries": len(changelog.get("entries", [])),
            "filtered_entries": len(entries),
            "entries": entries,
        }
    
    def add_changelog_entry(
        self,
        title: str,
        description: str,
        category: str,
        entry_type: str = "changed",
        affected_components: Optional[List[str]] = None,
        changes: Optional[List[Dict[str, str]]] = None,
        author: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add a new changelog entry.
        
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
        changelog = self._read_json(self.changelog_file)
        
        # Generate entry ID
        timestamp = datetime.utcnow()
        entry_id = f"{timestamp.strftime('%Y-%m-%d')}-{len(changelog.get('entries', [])) + 1}"
        
        entry = {
            "id": entry_id,
            "date": timestamp.isoformat() + "Z",
            "type": entry_type,
            "category": category,
            "title": title,
            "description": description,
            "affected_components": affected_components or [],
            "changes": changes or [],
        }
        
        if author:
            entry["author"] = author
        
        # Add to changelog
        if "entries" not in changelog:
            changelog["entries"] = []
        
        changelog["entries"].append(entry)
        
        # Write back
        self._write_json(self.changelog_file, changelog)
        
        return entry
    
    def get_configuration_changelog(
        self,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get trading configuration changelog (separate from model changes).
        
        Args:
            limit: Maximum number of entries to return
        
        Returns:
            Dictionary with configuration changelog entries
        """
        changelog = self._read_json(self.changelog_file)
        entries = changelog.get("entries", [])
        
        # Filter for configuration changes
        config_entries = [
            e for e in entries
            if e.get("category") == "configuration"
        ]
        
        # Sort by date (newest first)
        config_entries.sort(key=lambda x: x.get("date", ""), reverse=True)
        
        # Apply limit
        if limit:
            config_entries = config_entries[:limit]
        
        return {
            "version": changelog.get("version", "1.0.0"),
            "total_entries": len(config_entries),
            "entries": config_entries,
        }
    
    def log_configuration_change(
        self,
        old_config: Dict[str, Any],
        new_config: Dict[str, Any],
        author: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log a trading configuration change.
        
        Args:
            old_config: Previous configuration values
            new_config: New configuration values
            author: Optional author name
        
        Returns:
            The created changelog entry
        """
        # Find what changed
        changes = []
        affected_components = []
        
        # Compare trading config
        old_trading = old_config.get("trading", {})
        new_trading = new_config.get("trading", {})
        
        for key in set(list(old_trading.keys()) + list(new_trading.keys())):
            old_val = old_trading.get(key)
            new_val = new_trading.get(key)
            
            if old_val != new_val:
                changes.append({
                    "component": f"trading.{key}",
                    "change": f"Changed from {old_val} to {new_val}",
                    "old_value": str(old_val),
                    "new_value": str(new_val),
                })
                affected_components.append(f"trading.{key}")
        
        # Compare probability model config
        old_prob = old_config.get("probability_model", {})
        new_prob = new_config.get("probability_model", {})
        
        for key in set(list(old_prob.keys()) + list(new_prob.keys())):
            old_val = old_prob.get(key)
            new_val = new_prob.get(key)
            
            if old_val != new_val:
                changes.append({
                    "component": f"probability_model.{key}",
                    "change": f"Changed from {old_val} to {new_val}",
                    "old_value": str(old_val),
                    "new_value": str(new_val),
                })
                affected_components.append(f"probability_model.{key}")
        
        if not changes:
            raise ValueError("No configuration changes detected")
        
        # Create changelog entry
        title = f"Configuration Change: {', '.join(affected_components[:3])}"
        if len(affected_components) > 3:
            title += f" and {len(affected_components) - 3} more"
        
        description = f"Updated trading or model configuration. {len(changes)} parameter(s) changed."
        
        return self.add_changelog_entry(
            title=title,
            description=description,
            category="configuration",
            entry_type="changed",
            affected_components=affected_components,
            changes=changes,
            author=author,
        )

