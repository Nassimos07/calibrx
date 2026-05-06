from __future__ import annotations

import argparse
from pathlib import Path

from calibrx.calibration import load_calibration
from calibrx.undistort import undistort_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="calibrx",
        description="CalibrX command line tools.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    undistort_parser = subparsers.add_parser(
        "undistort",
        help="Apply a CalibrX calibration export to an image or directory.",
        description="Apply a CalibrX calibration export to an image or directory.",
    )
    _add_undistort_args(undistort_parser)

    args = parser.parse_args(argv)
    if args.command == "undistort":
        return _run_undistort(args)

    parser.error(f"Unknown command: {args.command}")
    return 2


def _add_undistort_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("input", help="Input image path or directory.")
    parser.add_argument("calibration", help="CalibrX calibration.json or rectified_calibration.json.")
    parser.add_argument("output", help="Output image path or directory.")
    parser.add_argument("--balance", type=float, default=None, help="Crop/FOV trade-off in [0, 1].")
    parser.add_argument("--fov-scale", type=float, default=None, help="Fisheye FOV scale. Default: export value or 1.0.")
    parser.add_argument("--glob", default="*.jpg", help="Input glob when input is a directory. Default: *.jpg")


def _run_undistort(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)
    calibration = load_calibration(args.calibration)

    if input_path.is_dir():
        output_path.mkdir(parents=True, exist_ok=True)
        images = sorted(path for path in input_path.glob(args.glob) if path.is_file())
        if not images:
            raise SystemExit(f"No files matched {args.glob!r} in {input_path}.")
        for image in images:
            saved = undistort_file(
                image,
                calibration,
                output_path / image.name,
                balance=args.balance,
                fov_scale=args.fov_scale,
            )
            print(saved)
        return 0

    saved = undistort_file(
        input_path,
        calibration,
        output_path,
        balance=args.balance,
        fov_scale=args.fov_scale,
    )
    print(saved)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
