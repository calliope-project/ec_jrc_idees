"""Generic classes to help with IDEES parsing."""

from abc import ABC, abstractmethod
from math import isclose
from pathlib import Path
from typing import Literal

import pandas as pd
from styleframe import StyleFrame

from ec_jrc_idees.utils import Metadata, get_filename_metadata

STYLE_FEATURES = Literal[
    "bg_color", "bold", "font_color", "underline", "border_type", "indent"
]


class IDEESSection:
    """Generic IDEES section within a sheet."""

    EXCEL_ROW_RANGE: tuple[int, int]
    NAME: str

    def __init__(self, dirty_sheet: pd.DataFrame, style: StyleFrame, cnf: dict) -> None:
        self.cnf: dict = cnf
        self.style: StyleFrame = style
        self.results: pd.DataFrame
        # Do a bit of pre-cleaning to make processing easier.
        self.dirty_df = (
            dirty_sheet.loc[self.get_excel_slice(self.EXCEL_ROW_RANGE)]
            .dropna(how="all", axis="columns")
            .drop("Code", axis="columns", errors="ignore")
        )
        self.tidy_df: pd.DataFrame

    @abstractmethod
    def tidy_up(self):
        """Process section."""
        ...

    def get_excel_slice(self, excel_rows: tuple[int, int]):
        """Get a dataframe section based on excel numbers."""
        return slice(excel_rows[0] - 2, excel_rows[1] - 2)

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
        20: "Section A" covers index 20 until 29.
        30: "Section B" covers all following values until 49.
        50: "Section B" the last section covers values until the end of the dataframe.

        Values lower than the first subsection are considered invalid!
        """
        if row < subsections.index.min():
            raise ValueError("Requested row located before the first section.")
        if row not in self.dirty_df.index:
            raise ValueError("Requested row not in section data.")
        n_idx = subsections.index.to_numpy()
        idx = n_idx[n_idx <= row].max()
        if find == "value":
            return subsections[idx]
        elif find == "index":
            return idx

    def check_subsection(self, columns: list[int], aggregate: list[int]):
        """Compare results against aggregated data sections.

        Compares the sum of the rows below the aggregate and before the next section.

        Parameters
        ----------
        columns : pd.Series | list
            Columns to compare in both data and results.
        section : pd.Series
            Specifies the aggregated rows in the input data.

        Raises
        ------
        ValueError
            Incorrect parsing detected (checksum failed).
        """
        results = self.tidy_df[columns]
        data = self.dirty_df[columns]
        for i, idx in enumerate(aggregate):
            if idx == aggregate[-1]:
                results_sum = results.loc[idx:].sum().sum()
                data_sum = data.loc[idx].sum()
            else:
                results_sum = (
                    self.tidy_df.loc[idx : aggregate[i + 1], columns].sum().sum()
                )
                data_sum = data.loc[idx].sum()
            if not isclose(results_sum, data_sum):
                raise ValueError("Parsing was incorrect!")

    def get_text_column(self) -> pd.Series:
        """Get the text column of this section."""
        idees_text = self.dirty_df.select_dtypes("object")
        if len(idees_text.columns) > 1:
            raise ValueError("Section contains more than one column with text.")
        return idees_text[self.dirty_df.columns[0]]

    def get_annual_dataframe(self) -> pd.DataFrame:
        """Get yearly data in this section."""
        year_data = self.dirty_df.select_dtypes("number")
        return year_data


class IDEESSheet:
    """Generic IDEES sheet."""

    NAME: str
    TARGET_SECTIONS: list[type[IDEESSection]]

    def __init__(self, excel: pd.ExcelFile, cnf: dict) -> None:
        self.dirty_sheet: pd.DataFrame = excel.parse(self.NAME)
        self.style: StyleFrame = StyleFrame.read_excel(
            excel, read_style=True, sheet_name=self.NAME
        )
        self.cnf: dict = cnf
        self.dirty_sections: dict[str, IDEESSection] = {}
        self.tidy_sections: dict[str, pd.DataFrame] = {}

    def prepare(self) -> None:
        """Prepare the section code needed for this file and version."""
        for target_section in self.TARGET_SECTIONS:
            name = target_section.NAME
            self.dirty_sections[name]  = target_section(
                self.dirty_sheet, self.style, self.cnf["sections"][name]
            )

    def tidy_up(self) -> None:
        """Turn all sections in this sheet into machine readable data."""
        for name, section in self.dirty_sections.items():
            section.tidy_up()
            self.tidy_sections[name] = section.tidy_df


class IDEESFile(ABC):
    """Generic IDEES file."""

    TARGET_SHEETS: list[type[IDEESSheet]]
    VALID_VERSIONS: list[int]
    NAME: str

    def __init__(self, filepath: Path | str, cnf: dict) -> None:
        filepath = Path(filepath)

        self.excel: pd.ExcelFile = pd.ExcelFile(filepath)
        self.cnf: dict = cnf
        self.dirty_sheets: dict[str, IDEESSheet] = {}
        self.tidy_sheets: dict[str, dict[str, pd.DataFrame]] = {}
        self.metadata: Metadata = get_filename_metadata(filepath.name)

    def prepare(self) -> None:
        """Prepare the sheet code needed for this file and version."""
        for target_sheet in self.TARGET_SHEETS:
            name = target_sheet.NAME
            self.dirty_sheets[name] = target_sheet(self.excel, self.cnf["sheets"][name])
            self.dirty_sheets[name].prepare()

    def tidy_up(self) -> None:
        """Turn all sheets in this file into machine readable data."""
        for name, sheet in self.dirty_sheets.items():
            sheet.tidy_up()
            self.tidy_sheets[name] = sheet.tidy_sections
