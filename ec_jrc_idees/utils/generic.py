"""JRC-IDEES generic functionality."""

from pathlib import Path

import pandas as pd
from styleframe import StyleFrame  # type: ignore

from ec_jrc_idees.settings import CNF, SUPPORTED_FILES, SUPPORTED_MC, SUPPORTED_YEARS
from ec_jrc_idees.utils import cleaning


class IDEESSection:
    """Generic IDEES section (within a sheet)."""

    EXCEL_ROW_RANGE = tuple[int, int]
    TIDY_COLS = tuple

    def __init__(
        self, data: pd.DataFrame, style: StyleFrame, cnf: dict
    ) -> None:
        self.name = self.__class__.__name__
        self.data: pd.DataFrame = cleaning.get_excel_row_range(data, self.cnf["row"])
        self.style: StyleFrame = style
        self.cnf: dict = cnf[self.name]

    def _row_slice(self):
        return slice(self.EXCEL_ROW_RANGE[0]-2, self.EXCEL_ROW_RANGE[1]-2)


class IDEESSheet:
    """Generic IDEES sheet."""

    SECTIONS: list[type[IDEESSection]]

    def __init__(self, excel: pd.ExcelFile, cnf) -> None:
        self.name: str = self.__class__.__name__
        self.data: pd.DataFrame = excel.parse(self.name)
        self.style: StyleFrame = StyleFrame.read_excel(
            excel, read_style=True, sheet_name=self.name
        )
        self.cnf: dict = cnf[self.name]
        self.sections: list[IDEESSection]

    def process_sections(self):
        """Process all configured sections."""
        for section_class in self.SECTIONS:
            section = section_class(self.data, self.style, self.cnf)



class IDEESFile:
    """Generic IDEES file."""

    SHEETS: list[type[IDEESSheet]]

    def __init__(self, dir, file, mc, year: int = 2021) -> None:
        if year not in SUPPORTED_YEARS:
            raise NotImplementedError(f"{year} not supported.")
        if file not in SUPPORTED_FILES:
            raise NotImplementedError(f"{file} not supported.")
        if mc not in SUPPORTED_MC:
            raise NotImplementedError(f"{mc} not supported.")
        self.dir = Path(dir)
        self.mc = mc
        self.year = year
        self.filename = f"JRC-IDEES-{year}_{file}_{mc}.xlsx"
        self.path = Path(dir) / mc / self.filename
        self.excel = pd.ExcelFile(self.path)
        self.cnf = CNF[file]
        self.sheets: list[IDEESSheet]
        self.name: str = self.__class__.__name__


    def process_sheets(self):
        """Process all configured sheets."""
        for sheet_class in self.SHEETS:
            sheet = sheet_class(self.excel, self.cnf)


