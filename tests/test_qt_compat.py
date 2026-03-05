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
        """__all__ must enumerate the two public constants."""
        import qBRA.utils.qt_compat as compat
        assert "LeftDockWidgetArea" in compat.__all__
        assert "RightDockWidgetArea" in compat.__all__


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
