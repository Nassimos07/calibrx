# CamCal SDK

Python SDK for applying CamCal calibration exports locally. Users can download
`calibration.json` or `rectified_calibration.json` from CamCal, install this
package, and reproduce the same undistortion results in their own scripts.

## Install

```bash
pip install camcal-sdk
```

For local development:

```bash
python -m pip install -e ".[dev]"
```

## Python usage

```python
from camcal_sdk import load_calibration, undistort_file

calibration = load_calibration("calibration.json")

undistort_file(
    "input.jpg",
    calibration,
    "output.jpg",
    balance=0.5,
)
```

For rectified exports, the saved rectification values are used by default:

```python
from camcal_sdk import undistort_file

undistort_file(
    "input.jpg",
    "rectified_calibration.json",
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
- `rectified_calibration.json`

It also accepts the deeper raw calibration payload shape produced by
`camcal-core`, as long as it contains `intrinsics.camera_matrix` and
`intrinsics.distortion_coefficients`.

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
