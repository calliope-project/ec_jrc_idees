"""Set up the testing environment."""

import shutil
from pathlib import Path

import pytest

from ec_jrc_idees.parser import EasyIDEES


@pytest.fixture(params=[2021, 2015], scope="session")
def version(request) -> int:
    """Dataset version to parse."""
    return request.param


@pytest.fixture(scope="session")
def easy_idees(version: int) -> EasyIDEES:
    """Construct a parser per dataset year."""
    easy = EasyIDEES(version)
    return easy


@pytest.fixture(params=["DE"], scope="session")
def country(request) -> str:
    """Select the country to process."""
    return request.param


@pytest.fixture(scope="session")
def zip_path(easy_idees: EasyIDEES, country: str):
    """Download zip file for this country and version."""
    version = easy_idees.version
    zipfile = Path(f"tmp/v{version}/idees_{country}.zip")

    zipfile.unlink(missing_ok=True)
    zipfile.parent.mkdir(exist_ok=True)

    easy_idees.download_country(country, zipfile, overwrite=True)
    return zipfile


@pytest.fixture(scope="session")
def country_path(easy_idees: EasyIDEES, zip_path: Path, country: str) -> Path:
    """Folder where all country files are placed."""
    country_dir = zip_path.parent / f"{country}"

    # Delete country files and re-download to make testing comprehensive
    if country_dir.exists():
        shutil.rmtree(country_dir.resolve())

    easy_idees.unzip(zip_path, country_dir)

    return country_dir
