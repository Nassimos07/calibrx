class CalibrXError(Exception):
    """Base exception for CalibrX SDK errors."""


class CalibrationFormatError(CalibrXError, ValueError):
    """Raised when a CalibrX calibration export cannot be parsed."""


class UndistortionError(CalibrXError, ValueError):
    """Raised when an image cannot be undistorted with the provided calibration."""
