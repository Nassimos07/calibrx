from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import yaml


class CalibrationFormatError(ValueError):
    """Raised when a CalibrX calibration export cannot be parsed."""


_MODEL_ALIASES = {
    "pinhole": "pinhole",
    "pinhole-wide": "pinhole_wide",
    "pinhole_wide": "pinhole_wide",
    "pinhole wide": "pinhole_wide",
    "fisheye": "fisheye",
}


@dataclass(frozen=True)
class Calibration:
    """Parsed CalibrX calibration export.

    The class keeps the OpenCV-ready arrays (`camera_matrix`,
    `distortion_coefficients`) alongside the original export metadata.
    """

    camera_matrix: np.ndarray
    distortion_coefficients: np.ndarray
    camera_model: str
    image_size: tuple[int, int] | None = None
    pattern_type: str | None = None
    rms_error: float | None = None
    n_images_used: int | None = None
    n_images_total: int | None = None
    square_size: float | None = None
    undistortion: Mapping[str, Any] = field(default_factory=dict)
    rectification: Mapping[str, Any] = field(default_factory=dict)
    raw: Mapping[str, Any] = field(default_factory=dict, repr=False)

    @property
    def K(self) -> np.ndarray:
        return self.camera_matrix

    @property
    def D(self) -> np.ndarray:
        return self.distortion_coefficients

    @classmethod
    def from_file(cls, path: str | Path) -> "Calibration":
        payload = _load_mapping_file(path)
        return cls.from_dict(payload)

    @classmethod
    def from_json(cls, value: str | bytes | bytearray) -> "Calibration":
        return cls.from_dict(json.loads(value))

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> "Calibration":
        if not isinstance(payload, Mapping):
            raise CalibrationFormatError("Calibration payload must be a JSON object.")

        candidates = list(_candidate_payloads(payload))
        matrix = _first_matrix(candidates)
        distortion = _first_distortion(candidates)
        camera_model = _first_string(candidates, "camera_model", "model")

        rectification = _first_mapping(candidates, "rectification") or {}
        undistortion = _first_mapping(candidates, "undistortion") or rectification
        if not camera_model:
            camera_model = _string_from_mapping(undistortion, "model")
        if not camera_model:
            camera_model = _string_from_mapping(rectification, "model")
        camera_model = _normalize_camera_model(camera_model)

        image_size = _first_image_size(candidates)
        summary = _first_mapping(candidates, "calibration_summary") or {}
        rms_error = _first_float(candidates, "rms_error")
        n_images_used = _first_int(candidates, "n_images_used")
        n_images_total = _first_int(candidates, "n_images_total")

        return cls(
            camera_matrix=matrix,
            distortion_coefficients=distortion,
            camera_model=camera_model,
            image_size=image_size,
            pattern_type=_first_string(candidates, "pattern_type"),
            rms_error=rms_error if rms_error is not None else _float_from_mapping(summary, "rms_error"),
            n_images_used=n_images_used if n_images_used is not None else _int_from_mapping(summary, "n_images_used"),
            n_images_total=n_images_total if n_images_total is not None else _int_from_mapping(summary, "n_images_total"),
            square_size=_first_float(candidates, "square_size"),
            undistortion=dict(undistortion),
            rectification=dict(rectification),
            raw=payload,
        )

    def to_core_calibration(self) -> dict[str, Any]:
        """Return the calibration dictionary expected by `calibrx-core`."""

        payload: dict[str, Any] = {
            "camera_model": self.camera_model,
            "pattern_type": self.pattern_type,
            "K": self.K.copy(),
            "D": self.D.copy(),
            "rms_error": self.rms_error,
            "image_size": self.image_size,
            "n_images_used": self.n_images_used,
            "n_images_total": self.n_images_total,
            "square_size": self.square_size,
        }
        return {key: value for key, value in payload.items() if value is not None}

    @property
    def balance(self) -> float:
        return _first_config_float(self.undistortion, self.rectification, key="balance", default=0.5)

    @property
    def fov_scale(self) -> float:
        return _first_config_float(self.undistortion, self.rectification, key="fov_scale", default=1.0)


def load_calibration(path: str | Path) -> Calibration:
    """Load a CalibrX `calibration.json` or `rectified_calibration.json` export."""

    return Calibration.from_file(path)


def ensure_calibration(value: Calibration | Mapping[str, Any] | str | Path) -> Calibration:
    if isinstance(value, Calibration):
        return value
    if isinstance(value, Mapping):
        return Calibration.from_dict(value)
    return Calibration.from_file(value)


