# CalibrX Export Format

The SDK primarily consumes the app-level export downloaded from CalibrX:

```json
{
  "format": "calibrx.calibration",
  "version": 1,
  "camera_model": "pinhole_wide",
  "pattern_type": "chessboard",
  "image_size": [1920, 1080],
  "intrinsics": {
    "camera_matrix": [[1000.0, 0.0, 960.0], [0.0, 1000.0, 540.0], [0.0, 0.0, 1.0]],
    "parameters": {
      "fx": 1000.0,
      "fy": 1000.0,
      "cx": 960.0,
      "cy": 540.0,
      "skew": 0.0
    },
    "distortion_model": "opencv_rational",
    "distortion_coefficients": [0.1, -0.02, 0.001, 0.002, 0.0, 0.01, -0.01, 0.002],
    "distortion_order": ["k1", "k2", "p1", "p2", "k3", "k4", "k5", "k6"],
    "distortion_parameters": {
      "k1": 0.1,
      "k2": -0.02,
      "p1": 0.001,
      "p2": 0.002,
      "k3": 0.0,
      "k4": 0.01,
      "k5": -0.01,
      "k6": 0.002
    }
  },
  "undistortion": {
    "engine": "calibrx-core",
    "balance": 0.5,
    "fov_scale": 1.0
  },
  "quality": {
    "rms_error": 0.368,
    "n_images_used": 56,
    "n_images_total": 60
  }
}
```

Rectified exports keep the same shape and store the tuned values in
`undistortion`:

```json
{
  "format": "calibrx.calibration",
  "version": 1,
  "camera_model": "fisheye",
  "image_size": [1920, 1080],
  "intrinsics": {
    "camera_matrix": [[...], [...], [...]],
    "parameters": {
      "fx": 1000.0,
      "fy": 1000.0,
      "cx": 960.0,
      "cy": 540.0,
      "skew": 0.0
    },
    "distortion_model": "opencv_fisheye",
    "distortion_coefficients": [...],
    "distortion_order": ["k1", "k2", "k3", "k4"],
    "distortion_parameters": {
      "k1": -0.01,
      "k2": 0.001,
      "k3": 0.0,
      "k4": 0.0
    }
  },
  "undistortion": {
    "engine": "calibrx-core",
    "balance": 0.5,
    "fov_scale": 1.0
  }
}
```

When `balance` or `fov_scale` are not provided by the caller, the SDK uses the
values saved in `undistortion`. Otherwise, it falls back to CalibrX defaults:
`balance=0.5` and `fov_scale=1.0`.

`camera_matrix` and `distortion_coefficients` are the canonical OpenCV-ready
values. The named `parameters` and `distortion_parameters` fields mirror the
same data so exports are easy to inspect, validate, and map into other tools.
