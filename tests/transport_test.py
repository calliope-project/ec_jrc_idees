"""Test Transport parsing."""

from pathlib import Path

import pandas as pd
import pytest
import yaml

from ec_jrc_idees.transport import TransportFile


@pytest.fixture
def cnf():
    """Config."""
    return yaml.safe_load(Path("src/ec_jrc_idees/data/Transport.yaml").read_text())


@pytest.fixture(params=["tests/files/JRC-IDEES-2021_Transport_DE.xlsx"])
def file(request, cnf):
    """Test Transport file versions."""
    return TransportFile(request.param, cnf)


def test_tidy_transport(file):
    """Transport sheets and sections should process correctly."""
    file.prepare()
    file.tidy_up()
    assert all(
        isinstance(file.tidy_sheets[sheet][section], pd.DataFrame)
        for sheet, sections in file.tidy_sheets.items()
        for section in sections
    )
