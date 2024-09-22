"""Test main functionality."""

import pytest
from ec_jrc_idees import parser


@pytest.fixture(params=[2021, 2015])
def easy(request):
    """Construct a parser per dataset year."""
    return parser.EasyIDEES(request.param)


@pytest.fixture(params=["DE"])
def downloaded_file(request, easy, tmp_path):
    """Download a country for each dataset version."""
    file = tmp_path / "test.zip"
    easy.download_country(request.param, file)
    return file


@pytest.fixture()
def unzipped_files(easy, downloaded_file, tmp_path):
    """Unzip dataset versions."""
    easy.unzip(downloaded_file, tmp_path)
    return tmp_path


def test_download(downloaded_file):
    """Country downloads should work as expected."""
    assert downloaded_file.exists()


def test_unzip(unzipped_files):
    """Unzipping should work as expected."""
    assert unzipped_files.iterdir() is not None
