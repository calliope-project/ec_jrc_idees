"""JRC-IDEES generic functionality."""

import importlib
from pathlib import Path

import pandas as pd
from styleframe import StyleFrame  # type: ignore

from ec_jrc_idees.settings import CNF, SUPPORTED_FILES, SUPPORTED_MC, SUPPORTED_YEARS
from ec_jrc_idees.utils import cleaning


class IDEESSection:
    """Generic IDEES section (within a sheet)."""

    EXCEL_ROW_RANGE: tuple[int, int]

    def __init__(
        self, filename: str, sheetname: str, data: pd.DataFrame, style: StyleFrame
    ) -> None:
        self.name: str = self.__class__.__name__
        self.filename: str = filename
        self.sheetname: str = sheetname
        self.cnf: dict = CNF["files"][filename]["sheets"][sheetname]["sections"][
            self.name
        ]
        self.style: StyleFrame = style
        self.results: dict[str, pd.DataFrame]
        self.data = cleaning.drop_empty_rows_and_cols(
            cleaning.get_excel_row_range(data, self.EXCEL_ROW_RANGE)
        )

    def _get_clean_data(self) -> pd.DataFrame:
        return cleaning.drop_empty_rows_and_cols(self.data)


class IDEESSheet:
    """Generic IDEES sheet."""

    def __init__(self, filename: str, excel: pd.ExcelFile) -> None:
        self.filename: str = filename
        self.name: str = self.__class__.__name__
        self.data: pd.DataFrame = excel.parse(self.name)
        self.style: StyleFrame = StyleFrame.read_excel(
            excel, read_style=True, sheet_name=self.name
        )
        self.cnf: dict = CNF["files"][self.filename]["sheets"][self.name]
        self.sections: dict[str, IDEESSection] = {}

    def prepare(self) -> None:
        """Fill in sections to process."""
        sections = list(self.cnf["sections"].keys())
        for section in sections:
            section_class = self._get_section_class(section)
            self.sections[section] = section_class(
                self.filename, self.name, self.data, self.style
            )

    def _get_section_class(self, section: str) -> type[IDEESSection]:
        module = importlib.import_module(
            f"ec_jrc_idees.{self.filename.lower()}.{self.name.lower()}.sections"
        )
        return getattr(module, section)


class IDEESFile:
    """Generic IDEES file."""

    def __init__(self, dir, file, mc, year: int = 2021) -> None:
        if year not in SUPPORTED_YEARS:
            raise NotImplementedError(f"{year} not supported.")
        if file not in SUPPORTED_FILES:
            raise NotImplementedError(f"{file} not supported.")
        if mc not in SUPPORTED_MC:
            raise NotImplementedError(f"{mc} not supported.")
        self.mc = mc
        self.year = year
        self.path = Path(dir) / mc / f"JRC-IDEES-{year}_{file}_{mc}.xlsx"
        self.excel = pd.ExcelFile(self.path)
        self.name: str = self.__class__.__name__
        self.cnf = CNF["files"][self.name]
        self.sheets: dict[str, IDEESSheet] = {}

    def prepare(self) -> None:
        """Fill in sheets to process."""
        sheets = list(self.cnf["sheets"].keys())
        for sheet in sheets:
            sheet_class = self._get_sheet_class(sheet)
            self.sheets[sheet] = sheet_class(self.name, self.excel)

    def _get_sheet_class(self, sheet: str) -> type[IDEESSheet]:
        """Get sheet class objects."""
        module = importlib.import_module(
            f"ec_jrc_idees.{self.name.lower()}.{sheet.lower()}"
        )
        return getattr(module, sheet)
