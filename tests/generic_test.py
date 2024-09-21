"""Test core functionality of generic classes."""

import pytest
import yaml

from ec_jrc_idees.generics import IDEESFile, IDEESSection, IDEESSheet


class Section(IDEESSection):
    """Dummy section functionality."""

    EXCEL_ROW_RANGE = (17, 56)
    NAME = "totalEnergyConsumption"

    def tidy_up(self):
        """Placehold of dummy process."""
        pass


class Sheet(IDEESSheet):
    """Dummy sheet functionality."""

    NAME = "TrRoad_ene"
    TARGET_SECTIONS = [Section]


class File(IDEESFile):
    """Dummy file functionality."""

    NAME = "Transport"
    TARGET_SHEETS = [Sheet]


@pytest.fixture
def path():
    """Path to arbitrary test files."""
    return "tests/files/JRC-IDEES-2021_Transport_DE.xlsx"


@pytest.fixture
def dummy_cnf():
    """Create a dummy configuration."""
    return yaml.safe_load(
        """
sheets:
  TrRoad_ene:
    prefix_cols:
      category:
      subcategory: "Road"
    sections:
      totalEnergyConsumption:
        prefix_cols:
"""
    )


@pytest.fixture
def file(path, dummy_cnf):
    """File object."""
    return File(path, dummy_cnf)


def test_file_loading(path, file):
    """Files should load the given path without failure."""
    assert file.excel.io == path


def test_generic_file_preparation(file: File, dummy_cnf):
    """File processing should trigger underlying sheet and section preparation."""
    file.prepare()
    cnf_dict = {
        sheet: [section for section in sheet_cnf["sections"]]
        for sheet, sheet_cnf in dummy_cnf["sheets"].items()
    }
    file_dict = {
        sheet_name: [section for section in sheet.dirty_sections]
        for sheet_name, sheet in file.dirty_sheets.items()
    }
    assert cnf_dict == file_dict
