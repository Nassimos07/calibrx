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
                "parameters": {
                    "fx": 1000,
                    "fy": 1000,
                    "cx": 960,
                    "cy": 540,
                    "skew": 0,
                },
                "distortion_model": "opencv_pinhole",
                "distortion_coefficients": [0.1, -0.02, 0.001, 0.002, 0.0],
                "distortion_order": ["k1", "k2", "p1", "p2", "k3"],
                "distortion_parameters": {
                    "k1": 0.1,
                    "k2": -0.02,
                    "p1": 0.001,
                    "p2": 0.002,
                    "k3": 0.0,
                },
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


def test_loads_named_intrinsics_without_matrix_or_vector():
    calibration = Calibration.from_dict(
        {
            "format": "calibrx.calibration",
            "version": 1,
            "camera_model": "pinhole_wide",
            "image_size": [1920, 1080],
            "intrinsics": {
                "parameters": {
                    "fx": 1000,
                    "fy": 1001,
                    "cx": 960,
                    "cy": 540,
                    "skew": 0,
                },
                "distortion_model": "opencv_rational",
                "distortion_order": ["k1", "k2", "p1", "p2", "k3", "k4", "k5", "k6"],
                "distortion_parameters": {
                    "k1": 0.1,
                    "k2": -0.02,
                    "p1": 0.001,
                    "p2": 0.002,
                    "k3": 0.0,
                    "k4": 0.01,
                    "k5": -0.01,
                    "k6": 0.002,
                },
            },
        }
    )

    assert calibration.K.tolist() == [[1000, 0, 960], [0, 1001, 540], [0, 0, 1]]
    assert calibration.D.reshape(-1).tolist() == pytest.approx([0.1, -0.02, 0.001, 0.002, 0.0, 0.01, -0.01, 0.002])


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
