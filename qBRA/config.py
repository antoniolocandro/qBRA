"""Facility configuration registry for qBRA plugin.

Centralises all FacilityConfig objects that were previously defined inside
IlsLlzDockWidget._init_facility().  Import FACILITY_REGISTRY wherever you
need to look up a facility by key.
"""

from qBRA.models.bra_parameters import FacilityConfig, FacilityDefaults

# ---------------------------------------------------------------------------
# Standard ILS/LLZ facility definitions
# ---------------------------------------------------------------------------

FACILITY_REGISTRY: dict[str, FacilityConfig] = {
    "LOC": FacilityConfig(
        key="LOC",
        label="ILS LLZ \u2013 single frequency",
        a_depends_on_threshold=True,
        defaults=FacilityDefaults(b=500, h=70, D=500, H=10, L=2300, phi=30, r_expr="a+6000"),
    ),
    "LOCII": FacilityConfig(
        key="LOCII",
        label="ILS LLZ \u2013 dual frequency",
        a_depends_on_threshold=True,
        defaults=FacilityDefaults(b=500, h=70, D=500, H=20, L=1500, phi=20, r_expr="a+6000"),
    ),
    "GP": FacilityConfig(
        key="GP",
        label="ILS GP M-Type (dual)",
        a_depends_on_threshold=False,
        defaults=FacilityDefaults(a=800, b=50, h=70, D=250, H=5, L=325, phi=10, r=6000),
    ),
    "DME": FacilityConfig(
        key="DME",
        label="DME (directional)",
        a_depends_on_threshold=True,
        defaults=FacilityDefaults(b=20, h=70, D=600, H=20, L=1500, phi=40, r_expr="a+6000"),
    ),
}
