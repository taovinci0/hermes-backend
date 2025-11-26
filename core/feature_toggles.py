"""Feature toggle configuration management.

Allows toggling features on/off, such as station calibration.
"""

from dataclasses import dataclass
from typing import Optional
import json
from pathlib import Path

from .config import PROJECT_ROOT
from .logger import logger


@dataclass
class FeatureToggles:
    """Feature toggle configuration."""
    
    station_calibration: bool = False
    
    @classmethod
    def load(cls, config_path: Optional[Path] = None) -> "FeatureToggles":
        """Load toggles from JSON file.
        
        Args:
            config_path: Optional path to feature_toggles.json
                        (defaults to data/config/feature_toggles.json)
        
        Returns:
            FeatureToggles instance
        """
        if config_path is None:
            config_path = PROJECT_ROOT / "data" / "config" / "feature_toggles.json"
        
        if not config_path.exists():
            # Create default
            toggles = cls()
            toggles.save(config_path)
            logger.info(
                f"Created default feature toggles at {config_path}"
            )
            return toggles
        
        try:
            with open(config_path) as f:
                data = json.load(f)
            
            return cls(**data)
        except Exception as e:
            logger.error(f"Failed to load feature toggles from {config_path}: {e}")
            # Return defaults on error
            return cls()
    
    def save(self, config_path: Optional[Path] = None) -> None:
        """Save toggles to JSON file.
        
        Args:
            config_path: Optional path to feature_toggles.json
                        (defaults to data/config/feature_toggles.json)
        """
        if config_path is None:
            config_path = PROJECT_ROOT / "data" / "config" / "feature_toggles.json"
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(config_path, "w") as f:
                json.dump({
                    "station_calibration": self.station_calibration,
                }, f, indent=2)
            
            logger.debug(f"Saved feature toggles to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save feature toggles to {config_path}: {e}")
            raise
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses.
        
        Returns:
            Dictionary with toggle states
        """
        return {
            "station_calibration": self.station_calibration,
        }
    
    def __repr__(self) -> str:
        return (
            f"FeatureToggles(station_calibration={self.station_calibration})"
        )


