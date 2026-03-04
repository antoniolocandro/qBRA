"""
Pytest configuration and fixtures for qBRA tests.

This file contains shared fixtures and configuration for all tests.
Fixtures are used to provide test data, mock objects, and setup/teardown logic.
"""

import pytest
from typing import Any, Dict
from unittest.mock import Mock, MagicMock

# Import dataclass models for fixtures
try:
    from qBRA.models.bra_parameters import BRAParameters, FacilityConfig, FacilityDefaults
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False


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
    Mock QgsVectorLayer object.
    
    Returns:
        Mock vector layer with basic properties.
    """
    layer = Mock()
    layer.name.return_value = "TestLayer"
    layer.selectedFeatures.return_value = []
    layer.fields.return_value = Mock()
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
    if not MODELS_AVAILABLE:
        pytest.skip("qBRA models not available")
    
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
    if not MODELS_AVAILABLE:
        pytest.skip("qBRA models not available")
    
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
