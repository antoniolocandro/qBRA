"""
Pytest configuration and fixtures for qBRA tests.

This file contains shared fixtures and configuration for all tests.
Fixtures are used to provide test data, mock objects, and setup/teardown logic.

IMPORTANT: QGIS mock injection happens at module level (top of this file) so
that all qBRA imports in test files succeed without a real QGIS installation.
"""

import sys
from unittest.mock import Mock, MagicMock

# ============================================================================
# QGIS Mock — injected at module level so all qBRA test imports work
# without a real QGIS installation.
# ============================================================================
try:
    import qgis.core  # Only present in a full QGIS environment
except ImportError:
    # --- Typed stubs ----------------------------------------------------------

    class _QgsWkbTypes:
        """Minimal WKB type constants and geometryType helper."""
        Point = 1
        MultiPoint = 4
        LineString = 2
        MultiLineString = 5
        Polygon = 3
        MultiPolygon = 6
        PointGeometry = 0
        LineGeometry = 1
        PolygonGeometry = 2
        UnknownGeometry = 3
        NullGeometry = 4

        @staticmethod
        def geometryType(wkb_type: int) -> int:
            _map = {
                1: 0, 4: 0,   # Point  → PointGeometry
                2: 1, 5: 1,   # Line   → LineGeometry
                3: 2, 6: 2,   # Poly   → PolygonGeometry
            }
            return _map.get(wkb_type, 3)  # 3 = UnknownGeometry

    class _QgsVectorLayer:
        """Minimal vector layer stub — real class so isinstance() works."""
        pass

    class _QgsLayerTreeNode:
        NodeLayer = 0
        NodeGroup = 1

    class _QgsFeature:
        """Minimal QgsFeature stub that stores geometry and attributes."""
        def __init__(self) -> None:
            self._geometry: Any = None
            self._attributes: list = []

        def setGeometry(self, geom: Any) -> None:
            self._geometry = geom

        def setAttributes(self, attrs: list) -> None:
            self._attributes = list(attrs)

        def attributes(self) -> list:
            return self._attributes

        def hasGeometry(self) -> bool:
            return self._geometry is not None

        def geometry(self) -> Any:
            return self._geometry

    # --- Assemble mocked qgis.core module ------------------------------------
    _core = MagicMock()
    _core.QgsWkbTypes = _QgsWkbTypes
    _core.QgsVectorLayer = _QgsVectorLayer
    _core.QgsLayerTreeNode = _QgsLayerTreeNode
    _core.QgsFeature = _QgsFeature

    # --- PyQt stubs -----------------------------------------------------------
    _pyqt_qtcore = MagicMock()
    _pyqt_qtcore.Qt = MagicMock()
    _pyqt_qtcore.pyqtSignal = MagicMock(return_value=MagicMock())
    _pyqt_qtcore.QVariant = MagicMock()

    # --- Inject into sys.modules (setdefault: skip if already present) -------
    sys.modules.setdefault("qgis", MagicMock())
    sys.modules.setdefault("qgis.core", _core)
    sys.modules.setdefault("qgis.PyQt", MagicMock())
    sys.modules.setdefault("qgis.PyQt.QtCore", _pyqt_qtcore)
    sys.modules.setdefault("qgis.PyQt.QtGui", MagicMock())
    sys.modules.setdefault("qgis.PyQt.QtWidgets", MagicMock())
    sys.modules.setdefault("qgis.PyQt.uic", MagicMock())
    sys.modules.setdefault("qgis.utils", MagicMock())

# ============================================================================
# Standard imports — must come AFTER sys.modules injection
# ============================================================================
import pytest
from typing import Any, Dict

# qBRA models are importable now that QGIS stubs are in sys.modules
from qBRA.models.bra_parameters import BRAParameters, FacilityConfig, FacilityDefaults

MODELS_AVAILABLE = True


# ============================================================================
# QGIS Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_qgis_iface() -> Mock:
    """
    Mock QGIS iface (interface) object.
    
    Returns:
        Mock object with common iface methods and properties.
    """
    iface = Mock()
    iface.mainWindow.return_value = Mock()
    iface.messageBar.return_value = Mock()
    iface.mapCanvas.return_value = Mock()
    iface.activeLayer.return_value = None
    return iface


