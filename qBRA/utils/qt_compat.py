"""Qt5 / Qt6 compatibility shim for qgis.PyQt.

QGIS 3.x bundles PyQt5 (Qt 5.x); future QGIS 4.x is expected to bundle
PyQt6 (Qt 6.x).  Both are accessed uniformly via ``qgis.PyQt``, but PyQt6
scoped previously flat enum values into per-class enum types:

    Qt5:  ``Qt.LeftDockWidgetArea``
    Qt6:  ``Qt.DockWidgetArea.LeftDockWidgetArea``

Import dock-area constants from this module instead of accessing them
directly on ``Qt`` so the plugin runs unmodified under both Qt generations.

Usage::

    from qBRA.utils.qt_compat import LeftDockWidgetArea, RightDockWidgetArea

    self.setAllowedAreas(LeftDockWidgetArea | RightDockWidgetArea)
"""

from qgis.PyQt.QtCore import Qt

# ---------------------------------------------------------------------------
# Dock-area flags
# Qt5 places the values directly on ``Qt``; Qt6 nests them in the enum class.
# ---------------------------------------------------------------------------
if hasattr(Qt, "LeftDockWidgetArea"):
    # Qt 5 (PyQt5 / QGIS 3.x)
    LeftDockWidgetArea = Qt.LeftDockWidgetArea    # type: ignore[attr-defined]
    RightDockWidgetArea = Qt.RightDockWidgetArea  # type: ignore[attr-defined]
else:
    # Qt 6 (PyQt6 / future QGIS 4.x)
    LeftDockWidgetArea = Qt.DockWidgetArea.LeftDockWidgetArea    # type: ignore[attr-defined]
    RightDockWidgetArea = Qt.DockWidgetArea.RightDockWidgetArea  # type: ignore[attr-defined]

__all__ = ["LeftDockWidgetArea", "RightDockWidgetArea"]
