# CalibrX

Python SDK for applying CalibrX calibration exports locally. Users download
`calibration.json`, `calibration.yaml`, `rectified_calibration.json`, or
`rectified_calibration.yaml` from CalibrX and call one undistortion function.

The SDK delegates undistortion to `calibrx-core`, the same engine used by the
CalibrX backend, so local results follow the platform implementation.

## Install

```bash
pip install calibrx
```

For local development:

```bash
python -m pip install -e ../camcal-core  # local source for calibrx-core
python -m pip install -e ".[dev]"
```

## Python usage

```python
from calibrx import undistort_file

undistort_file(
    "input.jpg",
    "calibration.json",
    "output.jpg",
)
```

The export decides the model, pattern type, balance, and fisheye FOV scale:

```python
undistort_file(
    "input.jpg",
    "rectified_calibration.yaml",
    "rectified_output.jpg",
)
```

For in-memory OpenCV/Numpy workflows:

```python
import cv2
from calibrx import load_calibration, undistort

image = cv2.imread("input.jpg")
calibration = load_calibration("calibration.json")

result = undistort(image, calibration)
cv2.imwrite("output.jpg", result.image)
print(result.camera_matrix)
```

## CLI usage

```bash
calibrx undistort input.jpg calibration.json output.jpg --balance 0.5
```

For fisheye calibrations:

```bash
calibrx undistort input.jpg calibration.json output.jpg --balance 0.5 --fov-scale 1.0
```

Batch a directory:

```bash
calibrx undistort ./frames calibration.json ./undistorted --glob "*.jpg"
```

## Supported exports

The SDK supports the CalibrX app exports:

- `calibration.json`
- `calibration.yaml`
- `rectified_calibration.json`
- `rectified_calibration.yaml`

It also accepts the older flat export shape and the deeper raw calibration
payload shape produced by `calibrx-core`, as long as camera intrinsics are
present.

Supported camera models:

- `pinhole`
- `pinhole_wide`
- `fisheye`

## Publishing

This repo is ready for public GitHub + PyPI:

1. Create a public GitHub repository named `calibrx`.
2. Push this local repo to it.
3. Configure PyPI trusted publishing for the GitHub release workflow.
4. Create a GitHub release tag like `v0.1.0`.

The package build is handled by:

```bash
python -m build
```
