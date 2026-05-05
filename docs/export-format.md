# CamCal Export Format

The SDK primarily consumes the app-level export downloaded from CamCal:

```json
{
  "camera_model": "pinhole_wide",
  "image_width": 1920,
  "image_height": 1080,
  "rms_error": 0.368,
  "n_images_used": 56,
  "n_images_total": 60,
  "camera_matrix": [[...], [...], [...]],
  "distortion_coefficients": [...]
}
```

Rectified exports add a `rectification` object:

```json
{
  "camera_model": "fisheye",
  "camera_matrix": [[...], [...], [...]],
  "distortion_coefficients": [...],
  "rectification": {
    "model": "fisheye",
    "balance": 0.5,
    "fov_scale": 1.0
  }
}
```

When `balance` or `fov_scale` are not provided by the caller, the SDK uses the
values saved in `rectification`. Otherwise, it falls back to CamCal defaults:
`balance=0.5` and `fov_scale=1.0`.
