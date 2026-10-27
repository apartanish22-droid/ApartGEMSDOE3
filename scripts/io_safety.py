"""Small safeguards for JSON reports; these do not authorize a raster."""
from pathlib import Path


def validate_output_path(output: Path, protected: tuple[Path, ...]) -> None:
    """Reject non-JSON reports and paths, symlinks, or hardlinks to input files."""
    if output.suffix.lower() != ".json":
        raise ValueError("Diagnostic output must have a .json extension")
    for path in protected:
        if output.resolve() == path.resolve():
            raise ValueError("Diagnostic output must not overwrite an input")
        if output.exists() and path.exists() and output.samefile(path):
            raise ValueError("Diagnostic output must not be a hardlink to an input")