@pytest.fixture
def mock_qgs_vector_layer() -> Mock:
    """
    Mock QgsVectorLayer object that passes isinstance(layer, QgsVectorLayer).

    The ``__class__`` assignment is the standard approach to make a Mock
    respond correctly to isinstance checks without requiring a real QGIS install.

    Returns:
        Mock vector layer with basic properties.
    """
    from qgis.core import QgsVectorLayer, QgsWkbTypes
    layer = Mock()
    layer.__class__ = QgsVectorLayer   # isinstance(layer, QgsVectorLayer) → True
    layer.name.return_value = "TestLayer"
    layer.selectedFeatures.return_value = []
    layer.fields.return_value = Mock()
    layer.wkbType.return_value = QgsWkbTypes.Point
    return layer


@pytest.fixture
def mock_qgs_feature() -> Mock:
    """
    Mock QgsFeature object.
    
    Returns:
        Mock feature with geometry and attributes.
    """
    feature = Mock()
    feature.id.return_value = 1
    feature.geometry.return_value = Mock()
    feature.attributes.return_value = []
    return feature


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_bra_parameters():
    """Sample BRA parameters for testing.
    
    Returns:
        BRAParameters dataclass instance with valid calculation parameters.
    """
    # Create a mock layer for testing
    mock_layer = Mock()
    mock_layer.name.return_value = "TestNavaidLayer"
    mock_layer.selectedFeatures.return_value = [Mock()]
    
    return BRAParameters(
        active_layer=mock_layer,
        a=1000.0,
        b=500.0,
        h=70.0,
        r=7000.0,
        D=500.0,
        H=10.0,
        L=2300.0,
        phi=30.0,
        azimuth=90.0,
        site_elev=100.0,
        remark="RWY09",
        direction="forward",
        facility_key="LOC",
        facility_label="ILS LLZ – single frequency",
    )


@pytest.fixture
def sample_facility_config():
    """Sample facility configuration for testing.

    Returns:
        FacilityConfig dataclass instance with defaults.
    """
    return FacilityConfig(
        key="LOC",
        label="ILS LLZ – single frequency",
        a_depends_on_threshold=True,
        defaults=FacilityDefaults(
            b=500,
            h=70,
            D=500,
            H=10,
            L=2300,
            phi=30,
            r_expr="a+6000",
        ),
    )


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def temp_project_dir(tmp_path):
    """
    Create a temporary directory for test files.
    
    Args:
        tmp_path: Pytest built-in fixture for temporary directories.
        
    Returns:
        Path to temporary directory.
    """
    return tmp_path


# ============================================================================
# Markers Configuration
# ============================================================================

def pytest_configure(config):
    """
    Configure pytest markers.
    
    This is called before tests are collected.
    """
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated)")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow tests (skip with -m 'not slow')")
    config.addinivalue_line("markers", "qgis: Tests requiring QGIS environment")


# ============================================================================
# Test Session Hooks
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Setup test environment before all tests.
    
    This runs once at the start of the test session.
    """
    # Add any global setup here
    print("\n🧪 Setting up test environment...")
    yield
    # Add any global teardown here
    print("\n✅ Test environment cleaned up")


# ============================================================================
# Helper Functions
# ============================================================================

def assert_valid_geometry(geometry):
    """
    Assert that a geometry object is valid.
    
    Args:
        geometry: QgsGeometry object to validate.
        
    Raises:
        AssertionError: If geometry is not valid.
    """
    assert geometry is not None, "Geometry should not be None"
    assert geometry.isGeosValid(), "Geometry should be valid"


def assert_feature_has_fields(feature, expected_fields):
    """
    Assert that a feature has all expected fields.
    
    Args:
        feature: QgsFeature object.
        expected_fields: List of expected field names.
        
    Raises:
        AssertionError: If any expected field is missing.
    """
    actual_fields = [field.name() for field in feature.fields()]
    for field in expected_fields:
        assert field in actual_fields, f"Field '{field}' not found in feature"
