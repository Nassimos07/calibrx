from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from calibrx._opencv import undistort_fisheye_image, undistort_pinhole_image
from calibrx.calibration import Calibration, ensure_calibration


@dataclass(frozen=True)
class UndistortResult:
    """Result returned by :func:`calibrx.undistort`.

    Attributes:
        image: Undistorted OpenCV/Numpy image array.
        camera_matrix: New camera matrix used for the output image.
        roi: OpenCV valid-pixel ROI for pinhole models. Fisheye outputs use
            `None` because OpenCV's fisheye path does not return an ROI.
        output_path: Written file path when `output_path` was provided.
    """

    image: np.ndarray
    camera_matrix: np.ndarray
    roi: tuple[int, int, int, int] | None = None
    output_path: Path | None = None


def undistort(
    image: np.ndarray | str | Path,
    calibration: Calibration | Mapping[str, Any] | str | Path,
    output_path: str | Path | None = None,
    *,
    balance: float | None = None,
    fov_scale: float | None = None,
) -> UndistortResult:
    """Apply a CalibrX export to an image.

    `image` can be either an OpenCV/Numpy image array or a file path. When
    `output_path` is provided, the undistorted image is also written to disk.
    The camera model, pattern type, balance, and fisheye FOV scale are resolved
    from the calibration export unless the caller explicitly overrides them.
    """

    parsed = ensure_calibration(calibration)
    source_image = _load_image(image)
    resolved_balance = parsed.balance if balance is None else float(balance)
    resolved_fov_scale = parsed.fov_scale if fov_scale is None else float(fov_scale)

    output, new_camera_matrix, roi = _run_undistort(
        source_image,
        parsed,
        balance=resolved_balance,
        fov_scale=resolved_fov_scale,
    )
    saved_path = _write_image(output, output_path) if output_path is not None else None
    return UndistortResult(output, new_camera_matrix, roi, saved_path)


def undistort_image(
    image: np.ndarray | str | Path,
    calibration: Calibration | Mapping[str, Any] | str | Path,
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
    calibration: Calibration | Mapping[str, Any] | str | Path,
    output_path: str | Path,
    *,
    balance: float | None = None,
    fov_scale: float | None = None,
) -> Path:
    """Load, undistort, and save one image file."""

    result = undistort(
        image_path,
        calibration,
        output_path,
        balance=balance,
        fov_scale=fov_scale,
    )
    if result.output_path is None:
        raise ValueError("The undistorted image was not written.")
    return result.output_path


def _run_undistort(
    image: np.ndarray,
    calibration: Calibration,
    *,
    balance: float,
    fov_scale: float,
) -> tuple[np.ndarray, np.ndarray, tuple[int, int, int, int] | None]:
    if calibration.camera_model == "fisheye":
        output, new_camera_matrix = undistort_fisheye_image(
            image,
            calibration.K,
            calibration.D,
            calibration_image_size=calibration.image_size,
            balance=balance,
            fov_scale=fov_scale,
        )
        return output, new_camera_matrix, None

    if calibration.camera_model in {"pinhole", "pinhole_wide"}:
        output, new_camera_matrix, roi = undistort_pinhole_image(
            image,
            calibration.K,
            calibration.D,
            balance=balance,
        )
        return output, new_camera_matrix, roi

    raise ValueError(f"Unsupported camera_model {calibration.camera_model!r}.")


def _load_image(image: np.ndarray | str | Path) -> np.ndarray:
    if isinstance(image, np.ndarray):
        return image

    source = Path(image)
    loaded = cv2.imread(str(source))
    if loaded is None:
        raise ValueError(f"Failed to read image: {source}")
    return loaded


def _write_image(image: np.ndarray, output_path: str | Path) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(destination), image)
    if not ok:
        raise ValueError(f"Failed to write image: {destination}")
    return destination
