from __future__ import annotations

import cv2
import numpy as np

from calibrx.exceptions import UndistortionError


def undistort_pinhole_image(
    image: np.ndarray,
    camera_matrix: np.ndarray,
    distortion_coefficients: np.ndarray,
    *,
    balance: float = 0.5,
) -> tuple[np.ndarray, np.ndarray, tuple[int, int, int, int]]:
    """Undistort a pinhole or rational pinhole image.

    This mirrors the CalibrX platform behavior for both `pinhole` and
    `pinhole_wide` exports: OpenCV chooses the output camera matrix from the
    requested crop/FOV balance, then remaps with the exported distortion vector.
    """

    _validate_balance(balance)
    K = _camera_matrix(camera_matrix)
    D = _distortion_coefficients(distortion_coefficients)

    height, width = image.shape[:2]
    image_size = (width, height)

    new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(K, D, image_size, balance, image_size)
    undistorted = cv2.undistort(image, K, D, None, new_camera_matrix)
    return undistorted, new_camera_matrix, tuple(int(value) for value in roi)


def undistort_fisheye_image(
    image: np.ndarray,
    camera_matrix: np.ndarray,
    distortion_coefficients: np.ndarray,
    *,
    calibration_image_size: tuple[int, int] | None = None,
    balance: float = 0.5,
    fov_scale: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Undistort an OpenCV fisheye image.

    If the input resolution differs from the calibration resolution but keeps
    the same aspect ratio, the camera matrix is scaled before undistortion.
    """

    _validate_balance(balance)
    _validate_fov_scale(fov_scale)

    K = _camera_matrix(camera_matrix)
    D = _distortion_coefficients(distortion_coefficients)
    if D.shape != (4, 1):
        raise UndistortionError(f"Expected 4 fisheye distortion coefficients, got shape {D.shape}.")

    height, width = image.shape[:2]
    current_size = (width, height)
    if calibration_image_size and current_size != calibration_image_size:
        K = _scale_camera_matrix(K, calibration_image_size, current_size)

    new_camera_matrix = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(
        K,
        D,
        current_size,
        np.eye(3),
        balance=balance,
        fov_scale=fov_scale,
    )
    map_x, map_y = cv2.fisheye.initUndistortRectifyMap(
        K,
        D,
        np.eye(3),
        new_camera_matrix,
        current_size,
        cv2.CV_16SC2,
    )
    undistorted = cv2.remap(
        image,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
    )
    return undistorted, new_camera_matrix


def _scale_camera_matrix(
    camera_matrix: np.ndarray,
    from_size: tuple[int, int],
    to_size: tuple[int, int],
) -> np.ndarray:
    from_w, from_h = from_size
    to_w, to_h = to_size

    from_aspect = from_w / from_h
    to_aspect = to_w / to_h
    if abs(from_aspect - to_aspect) > 0.01:
        raise UndistortionError(
            f"Cannot undistort {to_w}x{to_h} (aspect {to_aspect:.3f}) with a "
            f"calibration done at {from_w}x{from_h} (aspect {from_aspect:.3f}). "
            "Different aspect ratios would produce geometrically invalid results."
        )

    scale_x = to_w / from_w
    scale_y = to_h / from_h

    scaled = camera_matrix.copy()
    scaled[0, 0] *= scale_x
    scaled[1, 1] *= scale_y
    scaled[0, 2] *= scale_x
    scaled[1, 2] *= scale_y
    return scaled


def _camera_matrix(value: np.ndarray) -> np.ndarray:
    matrix = np.asarray(value, dtype=np.float64)
    if matrix.shape != (3, 3):
        raise UndistortionError(f"Expected camera matrix shape (3, 3), got {matrix.shape}.")
    return matrix


def _distortion_coefficients(value: np.ndarray) -> np.ndarray:
    coefficients = np.asarray(value, dtype=np.float64).reshape(-1, 1)
    if coefficients.size == 0:
        raise UndistortionError("Distortion coefficients must not be empty.")
    return coefficients


def _validate_balance(value: float) -> None:
    if not (0.0 <= value <= 1.0):
        raise ValueError(f"balance must be in [0, 1], got {value}")


def _validate_fov_scale(value: float) -> None:
    if value <= 0:
        raise ValueError(f"fov_scale must be > 0, got {value}")
