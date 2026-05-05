# CamCal SDK

Python SDK for applying CamCal calibration exports locally. Users download
`calibration.json`, `calibration.yaml`, `rectified_calibration.json`, or
`rectified_calibration.yaml` from CamCal and call one undistortion function.

The SDK delegates undistortion to `camcal-core`, the same engine used by the
CamCal backend, so local results follow the platform implementation.

## Install

```bash
pip install camcal-sdk
```

For local development:

```bash
python -m pip install -e ../camcal-core
python -m pip install -e ".[dev]"
```

## Python usage

```python
from camcal_sdk import undistort_file

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
from camcal_sdk import load_calibration, undistort

image = cv2.imread("input.jpg")
calibration = load_calibration("calibration.json")

result = undistort(image, calibration)
cv2.imwrite("output.jpg", result.image)
print(result.camera_matrix)
```

## CLI usage

```bash
camcal-undistort input.jpg calibration.json output.jpg --balance 0.5
```

For fisheye calibrations:

```bash
camcal-undistort input.jpg calibration.json output.jpg --balance 0.5 --fov-scale 1.0
```

Batch a directory:

```bash
camcal-undistort ./frames calibration.json ./undistorted --glob "*.jpg"
```

## Supported exports

The SDK supports the CamCal app exports:

- `calibration.json`
- `calibration.yaml`
- `rectified_calibration.json`
- `rectified_calibration.yaml`

It also accepts the older flat export shape and the deeper raw calibration
payload shape produced by `camcal-core`, as long as camera intrinsics are
present.

Supported camera models:

- `pinhole`
- `pinhole_wide`
- `fisheye`

## Publishing

This repo is ready for public GitHub + PyPI:

1. Create a public GitHub repository named `camcal-sdk`.
2. Push this local repo to it.
3. Configure PyPI trusted publishing for the GitHub release workflow.
4. Create a GitHub release tag like `v0.1.0`.

The package build is handled by:

```bash
python -m build
```
