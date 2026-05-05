from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from camcal_sdk.calibration import Calibration, ensure_calibration


@dataclass(frozen=True)
class UndistortResult:
    image: np.ndarray
    camera_matrix: np.ndarray
    roi: tuple[int, int, int, int] | None = None


def undistort(
    image: np.ndarray,
    calibration: Calibration | Mapping | str | Path,
    *,
    balance: float | None = None,
    fov_scale: float | None = None,
) -> UndistortResult:
    """Apply a CamCal calibration export to an image.

    The implementation mirrors the backend/core OpenCV calls used by CamCal:
    pinhole models use `cv2.getOptimalNewCameraMatrix` + `cv2.undistort`,
    while fisheye models use `cv2.fisheye` rectification maps.
    """

    if image is None or not hasattr(image, "shape"):
        raise ValueError("image must be a numpy array loaded by OpenCV or an equivalent array.")

    parsed = ensure_calibration(calibration)
    balance = _resolve_balance(parsed, balance)
    fov_scale = _resolve_fov_scale(parsed, fov_scale)

    if not (0.0 <= balance <= 1.0):
        raise ValueError(f"balance must be in [0, 1], got {balance}.")
    if fov_scale <= 0:
        raise ValueError(f"fov_scale must be > 0, got {fov_scale}.")

    if parsed.camera_model == "fisheye":
        return _undistort_fisheye(image, parsed, balance=balance, fov_scale=fov_scale)
    if parsed.camera_model in {"pinhole", "pinhole_wide"}:
        return _undistort_pinhole(image, parsed, balance=balance)

    raise ValueError(f"Unsupported camera_model {parsed.camera_model!r}.")


def undistort_image(
    image: np.ndarray,
    calibration: Calibration | Mapping | str | Path,
    *,
    balance: float | None = None,
    fov_scale: float | None = None,
) -> np.ndarray:
    """Return only the undistorted image array."""

    return undistort(
        image,
        calibration,
        balance=balance,
        fov_scale=fov_scale,
    ).image


def undistort_file(
    image_path: str | Path,
    calibration: Calibration | Mapping | str | Path,
    output_path: str | Path,
    *,
    balance: float | None = None,
    fov_scale: float | None = None,
) -> Path:
    """Load, undistort, and save one image file."""

    source = Path(image_path)
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    image = cv2.imread(str(source))
    if image is None:
        raise ValueError(f"Failed to read image: {source}")

    result = undistort(
        image,
        calibration,
        balance=balance,
        fov_scale=fov_scale,
    )
    ok = cv2.imwrite(str(destination), result.image)
    if not ok:
        raise ValueError(f"Failed to write image: {destination}")
    return destination


def _undistort_pinhole(image: np.ndarray, calibration: Calibration, *, balance: float) -> UndistortResult:
    height, width = image.shape[:2]
    image_size = (width, height)

    new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
        calibration.K,
        calibration.D,
        image_size,
        balance,
        image_size,
    )
    output = cv2.undistort(image, calibration.K, calibration.D, None, new_camera_matrix)
    return UndistortResult(output, new_camera_matrix, tuple(int(v) for v in roi))


def _undistort_fisheye(
    image: np.ndarray,
    calibration: Calibration,
    *,
    balance: float,
    fov_scale: float,
) -> UndistortResult:
    height, width = image.shape[:2]
    current_size = (width, height)
    K = calibration.K
    D = calibration.D

    if D.shape != (4, 1):
        raise ValueError(f"Fisheye calibration expects 4 distortion coefficients, got shape {D.shape}.")

    if calibration.image_size and current_size != calibration.image_size:
        K = _scale_camera_matrix(K, calibration.image_size, current_size)

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
    output = cv2.remap(
        image,
        map_x,
        map_y,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
    )
    return UndistortResult(output, new_camera_matrix)


def _scale_camera_matrix(
    K: np.ndarray,
    from_size: tuple[int, int],
    to_size: tuple[int, int],
) -> np.ndarray:
    from_w, from_h = from_size
    to_w, to_h = to_size
    from_aspect = from_w / from_h
    to_aspect = to_w / to_h

    if abs(from_aspect - to_aspect) > 0.01:
        raise ValueError(
            f"Cannot undistort {to_w}x{to_h} with a calibration done at "
            f"{from_w}x{from_h}; aspect ratios differ."
        )

    scale_x = to_w / from_w
    scale_y = to_h / from_h
    scaled = K.copy()
    scaled[0, 0] *= scale_x
    scaled[1, 1] *= scale_y
    scaled[0, 2] *= scale_x
    scaled[1, 2] *= scale_y
    return scaled


def _resolve_balance(calibration: Calibration, value: float | None) -> float:
    if value is not None:
        return float(value)
    rectification_value = calibration.rectification.get("balance")
    return float(rectification_value) if rectification_value is not None else 0.5


def _resolve_fov_scale(calibration: Calibration, value: float | None) -> float:
    if value is not None:
        return float(value)
    rectification_value = calibration.rectification.get("fov_scale")
    return float(rectification_value) if rectification_value is not None else 1.0
