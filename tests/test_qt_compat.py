"""Tests for qBRA.utils.qt_compat — Qt5/Qt6 compatibility shim."""

import pytest
from unittest.mock import MagicMock, patch


class TestQtCompatExports:
    """Verify the module is importable and exports the expected names."""

    def test_module_imports_without_error(self):
        """qt_compat must be importable in the mocked test environment."""
        import qBRA.utils.qt_compat  # noqa: F401 — import is the assertion

    def test_left_dock_widget_area_defined(self):
        """LeftDockWidgetArea must be a non-None attribute after import."""
        from qBRA.utils.qt_compat import LeftDockWidgetArea
        assert LeftDockWidgetArea is not None

    def test_right_dock_widget_area_defined(self):
        """RightDockWidgetArea must be a non-None attribute after import."""
        from qBRA.utils.qt_compat import RightDockWidgetArea
        assert RightDockWidgetArea is not None

    def test_all_lists_expected_names(self):
        """__all__ must enumerate all public constants."""
        import qBRA.utils.qt_compat as compat
        assert "LeftDockWidgetArea" in compat.__all__
        assert "RightDockWidgetArea" in compat.__all__
        assert "QVariantInt" in compat.__all__
        assert "QVariantString" in compat.__all__
        assert "QVariantDouble" in compat.__all__

    def test_qvariant_constants_defined(self):
        """QVariantInt, QVariantString, QVariantDouble must all be non-None."""
        from qBRA.utils.qt_compat import QVariantInt, QVariantString, QVariantDouble
        assert QVariantInt is not None
        assert QVariantString is not None
        assert QVariantDouble is not None


class TestQtCompatVersionDetection:
    """Verify the Qt5 / Qt6 detection branch logic."""

    def test_qt5_path_uses_flat_enum(self):
        """When Qt has LeftDockWidgetArea directly, the Qt5 path is taken."""
        mock_qt = MagicMock()
        mock_qt.LeftDockWidgetArea = "qt5_left"
        mock_qt.RightDockWidgetArea = "qt5_right"

        mock_core = MagicMock()
        mock_core.Qt = mock_qt

        with patch.dict("sys.modules", {"qgis.PyQt.QtCore": mock_core}):
            import importlib
            import qBRA.utils.qt_compat as compat
            # Reload to exercise the branch under the patched module
            importlib.reload(compat)
            assert compat.LeftDockWidgetArea == "qt5_left"
            assert compat.RightDockWidgetArea == "qt5_right"

    def test_qt6_path_uses_nested_enum(self):
        """When Qt lacks LeftDockWidgetArea directly, the Qt6 nested path is taken."""
        mock_qt = MagicMock(spec=[])  # spec=[] → no attributes → hasattr returns False
        nested = MagicMock()
        nested.LeftDockWidgetArea = "qt6_left"
        nested.RightDockWidgetArea = "qt6_right"
        mock_qt.DockWidgetArea = nested

        mock_core = MagicMock()
        mock_core.Qt = mock_qt

        with patch.dict("sys.modules", {"qgis.PyQt.QtCore": mock_core}):
            import importlib
            import qBRA.utils.qt_compat as compat
            importlib.reload(compat)
            assert compat.LeftDockWidgetArea == "qt6_left"
            assert compat.RightDockWidgetArea == "qt6_right"


class TestQtCompatQVariant:
    """Verify QVariant type constant detection for PyQt5 vs PyQt6."""

    def test_pyqt5_path_uses_qvariant(self):
        """When QVariant is available (PyQt5/QGIS 3), Int/String/Double are read from it."""
        mock_qvariant = MagicMock()
        mock_qvariant.Int = 2
        mock_qvariant.String = 10
        mock_qvariant.Double = 6

        mock_qt = MagicMock()
        mock_qt.LeftDockWidgetArea = "left"
        mock_qt.RightDockWidgetArea = "right"

        mock_core = MagicMock()
        mock_core.Qt = mock_qt
        mock_core.QVariant = mock_qvariant

        with patch.dict("sys.modules", {"qgis.PyQt.QtCore": mock_core}):
            import importlib
            import qBRA.utils.qt_compat as compat
            importlib.reload(compat)
            assert compat.QVariantInt == 2
            assert compat.QVariantString == 10
            assert compat.QVariantDouble == 6

    def test_pyqt6_path_uses_qmetatype(self):
        """When QVariant is absent (PyQt6/QGIS 4), constants fall back to QMetaType.Type."""
        mock_meta_type = MagicMock()
        mock_meta_type.Int = 2
        mock_meta_type.QString = 10
        mock_meta_type.Double = 6

        mock_qmetatype = MagicMock()
        mock_qmetatype.Type = mock_meta_type

        mock_qt = MagicMock(spec=[])  # no LeftDockWidgetArea → Qt6 path for dock areas too
        nested = MagicMock()
        nested.LeftDockWidgetArea = "left"
        nested.RightDockWidgetArea = "right"
        mock_qt.DockWidgetArea = nested

        mock_core = MagicMock(spec=["Qt", "QMetaType"])
        mock_core.Qt = mock_qt
        mock_core.QMetaType = mock_qmetatype
        # Simulate QVariant not existing: accessing it raises AttributeError
        type(mock_core).QVariant = property(lambda self: (_ for _ in ()).throw(AttributeError("no QVariant")))

        with patch.dict("sys.modules", {"qgis.PyQt.QtCore": mock_core}):
            import importlib
            import qBRA.utils.qt_compat as compat
            importlib.reload(compat)
            assert compat.QVariantInt == 2
            assert compat.QVariantString == 10
            assert compat.QVariantDouble == 6

