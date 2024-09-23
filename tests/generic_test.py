"""Test core functionality of generic classes."""

from pathlib import Path
from typing import override  # type:ignore

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
    def specific_check(self):
        pass

    @override
    def generic_check(self):
        pass

    @override
    def prettify(self) -> None:
        pass


class Sheet(IDEESSheet):
    """Dummy sheet functionality."""

    SHEET_NAME = "TrRoad_ene"
    SECTION_CLEANERS = [Section]

    @override
    def check(self):
        pass


class File(IDEESFile):
    """Dummy file functionality."""

    SHEET_CLEANERS = [Sheet]

    @override
    def check(self):
        pass


@pytest.fixture
def dummy_file_path(country_path, easy_idees) -> Path:
    """Path to arbitrary test files."""
    return country_path / f"JRC-IDEES-{easy_idees.version}_Transport_DE.xlsx"


@pytest.fixture
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


@pytest.fixture
def dummy_cleaner(dummy_file_path, dummy_cnf):
    """Contains 'fake' cleaning sequence, for simple execution tests."""
    return File(dummy_file_path, dummy_cnf)


def test_file_loading(dummy_file_path, dummy_cleaner):
    """File cleaner should contain the provided file."""
    assert str(dummy_cleaner.excel.io) == str(dummy_file_path)


def test_generic_file_preparation(dummy_cleaner: File, dummy_cnf):
    """File processing should trigger underlying sheet and section preparation."""
    dummy_cleaner.prepare()
    dummy_cleaner.tidy_up()
    cnf_dict = {
        sheet: [section for section in sheet_cnf["sections"]]
        for sheet, sheet_cnf in dummy_cnf["sheets"].items()
    }
    file_dict = {
        sheet_name: [section for section in sheet]
        for sheet_name, sheet in dummy_cleaner.tidy_sheets.items()
    }
    assert cnf_dict == file_dict
    assert DUMMY_TIDY_DF.equals(
        dummy_cleaner.tidy_sheets[Sheet.__name__][Section.__name__]
    )
