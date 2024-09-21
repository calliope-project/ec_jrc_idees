"""JRC-IDEES generic functionality."""

import importlib
from collections import namedtuple
from math import isclose
from pathlib import Path
from typing import Literal

import pandas as pd
from styleframe import StyleFrame  # type: ignore

from ec_jrc_idees.settings import CNF, SUPPORTED_FILES, SUPPORTED_MC, SUPPORTED_YEARS
from ec_jrc_idees.settings.config import tidy_columns_cnf
from ec_jrc_idees._utils import cleaning

STYLE_FEATURES = Literal[
    "bg_color", "bold", "font_color", "underline", "border_type", "indent"
]

ExcelRows: tuple[int, int] = namedtuple("ExcelRows", "start end")


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
        self.results: pd.DataFrame
        section_df = data.loc[self.row_slice(self.EXCEL_ROW_RANGE)]
        if isinstance(section_df, pd.Series):
            raise TypeError("Parsed section must be DataFrame, not Series.")
        self.data: pd.DataFrame = section_df.dropna(how="all", axis="columns")
        if "Code" in self.data.columns:
            self.data = self.data.drop("Code", axis="columns")

    def process(self):
        """Process section."""
        for column, value in self.cnf["tidy_columns"].items():
            self.results.insert(0, column, value, allow_duplicates=False)

    def _get_clean_data(self) -> pd.DataFrame:
        return cleaning.drop_empty_rows_and_cols(self.data)

    def row_slice(self, excel_rows: tuple[int, int]):
        """Get a dataframe section based on excel numbers."""
        return slice(excel_rows[0] - 2, excel_rows[1] - 2)

    @staticmethod
    def unit_from_parenthesis(cell_text: str) -> str:
        """Read text within a parenthesis as unit and standardize it."""
        if cell_text.count("(") != 1 or cell_text.count(")") != 1:
            raise ValueError("Too many parenthesis to parse.")
        unit = cell_text.split("(")[1].split(")")[0]
        unit = unit.replace(" of ", "_").replace(" ", "_").replace("/", "per")
        unit = unit.lower()
        return unit

    def get_style_feature(self, feature: STYLE_FEATURES, index: pd.Index) -> pd.Series:
        """Search the styleframe using the fist column."""
        col = self.data.columns[0]
        return getattr(self.style[col].style, feature)[index]

    def find_subsection(
        self,
        row: int,
        subsections: pd.Series,
        find: Literal["value", "index"] = "value",
    ) -> str:
        """Find subsection a row belongs to.

        This function requires `subsections` to have the following setup:
        - `subsections.index`: the row in `self.data` were a section starts.
        - `subsections.values`: the name of the section.

        Sections encompass all the values until the next. E.g.:
        20: "LNG vehicles" covers index 20 until 29.
        30: "Motor vehicles" covers all following values.

        Values lower than the first subsection are considered invalid!
        """
        if row < subsections.index.min():
            raise ValueError("Requested row located before the first section.")
        if row not in self.data.index:
            raise ValueError("Requested row not in section data.")
        n_idx = subsections.index.to_numpy()
        idx = n_idx[n_idx <= row].max()
        if find == "value":
            return subsections[idx]
        elif find == "index":
            return idx

    def check_subsection(self, columns: list[int], section: list[int]):
        """Compare results against aggregated data sections.

        Parameters
        ----------
        years : pd.Series | list
            Columns to compare in both data and results.
        section : pd.Series
            Specifies the aggregated rows in the input data.

        Raises
        ------
        ValueError
            Incorrect parsing detected (checksum failed).
        """
        results = self.results[columns]
        data = self.data[columns]
        for i, idx in enumerate(section):
            if idx == section[-1]:
                results_sum = results.loc[idx:].sum().sum()
                data_sum = data.loc[idx].sum()
            else:
                results_sum = self.results.loc[idx:section[i+1], columns].sum().sum()
                data_sum = data.loc[idx].sum()
            if not isclose(results_sum, data_sum):
                raise ValueError("Parsing was incorrect!")

    def get_text_column(self) -> pd.Series:
        """Return the text column of this section."""
        idees_text = self.data.select_dtypes("object")
        if len(idees_text.columns) > 1:
            raise ValueError("Section contains more than one column with text.")
        return idees_text[self.data.columns[0]]

    def get_annual_data(self) -> pd.DataFrame:
        """Return yearly data for this section."""
        year_data = self.data.select_dtypes("number")
        years = year_data.columns.to_numpy()
        if not all(CNF["years"]["min"] <= years) & all(years <= CNF["years"]["max"]):
            raise ValueError("Section contains non-annual data.")
        return year_data

    def get_preset_row(self, empty_cols: pd.Index):
        tidy_dict = tidy_columns_cnf(self.filename, self.sheetname, self.name)
        preset = pd.DataFrame([tidy_dict])

        preset[empty_cols] = None
        preset = preset.iloc[0]
        preset


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
