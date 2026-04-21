"""Data models for Building Restriction Area (BRA) calculations.

This module defines typed dataclasses for all parameter structures used in
ILS/LLZ BRA calculations, replacing Dict[str, Any] with strongly-typed models.
"""

from dataclasses import dataclass, field
from typing import Optional, Union
from qgis.core import QgsVectorLayer


@dataclass(frozen=True)
class FacilityDefaults:
    """Default parameter values for a facility type.
    
    Attributes:
        a: Distance from navaid to threshold (meters). Optional if depends on routing.
        b: Distance behind threshold (meters)
        h: Maximum obstacle height (meters)
        D: Half-width at threshold (meters)
        H: Maximum elevation above site (meters)
        L: Lateral distance (meters)
        phi: Divergence angle (degrees)
        r: Optional fixed radius (meters)
        r_expr: Optional expression for calculating r (e.g., "a+6000")
    """
    b: float
    h: float
    D: float
    H: float
    L: float
    phi: float
    a: Optional[float] = None
    r: Optional[float] = None
    r_expr: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate facility defaults."""
        # Validate that either r or r_expr is provided, but not both
        if self.r is not None and self.r_expr is not None:
            raise ValueError("Cannot specify both 'r' and 'r_expr'")
        
        # Validate non-negative values
        if self.b < 0:
            raise ValueError(f"b must be non-negative, got {self.b}")
        if self.h < 0:
            raise ValueError(f"h must be non-negative, got {self.h}")
        if self.D < 0:
            raise ValueError(f"D must be non-negative, got {self.D}")
        if self.H < 0:
            raise ValueError(f"H must be non-negative, got {self.H}")
        if self.L < 0:
            raise ValueError(f"L must be non-negative, got {self.L}")
        if not (0 <= self.phi <= 180):
            raise ValueError(f"phi must be between 0 and 180 degrees, got {self.phi}")
        if self.a is not None and self.a < 0:
            raise ValueError(f"a must be non-negative, got {self.a}")
        if self.r is not None and self.r < 0:
            raise ValueError(f"r must be non-negative, got {self.r}")


@dataclass(frozen=True)
class FacilityConfig:
    """Configuration for a facility type (LOC, LOCII, GP, DME, etc.).
    
    Attributes:
        key: Short identifier (e.g., "LOC", "LOCII")
        label: Human-readable label (e.g., "ILS LLZ – single frequency")
        a_depends_on_threshold: If True, 'a' is calculated from routing geometry
        defaults: Default parameter values for this facility
    """
    key: str
    label: str
    a_depends_on_threshold: bool
    defaults: FacilityDefaults
    
    def __post_init__(self) -> None:
        """Validate facility configuration."""
        if not self.key:
            raise ValueError("Facility key cannot be empty")
        if not self.label:
            raise ValueError("Facility label cannot be empty")
        
        # If a_depends_on_threshold is True, 'a' should not be in defaults
        if self.a_depends_on_threshold and self.defaults.a is not None:
            raise ValueError(
                f"Facility {self.key}: when a_depends_on_threshold is True, "
                f"defaults should not specify 'a'"
            )
        
        # If a_depends_on_threshold is False, 'a' must be in defaults
        if not self.a_depends_on_threshold and self.defaults.a is None:
            raise ValueError(
                f"Facility {self.key}: when a_depends_on_threshold is False, "
                f"defaults must specify 'a'"
            )


@dataclass
class BRAParameters:
    """Parameters for Building Restriction Area (BRA) calculation.
    
    This replaces the Dict[str, Any] parameter structure with a strongly-typed
    dataclass that includes validation.
    
    Attributes:
        active_layer: QGIS vector layer with navaid feature
        azimuth: Direction angle in degrees (0–360, exclusive)
        a: Distance from navaid to threshold (meters)
        b: Distance behind threshold (meters)
        h: Maximum obstacle height (meters)
        r: Radius of protection (meters)
        D: Half-width at threshold (meters)
        H: Maximum elevation above site (meters)
        L: Lateral distance (meters)
        phi: Divergence angle (degrees)
        site_elev: Site elevation (meters)
        remark: Identifier/label for the output (e.g., "RWY09")
        direction: Routing direction ("forward" or "backward")
        facility_key: Facility type identifier (e.g., "LOC", "LOCII")
        facility_label: Human-readable facility name
        display_name: Full display name for output layer (optional, computed from remark if None)
    """
    active_layer: QgsVectorLayer
    azimuth: float
    a: float
    b: float
    h: float
    r: float
    D: float
    H: float
    L: float
    phi: float
    site_elev: float
    remark: str
    direction: str
    facility_key: str
    facility_label: str
    display_name: Optional[str] = None
    
    def __post_init__(self) -> None:
        """Validate BRA parameters and compute derived values."""
        # Validate azimuth (must be normalized to [0, 360) before construction)
        if not (0 <= self.azimuth < 360):
            raise ValueError(f"azimuth must be in [0, 360), got {self.azimuth} — normalize with '% 360' before passing")
        
        # Validate non-negative values
        if self.a < 0:
            raise ValueError(f"a must be non-negative, got {self.a}")
        if self.b < 0:
            raise ValueError(f"b must be non-negative, got {self.b}")
        if self.h < 0:
            raise ValueError(f"h must be non-negative, got {self.h}")
        if self.r < 0:
            raise ValueError(f"r must be non-negative, got {self.r}")
        if self.D < 0:
            raise ValueError(f"D must be non-negative, got {self.D}")
        if self.H < 0:
            raise ValueError(f"H must be non-negative, got {self.H}")
        if self.L < 0:
            raise ValueError(f"L must be non-negative, got {self.L}")
        if not (0 <= self.phi <= 180):
            raise ValueError(f"phi must be between 0 and 180 degrees, got {self.phi}")
        
        # Validate direction
        if self.direction not in ("forward", "backward"):
            raise ValueError(f"direction must be 'forward' or 'backward', got {self.direction}")
        
        # Validate strings are not empty
        if not self.remark:
            raise ValueError("remark cannot be empty")
        if not self.facility_key:
            raise ValueError("facility_key cannot be empty")
        if not self.facility_label:
            raise ValueError("facility_label cannot be empty")
        
        # Compute display_name if not provided
        if self.display_name is None:
            object.__setattr__(
                self, 
                'display_name', 
                f"{self.remark} - {self.facility_label}" if self.facility_label else self.remark
            )
    
    def to_dict(self) -> dict:
        """Convert to dictionary format for backward compatibility.
        
        Returns:
            Dictionary with all parameters (legacy format)
        """
        return {
            "active_layer": self.active_layer,
            "azimuth": self.azimuth,
            "a": self.a,
            "b": self.b,
            "h": self.h,
            "r": self.r,
            "D": self.D,
            "H": self.H,
            "L": self.L,
            "phi": self.phi,
            "remark": self.remark,
            "direction": self.direction,
            "site_elev": self.site_elev,
            "facility_key": self.facility_key,
            "facility_label": self.facility_label,
            "display_name": self.display_name,
        }
