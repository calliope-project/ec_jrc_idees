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
    VALID_VERSIONS: tuple[int, ...]
    NAME: str

    def __init__(self, dirty_sheet: pd.DataFrame, style: StyleFrame, cnf: dict) -> None:
        self.cnf: dict = cnf
        self.style: StyleFrame = style
        # Do a bit of pre-cleaning to make processing easier.
        self.dirty_df = (
            dirty_sheet.loc[self.get_excel_slice(self.EXCEL_ROW_RANGE)]
            .dropna(how="all", axis="columns")
            .drop("Code", axis="columns", errors="ignore")
        )
        # Standard features to prepare
        self.annual_df: pd.DataFrame
        self.idees_text: pd.Series
        # results
        self.tidy_df: pd.DataFrame

    def prepare(self):
        """Prepare features for this section."""
        self.idees_text = self.get_idees_text_column()
        self.annual_df = self.get_annual_dataframe()

    @abstractmethod
    def tidy_up(self):
        """Process section."""

    @abstractmethod
    def check(self):
        """Run validation for this section."""

    def prettify(self) -> None:
        """Rename and standardise stuff, if necessary."""
        pass

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

    def check_subsection(self, columns, aggregate_indexes):
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
        for i, idx in enumerate(aggregate_indexes):
            if idx == aggregate_indexes[-1]:
                results_sum = self.tidy_df[columns].loc[idx:].sum().sum()
                data_sum = self.dirty_df[columns].loc[idx].sum()
            else:
                end = aggregate_indexes[i + 1] - 1  # index before next aggregate row
                results_sum = (
                    self.tidy_df.loc[slice(idx, end), columns].sum().sum()
                )
                data_sum = self.dirty_df[columns].loc[idx].sum()
            if not isclose(results_sum, data_sum):
                raise ValueError("Parsing was incorrect!")

    def get_idees_text_column(self) -> pd.Series:
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
        self.tidy_sections: dict[str, pd.DataFrame] = {}
        self.metadata: Metadata = get_filename_metadata(str(Path(str(excel.io)).name))

    def prepare(self) -> None:
        """Prepare features for this sheet, if necessary."""
        pass

    def tidy_up(self) -> None:
        """Turn all sections in this sheet into machine readable data."""
        for target_section in self.TARGET_SECTIONS:
            name = target_section.NAME
            section_cleaner = target_section(
                self.dirty_sheet, self.style, self.cnf["sections"][name]
            )
            section_cleaner.prepare()
            section_cleaner.tidy_up()
            section_cleaner.prettify()
            section_cleaner.check()
            self.tidy_sections[name] = section_cleaner.tidy_df

    def prettify(self) -> None:
        """Rename and standardise stuff, if necessary."""
        pass

    @abstractmethod
    def check(self):
        """Run validation for this sheet."""


class IDEESFile(ABC):
    """Generic IDEES file."""

    TARGET_SHEETS: list[type[IDEESSheet]]
    NAME: str

    def __init__(self, filepath: Path | str, cnf: dict) -> None:
        filepath = Path(filepath)

        self.excel: pd.ExcelFile = pd.ExcelFile(filepath)
        self.cnf: dict = cnf
        self.tidy_sheets: dict[str, dict[str, pd.DataFrame]] = {}
        self.metadata: Metadata = get_filename_metadata(filepath.name)

    def prepare(self) -> None:
        """Prepare features for this file, if necessary."""
        pass

    def tidy_up(self) -> None:
        """Clean all sheets configured for this file."""
        for target_sheet in self.TARGET_SHEETS:
            name = target_sheet.NAME
            sheet_cleaner = target_sheet(self.excel, self.cnf["sheets"][name])
            sheet_cleaner.prepare()
            sheet_cleaner.tidy_up()
            sheet_cleaner.prettify()
            sheet_cleaner.check()
            self.tidy_sheets[name] = sheet_cleaner.tidy_sections

    def prettify(self) -> None:
        """Rename and standardise stuff, if necessary."""
        pass

    @abstractmethod
    def check(self):
        """Run validation for this file."""
