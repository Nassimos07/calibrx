# CamCal Export Format

The SDK primarily consumes the app-level export downloaded from CamCal:

```json
{
  "format": "camcal.calibration",
  "version": 1,
  "camera_model": "pinhole_wide",
  "pattern_type": "chessboard",
  "image_size": [1920, 1080],
  "intrinsics": {
    "camera_matrix": [[...], [...], [...]],
    "distortion_coefficients": [...]
  },
  "undistortion": {
    "engine": "camcal-core",
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
  "format": "camcal.calibration",
  "version": 1,
  "camera_model": "fisheye",
  "image_size": [1920, 1080],
  "intrinsics": {
    "camera_matrix": [[...], [...], [...]],
    "distortion_coefficients": [...]
  },
  "undistortion": {
    "engine": "camcal-core",
    "balance": 0.5,
    "fov_scale": 1.0
  }
}
```

When `balance` or `fov_scale` are not provided by the caller, the SDK uses the
values saved in `undistortion`. Otherwise, it falls back to CamCal defaults:
`balance=0.5` and `fov_scale=1.0`.
