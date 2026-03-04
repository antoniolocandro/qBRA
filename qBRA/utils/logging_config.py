"""Logging configuration for qBRA plugin.

This module provides structured logging for the qBRA plugin, integrating with
QGIS MessageLog for display in the QGIS interface.
"""

import logging
from typing import Optional

try:
    from qgis.core import Qgis, QgsMessageLog
    QGIS_AVAILABLE = True
except ImportError:
    QGIS_AVAILABLE = False


# Plugin name for QGIS MessageLog
PLUGIN_NAME = "qBRA"


class QGISLogHandler(logging.Handler):
    """Custom logging handler that writes to QGIS MessageLog.
    
    This handler integrates Python's logging framework with QGIS's message
    display system, allowing logs to appear in the QGIS Log Messages panel.
    """
    
    def __init__(self, plugin_name: str = PLUGIN_NAME):
        """Initialize QGIS log handler.
        
        Args:
            plugin_name: Name to display in QGIS MessageLog
        """
        super().__init__()
        self.plugin_name = plugin_name
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to QGIS MessageLog.
        
        Args:
            record: Log record to emit
        """
        if not QGIS_AVAILABLE:
            return
        
        # Map Python logging levels to QGIS levels
        level_map = {
            logging.DEBUG: Qgis.Info,
            logging.INFO: Qgis.Info,
            logging.WARNING: Qgis.Warning,
            logging.ERROR: Qgis.Critical,
            logging.CRITICAL: Qgis.Critical,
        }
        
        qgis_level = level_map.get(record.levelno, Qgis.Info)
        message = self.format(record)
        
        try:
            QgsMessageLog.logMessage(message, self.plugin_name, qgis_level)
        except Exception:
            # Fallback to console if QGIS logging fails
            print(f"[{self.plugin_name}] {message}")


def setup_logger(
    name: str,
    level: int = logging.INFO,
    use_qgis: bool = True,
) -> logging.Logger:
    """Setup and configure a logger for the qBRA plugin.
    
    Creates a namespaced logger with appropriate handlers for QGIS integration.
    
    Args:
        name: Logger name (should be module path, e.g., "qBRA.dockwidgets.ils")
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_qgis: Whether to use QGIS MessageLog handler (True) or console (False)
        
    Returns:
        Configured logger instance
        
    Example:
        >>> logger = setup_logger("qBRA.modules.ils_llz_logic")
        >>> logger.info("Building BRA layers")
        >>> logger.debug("Processing feature %s", feature_id)
        >>> logger.error("Validation failed", exc_info=True)
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    logger.propagate = False
    
    # Choose handler based on QGIS availability and preference
    if use_qgis and QGIS_AVAILABLE:
        handler = QGISLogHandler(PLUGIN_NAME)
    else:
        handler = logging.StreamHandler()
    
    # Format with timestamp, level, and message
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger with default qBRA configuration.
    
    Convenience function for getting a logger without manual setup.
    
    Args:
        name: Logger name (typically __name__ from calling module)
        
    Returns:
        Configured logger instance
        
    Example:
        >>> # In your module
        >>> logger = get_logger(__name__)
        >>> logger.info("Operation completed successfully")
    """
    return setup_logger(name)
