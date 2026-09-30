# Releasing

1. Confirm the working tree is clean apart from intended release changes and update `CHANGELOG.md`.
2. Run the supported Python test matrix locally where available:

   ```sh
   python3.11 -m pytest
   python3.12 -m pytest
   ```

3. Build and inspect both artifacts:

   ```sh
   python -m build
   python -m twine check dist/*
   ```

4. Fresh-install the wheel and sdist in separate temporary virtual environments, then run `agent-trace --help` and the checked-in demo.
5. Create a signed/tagged release through the repository's reviewed GitHub release process. Do not publish from an unreviewed checkout.

The GitHub Actions workflow is the source of truth for the Ubuntu/macOS Python 3.11/3.12 test matrix and package build checks.
