"""Tests for logging configuration."""

import logging
import pytest
from unittest.mock import Mock, patch, MagicMock

from qBRA.utils.logging_config import (
    QGISLogHandler,
    setup_logger,
    get_logger,
    PLUGIN_NAME,
    QGIS_AVAILABLE,
)


class TestQGISLogHandler:
    """Test QGIS log handler."""

    def test_handler_initialization(self):
        """Test handler can be initialized."""
        handler = QGISLogHandler()
        assert handler.plugin_name == PLUGIN_NAME

    def test_handler_custom_plugin_name(self):
        """Test handler accepts custom plugin name."""
        handler = QGISLogHandler("CustomPlugin")
        assert handler.plugin_name == "CustomPlugin"

    @pytest.mark.skipif(not QGIS_AVAILABLE, reason="QGIS not available")
    @patch("qBRA.utils.logging_config.QGIS_AVAILABLE", True)
    @patch("qBRA.utils.logging_config.QgsMessageLog")
    def test_emit_logs_to_qgis(self, mock_qgs_log):
        """Test that emit sends logs to QGIS MessageLog."""
        handler = QGISLogHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        handler.emit(record)
        
        # Verify QgsMessageLog was called
        mock_qgs_log.logMessage.assert_called_once()

    @patch("qBRA.utils.logging_config.QGIS_AVAILABLE", False)
    def test_emit_without_qgis(self, capsys):
        """Test that emit falls back to console when QGIS not available."""
        handler = QGISLogHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        handler.emit(record)
        
        # When QGIS not available, emit should return early
        # No exception should be raised


class TestSetupLogger:
    """Test logger setup function."""

    def test_setup_logger_creates_logger(self):
        """Test that setup_logger creates a logger with correct name."""
        logger_name = "qBRA.test.module"
        logger = setup_logger(logger_name, use_qgis=False)
        
        assert logger.name == logger_name
        assert isinstance(logger, logging.Logger)

    def test_setup_logger_sets_level(self):
        """Test that setup_logger sets correct logging level."""
        logger = setup_logger("qBRA.test.debug", level=logging.DEBUG, use_qgis=False)
        assert logger.level == logging.DEBUG
        
        logger2 = setup_logger("qBRA.test.warning", level=logging.WARNING, use_qgis=False)
        assert logger2.level == logging.WARNING

    def test_setup_logger_adds_handler(self):
        """Test that setup_logger adds appropriate handler."""
        logger = setup_logger("qBRA.test.handler", use_qgis=False)
        
        assert len(logger.handlers) > 0
        # Should have StreamHandler when use_qgis=False
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_setup_logger_no_duplicate_handlers(self):
        """Test that calling setup_logger twice doesn't add duplicate handlers."""
        logger_name = "qBRA.test.duplicate"
        
        logger1 = setup_logger(logger_name, use_qgis=False)
        initial_handler_count = len(logger1.handlers)
        
        logger2 = setup_logger(logger_name, use_qgis=False)
        
        assert logger1 is logger2  # Same logger instance
        assert len(logger2.handlers) == initial_handler_count  # No new handlers

    def test_setup_logger_formatter(self):
        """Test that setup_logger configures handler with formatter."""
        logger = setup_logger("qBRA.test.format", use_qgis=False)
        
        handler = logger.handlers[0]
        assert handler.formatter is not None
        
        # Test format includes expected components
        format_string = handler.formatter._fmt
        assert "%(asctime)s" in format_string
        assert "%(name)s" in format_string
        assert "%(levelname)s" in format_string
        assert "%(message)s" in format_string

    def test_setup_logger_no_propagate(self):
        """Test that logger doesn't propagate to root logger."""
        logger = setup_logger("qBRA.test.propagate", use_qgis=False)
        assert logger.propagate is False


class TestGetLogger:
    """Test convenience get_logger function."""

    def test_get_logger_returns_configured_logger(self):
        """Test that get_logger returns a properly configured logger."""
        logger = get_logger("qBRA.test.convenience")
        
        assert isinstance(logger, logging.Logger)
        assert logger.name == "qBRA.test.convenience"
        assert len(logger.handlers) > 0

    def test_get_logger_returns_same_instance(self):
        """Test that get_logger returns same logger instance for same name."""
        logger1 = get_logger("qBRA.test.singleton")
        logger2 = get_logger("qBRA.test.singleton")
        
        assert logger1 is logger2


class TestLoggingIntegration:
    """Test logging integration scenarios."""

    def test_logger_logs_debug_message(self):
        """Test that logger can log debug messages."""
        import io
        stream = io.StringIO()
        
        logger = setup_logger("qBRA.test.debug_msg", level=logging.DEBUG, use_qgis=False)
        # Add additional handler for testing
        test_handler = logging.StreamHandler(stream)
        test_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(test_handler)
        
        logger.debug("Debug message: %s", "test")
        
        output = stream.getvalue()
        assert "Debug message: test" in output

    def test_logger_logs_info_message(self):
        """Test that logger can log info messages."""
        import io
        stream = io.StringIO()
        
        logger = setup_logger("qBRA.test.info_msg", level=logging.INFO, use_qgis=False)
        # Add additional handler for testing
        test_handler = logging.StreamHandler(stream)
        test_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(test_handler)
        
        logger.info("Info message: %s", "test")
        
        output = stream.getvalue()
        assert "Info message: test" in output

    def test_logger_logs_warning_message(self):
        """Test that logger can log warning messages."""
        import io
        stream = io.StringIO()
        
        logger = setup_logger("qBRA.test.warning_msg", level=logging.WARNING, use_qgis=False)
        # Add additional handler for testing
        test_handler = logging.StreamHandler(stream)
        test_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(test_handler)
        
        logger.warning("Warning message: %s", "test")
        
        output = stream.getvalue()
        assert "Warning message: test" in output

    def test_logger_logs_error_message(self):
        """Test that logger can log error messages."""
        import io
        stream = io.StringIO()
        
        logger = setup_logger("qBRA.test.error_msg", level=logging.ERROR, use_qgis=False)
        # Add additional handler for testing
        test_handler = logging.StreamHandler(stream)
        test_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(test_handler)
        
        logger.error("Error message: %s", "test")
        
        output = stream.getvalue()
        assert "Error message: test" in output

    def test_logger_logs_exception_with_traceback(self):
        """Test that logger can log exceptions with traceback."""
        import io
        stream = io.StringIO()
        
        logger = setup_logger("qBRA.test.exception", level=logging.ERROR, use_qgis=False)
        # Add additional handler for testing
        test_handler = logging.StreamHandler(stream)
        test_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(test_handler)
        
        try:
            raise ValueError("Test exception")
        except ValueError:
            logger.error("Exception occurred", exc_info=True)
        
        output = stream.getvalue()
        assert "Exception occurred" in output
        assert "ValueError: Test exception" in output
        assert "Traceback" in output
