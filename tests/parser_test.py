"""Test main functionality."""

from pathlib import Path

from ec_jrc_idees.parser import EasyIDEES


def test_zip_download(zip_path: Path):
    """Zip file should be created successfully."""
    assert zip_path.exists()

def test_unzip(easy_idees: EasyIDEES, country_path: Path):
    """Unzipped files should be excels with the right versioning."""
    unzipped_files = [path for path in country_path.iterdir() if path.is_file()]
    assert all([".xlsx" in file.name for file in unzipped_files])
    assert all([str(easy_idees.version) in file.name for file in unzipped_files ])
