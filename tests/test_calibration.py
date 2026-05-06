import numpy as np
import pytest

from calibrx import Calibration, CalibrationFormatError


def test_loads_app_export_shape():
    calibration = Calibration.from_dict(
        {
            "format": "calibrx.calibration",
            "version": 1,
            "camera_model": "pinhole_wide",
            "image_size": [1920, 1080],
            "intrinsics": {
                "camera_matrix": [[1000, 0, 960], [0, 1000, 540], [0, 0, 1]],
                "distortion_coefficients": [0.1, -0.02, 0.001, 0.002, 0.0],
            },
            "undistortion": {"balance": 0.25, "fov_scale": 1.0},
            "quality": {
                "rms_error": 0.368,
                "n_images_used": 56,
                "n_images_total": 60,
            },
        }
    )

    assert calibration.camera_model == "pinhole_wide"
    assert calibration.image_size == (1920, 1080)
    assert calibration.rms_error == pytest.approx(0.368)
    assert calibration.balance == pytest.approx(0.25)
    assert calibration.K.shape == (3, 3)
    assert calibration.D.shape == (5, 1)


def test_loads_raw_core_payload_shape():
    calibration = Calibration.from_dict(
        {
            "camera_model": "fisheye",
            "pattern_type": "chessboard",
            "intrinsics": {
                "camera_matrix": [[500, 0, 320], [0, 500, 240], [0, 0, 1]],
                "distortion_coefficients": [-0.1, 0.01, 0.0, 0.0],
            },
            "calibration_summary": {
                "image_size": [640, 480],
                "rms_error": 0.42,
                "n_images_used": 12,
            },
        }
    )

    assert calibration.camera_model == "fisheye"
    assert calibration.pattern_type == "chessboard"
    assert calibration.image_size == (640, 480)
    assert calibration.D.shape == (4, 1)


def test_missing_matrix_is_clear_error():
    with pytest.raises(CalibrationFormatError, match="Missing camera_matrix"):
        Calibration.from_dict(
            {
                "camera_model": "pinhole",
                "distortion_coefficients": [0.0, 0.0, 0.0, 0.0],
            }
        )


def test_matrix_shape_is_validated():
    with pytest.raises(CalibrationFormatError, match="Expected camera_matrix shape"):
        Calibration.from_dict(
            {
                "camera_model": "pinhole",
                "camera_matrix": np.eye(2).tolist(),
                "distortion_coefficients": [0.0, 0.0, 0.0, 0.0],
            }
        )
