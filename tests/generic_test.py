"""Test core functionality of generic classes."""

from typing import override

import pandas as pd
import pytest
import yaml
from ec_jrc_idees.generics import IDEESFile, IDEESSection, IDEESSheet

DUMMY_TIDY_DF = pd.DataFrame(True, columns=[1, 2, 3], index=[1, 2, 3])


class Section(IDEESSection):
    """Dummy section functionality."""

    EXCEL_ROW_RANGE = (17, 56)

    def tidy_up(self):
        """Placehold of dummy process."""
        self.tidy_df = DUMMY_TIDY_DF

    @override
    def check(self):
        return True


class Sheet(IDEESSheet):
    """Dummy sheet functionality."""

    SHEET_NAME = "TrRoad_ene"
    SECTION_CLEANERS = [Section]

    @override
    def check(self):
        return True


class File(IDEESFile):
    """Dummy file functionality."""

    SHEET_CLEANERS = [Sheet]

    @override
    def check(self):
        return True


@pytest.fixture()
def path():
    """Path to arbitrary test files."""
    return "tests/files/JRC-IDEES-2021_Transport_DE.xlsx"


@pytest.fixture()
def dummy_cnf():
    """Create a dummy configuration."""
    return yaml.safe_load(
        """
sheets:
  Sheet:
    prefix_cols:
      category:
      subcategory: "Road"
    sections:
      Section:
        prefix_cols:
"""
    )


@pytest.fixture()
def file(path, dummy_cnf):
    """File object."""
    return File(path, dummy_cnf)


def test_file_loading(path, file):
    """Files should load the given path without failure."""
    assert str(file.excel.io) == str(path)


def test_generic_file_preparation(file: File, dummy_cnf):
    """File processing should trigger underlying sheet and section preparation."""
    file.prepare()
    file.tidy_up()
    cnf_dict = {
        sheet: [section for section in sheet_cnf["sections"]]
        for sheet, sheet_cnf in dummy_cnf["sheets"].items()
    }
    file_dict = {
        sheet_name: [section for section in sheet]
        for sheet_name, sheet in file.tidy_sheets.items()
    }
    assert cnf_dict == file_dict
    assert DUMMY_TIDY_DF.equals(file.tidy_sheets[Sheet.__name__][Section.__name__])
