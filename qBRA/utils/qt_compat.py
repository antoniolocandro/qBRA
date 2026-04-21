"""Qt5 / Qt6 and QGIS 3/4 compatibility shim for qgis.PyQt.

QGIS 3.x bundles PyQt5 (Qt 5.x); QGIS 4.x bundles PyQt6 (Qt 6.x).
Both are accessed uniformly via ``qgis.PyQt``, but several enum values moved
between QGIS/Qt versions:

    Qt5/QGIS3:  ``Qt.LeftDockWidgetArea``,  ``Qgis.Warning``
    Qt6/QGIS4:  ``Qt.DockWidgetArea.LeftDockWidgetArea``,  ``Qgis.MessageLevel.Warning``

Additionally, PyQt6 removes ``QVariant`` entirely — use ``QMetaType.Type``
instead.

Import all version-sensitive symbols from this module so the plugin runs
unmodified under both QGIS 3 and QGIS 4.

Usage::

    from qBRA.utils.qt_compat import (
        LeftDockWidgetArea, RightDockWidgetArea,
        QVariantInt, QVariantString, QVariantDouble,
        MsgInfo, MsgWarning, MsgCritical, MsgSuccess,
    )
"""

from qgis.PyQt.QtCore import Qt
from qgis.core import Qgis

# ---------------------------------------------------------------------------
# Dock-area flags
# Qt5 places the values directly on ``Qt``; Qt6 nests them in the enum class.
# ---------------------------------------------------------------------------
if hasattr(Qt, "LeftDockWidgetArea"):
    # Qt 5 (PyQt5 / QGIS 3.x)
    LeftDockWidgetArea = Qt.LeftDockWidgetArea    # type: ignore[attr-defined]
    RightDockWidgetArea = Qt.RightDockWidgetArea  # type: ignore[attr-defined]
else:
    # Qt 6 (PyQt6 / QGIS 4.x)
    LeftDockWidgetArea = Qt.DockWidgetArea.LeftDockWidgetArea    # type: ignore[attr-defined]
    RightDockWidgetArea = Qt.DockWidgetArea.RightDockWidgetArea  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# QVariant field-type constants
# ``QVariant`` exists in PyQt5 / QGIS 3.x but was removed entirely in
# PyQt6 / QGIS 4.x.  In Qt6 the equivalent is ``QMetaType.Type``.
# ---------------------------------------------------------------------------
try:
    from qgis.PyQt.QtCore import QVariant as _QVariant  # type: ignore[attr-defined]
    QVariantInt = _QVariant.Int        # type: ignore[attr-defined]
    QVariantString = _QVariant.String  # type: ignore[attr-defined]
    QVariantDouble = _QVariant.Double  # type: ignore[attr-defined]
except (ImportError, AttributeError):
    # PyQt6 / QGIS 4.x — QVariant removed; QMetaType.Type is the replacement.
    from qgis.PyQt.QtCore import QMetaType as _QMetaType  # type: ignore[attr-defined]
    QVariantInt = _QMetaType.Type.Int        # type: ignore[attr-defined]
    QVariantString = _QMetaType.Type.QString  # type: ignore[attr-defined]
    QVariantDouble = _QMetaType.Type.Double  # type: ignore[attr-defined]

# ---------------------------------------------------------------------------
# Qgis message-level constants
# QGIS 3: Qgis.Info / Qgis.Warning / Qgis.Critical / Qgis.Success (flat)
# QGIS 4: Qgis.MessageLevel.Info / .Warning / .Critical / .Success (nested)
# Use MsgInfo, MsgWarning, MsgCritical, MsgSuccess throughout the plugin.
# ---------------------------------------------------------------------------
if hasattr(Qgis, "MessageLevel"):
    # QGIS 4.x — values nested inside Qgis.MessageLevel
    MsgInfo = Qgis.MessageLevel.Info        # type: ignore[attr-defined]
    MsgWarning = Qgis.MessageLevel.Warning  # type: ignore[attr-defined]
    MsgCritical = Qgis.MessageLevel.Critical  # type: ignore[attr-defined]
    MsgSuccess = Qgis.MessageLevel.Success  # type: ignore[attr-defined]
else:
    # QGIS 3.x — flat attributes on Qgis
    MsgInfo = Qgis.Info        # type: ignore[attr-defined]
    MsgWarning = Qgis.Warning  # type: ignore[attr-defined]
    MsgCritical = Qgis.Critical  # type: ignore[attr-defined]
    MsgSuccess = Qgis.Success  # type: ignore[attr-defined]

__all__ = [
    "LeftDockWidgetArea",
    "RightDockWidgetArea",
    "QVariantInt",
    "QVariantString",
    "QVariantDouble",
    "MsgInfo",
    "MsgWarning",
    "MsgCritical",
    "MsgSuccess",
]
