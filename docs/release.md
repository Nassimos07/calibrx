# Release Checklist

Maintainer notes for publishing CalibrX.

1. Create or update the public GitHub repository.
2. Push the latest `main` branch.
3. Configure PyPI trusted publishing for the GitHub release workflow.
4. Run the local test suite:

   ```bash
   python -m pytest
   ```

5. Build the package:

   ```bash
   python -m build
   ```

6. Validate the distribution files:

   ```bash
   python -m twine check dist/*
   ```

7. Publish to TestPyPI first.
8. Install from TestPyPI in a clean environment and run a real undistortion.
9. Publish to PyPI.
