"""Central constants for the qBRA plugin.

Replaces magic numbers and string literals scattered across modules.
Import from here rather than repeating literal values.
"""

# ---------------------------------------------------------------------------
# Geometry calculation
# ---------------------------------------------------------------------------

#: Distance (metres) projected beyond intersection points to guarantee that
#: line–circle / segment–segment intersections are always computable.
PROJECTION_DISTANCE: int = 10_000

# ---------------------------------------------------------------------------
# Memory layer creation
# ---------------------------------------------------------------------------

#: Prefix for the WKT geometry type + CRS string used when creating memory
#: layers (e.g. ``"PolygonZ?crs=EPSG:4326"``).
CRS_TEMPLATE_PREFIX: str = "PolygonZ?crs="

#: Suffix appended to the display name when naming BRA output layers.
LAYER_NAME_SUFFIX: str = "BRA_areas"
