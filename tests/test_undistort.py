import numpy as np

from camcal_sdk import Calibration, undistort


def test_pinhole_identity_like_calibration_returns_same_shape():
    image = np.zeros((32, 48, 3), dtype=np.uint8)
    image[8:24, 16:32] = 255
    calibration = Calibration.from_dict(
        {
            "camera_model": "pinhole",
            "image_width": 48,
            "image_height": 32,
            "camera_matrix": [[40, 0, 24], [0, 40, 16], [0, 0, 1]],
            "distortion_coefficients": [0, 0, 0, 0, 0],
        }
    )

    result = undistort(image, calibration, balance=0.5)

    assert result.image.shape == image.shape
    assert result.camera_matrix.shape == (3, 3)
    assert result.roi is not None
