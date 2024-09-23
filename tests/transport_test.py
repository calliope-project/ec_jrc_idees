"""Test Transport parsing."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from ec_jrc_idees.transport import TransportFile


@pytest.fixture
def transport_cnf() -> dict:
    """Get internal transport configuration."""
    return yaml.safe_load(Path("src/ec_jrc_idees/config/Transport.yaml").read_text())


@pytest.fixture
def transport_file(country_path, country, version) -> Path:
    """Get stable transport filepath."""
    return country_path / f"JRC-IDEES-{version}_Transport_{country}.xlsx"


@pytest.fixture
def file(transport_file, transport_cnf):
    """Enable transport file testing."""
    return TransportFile(transport_file, transport_cnf)


def test_tidy_transport(file):
    """Configured transport sheets and sections should process correctly."""
    file.tidy_up()
    assert all(
        isinstance(file.tidy_sheets[sheet][section], pd.DataFrame)
        for sheet, sections in file.tidy_sheets.items()
        for section in sections
    )