def _candidate_payloads(payload: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    candidates: list[Mapping[str, Any]] = [payload]
    for key in ("calibration", "payload", "result", "intrinsics", "quality"):
        nested = payload.get(key)
        if isinstance(nested, Mapping):
            candidates.append(nested)

    for candidate in list(candidates):
        intrinsics = candidate.get("intrinsics")
        if isinstance(intrinsics, Mapping):
            candidates.append(intrinsics)
    return candidates


def _load_mapping_file(path: str | Path) -> Mapping[str, Any]:
    source = Path(path)
    content = source.read_text(encoding="utf-8")
    suffix = source.suffix.lower()

    if suffix in {".yaml", ".yml"}:
        payload = yaml.safe_load(content)
    else:
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            payload = yaml.safe_load(content)

    if not isinstance(payload, Mapping):
        raise CalibrationFormatError(f"Calibration file must contain an object: {source}")
    return payload


def _first_matrix(candidates: list[Mapping[str, Any]]) -> np.ndarray:
    for candidate in candidates:
        value = candidate.get("camera_matrix")
        if value is None:
            value = candidate.get("K")
        if value is None:
            continue
        matrix = np.asarray(value, dtype=np.float64)
        if matrix.shape != (3, 3):
            raise CalibrationFormatError(f"Expected camera_matrix shape (3, 3), got {matrix.shape}.")
        return matrix
    raise CalibrationFormatError("Missing camera_matrix in calibration export.")


def _first_distortion(candidates: list[Mapping[str, Any]]) -> np.ndarray:
    keys = ("distortion_coefficients", "dist_coeffs", "distortion", "D")
    for candidate in candidates:
        for key in keys:
            value = candidate.get(key)
            if value is None:
                continue
            coefficients = np.asarray(value, dtype=np.float64).reshape(-1, 1)
            if coefficients.size == 0:
                raise CalibrationFormatError("distortion_coefficients must not be empty.")
            return coefficients
    raise CalibrationFormatError("Missing distortion_coefficients in calibration export.")


def _normalize_camera_model(value: str | None) -> str:
    if not value:
        raise CalibrationFormatError("Missing camera_model in calibration export.")
    normalized = _MODEL_ALIASES.get(value.strip().lower())
    if not normalized:
        supported = ", ".join(sorted(set(_MODEL_ALIASES.values())))
        raise CalibrationFormatError(f"Unsupported camera_model {value!r}. Supported models: {supported}.")
    return normalized


def _first_image_size(candidates: list[Mapping[str, Any]]) -> tuple[int, int] | None:
    for candidate in candidates:
        width = _int_from_mapping(candidate, "image_width") or _int_from_mapping(candidate, "width")
        height = _int_from_mapping(candidate, "image_height") or _int_from_mapping(candidate, "height")
        if width and height:
            return width, height

        size = candidate.get("image_size")
        parsed = _parse_image_size(size)
        if parsed:
            return parsed

        size = candidate.get("sensor_size")
        parsed = _parse_image_size(size)
        if parsed:
            return parsed

        summary = candidate.get("calibration_summary")
        if isinstance(summary, Mapping):
            parsed = _parse_image_size(summary.get("image_size"))
            if parsed:
                return parsed
    return None


def _parse_image_size(value: Any) -> tuple[int, int] | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        width = _int_from_mapping(value, "width") or _int_from_mapping(value, "image_width")
        height = _int_from_mapping(value, "height") or _int_from_mapping(value, "image_height")
        if width and height:
            return width, height
        return None
    if isinstance(value, (list, tuple)) and len(value) >= 2:
        width = int(value[0])
        height = int(value[1])
        if width > 0 and height > 0:
            return width, height
    return None


def _first_mapping(candidates: list[Mapping[str, Any]], key: str) -> Mapping[str, Any] | None:
    for candidate in candidates:
        value = candidate.get(key)
        if isinstance(value, Mapping):
            return value
    return None


def _first_string(candidates: list[Mapping[str, Any]], *keys: str) -> str | None:
    for candidate in candidates:
        for key in keys:
            value = _string_from_mapping(candidate, key)
            if value:
                return value
    return None


def _first_float(candidates: list[Mapping[str, Any]], key: str) -> float | None:
    for candidate in candidates:
        value = _float_from_mapping(candidate, key)
        if value is not None:
            return value
    return None


def _first_int(candidates: list[Mapping[str, Any]], key: str) -> int | None:
    for candidate in candidates:
        value = _int_from_mapping(candidate, key)
        if value is not None:
            return value
    return None


def _string_from_mapping(mapping: Mapping[str, Any], key: str) -> str | None:
    value = mapping.get(key)
    return value if isinstance(value, str) and value.strip() else None


def _float_from_mapping(mapping: Mapping[str, Any], key: str) -> float | None:
    value = mapping.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_from_mapping(mapping: Mapping[str, Any], key: str) -> int | None:
    value = mapping.get(key)
    if value is None:
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _first_config_float(*mappings: Mapping[str, Any], key: str, default: float) -> float:
    for mapping in mappings:
        value = _float_from_mapping(mapping, key)
        if value is not None:
            return value
    return default
