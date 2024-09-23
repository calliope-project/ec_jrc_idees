"""Generic classes to help with IDEES parsing."""

from abc import ABC, abstractmethod
from math import isclose
from pathlib import Path
from typing import Literal

import pandas as pd
from pandera import Check, Column, DataFrameSchema, Index
from styleframe import StyleFrame

from ec_jrc_idees import utils
from ec_jrc_idees.utils import Metadata

STYLE_FEATURES = Literal[
    "bg_color", "bold", "font_color", "underline", "border_type", "indent"
]


class IDEESSection:
    """Generic IDEES section within a sheet."""

    EXCEL_ROW_RANGE: tuple[int, int]
    VALID_VERSIONS: tuple[int, ...]

    def __init__(self, dirty_sheet: pd.DataFrame, style: StyleFrame, cnf: dict) -> None:
        self.cnf: dict[str, dict] = cnf
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

    def generic_check(self):
        """Run validation for this section."""
        if "(" in self.idees_text.iloc[0]:
            units = utils.get_units_in_brackets(self.idees_text.iloc[0])
        else:
            units = None
        expected_units = self.cnf["units"]["idees"]
        if units != expected_units:
            raise ValueError(f"Unit mismatch: got '{units}', not '{expected_units}'")

    @abstractmethod
    def specific_check(self):
        """Run tailored checks for this section."""

    def prettify(self) -> None:
        """Rename and standardise stuff, if necessary."""
        units = self.cnf["units"].get("tidy")
        if not units:
            units = utils.standardize_unit(self.cnf["units"]["idees"])
        assert units, "Units cannot be empty."
        self.tidy_df = pd.melt(
            self.tidy_df,
            id_vars=list(self.cnf["template_columns"].keys()),
            value_vars=self.annual_df.columns.to_list(),
            var_name="year",
            value_name=f"{self.cnf['variable']} [{units}]",
        )
        # The cleaning should've made object inferring easy.
        self.tidy_df = self.tidy_df.infer_objects()

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
                results_sum = self.tidy_df.loc[slice(idx, end), columns].sum().sum()
                data_sum = self.dirty_df[columns].loc[idx].sum()
            if not isclose(results_sum, data_sum):
                raise ValueError("Parsing was incorrect!")

    def get_idees_text_column(self) -> pd.Series:
        """Get the text column of this section."""
        idees_text = self.dirty_df.iloc[:, 0]
        if not all(isinstance(i, str) for i in idees_text.to_numpy()):
            raise ValueError("First column should only be string values.")
        return idees_text

    def get_annual_dataframe(self) -> pd.DataFrame:
        """Get yearly data in this section."""
        annual_df = self.dirty_df.iloc[:, 1:]
        return annual_df


class IDEESSheet:
    """Generic IDEES sheet."""

    SHEET_NAME: str
    SECTION_CLEANERS: list[type[IDEESSection]]

    def __init__(self, excel: pd.ExcelFile, cnf: dict) -> None:
        self.dirty_sheet: pd.DataFrame = excel.parse(self.SHEET_NAME)
        self.style: StyleFrame = StyleFrame.read_excel(
            excel, read_style=True, sheet_name=self.SHEET_NAME
        )
        self.cnf: dict = cnf
        self.tidy_sections: dict[str, pd.DataFrame] = {}
        self.metadata: Metadata = utils.get_filename_metadata(str(excel.io))
        self.section_cleaners: dict[str, type[IDEESSection]] = {
            _class.__name__: _class for _class in self.SECTION_CLEANERS
        }

    def prepare(self) -> None:
        """Prepare features for this sheet, if necessary."""
        pass

    def tidy_up(self) -> None:
        """Turn all sections in this sheet into machine readable data."""
        target_sections = self.cnf["sections"]
        for name, cnf in target_sections.items():
            if name not in self.section_cleaners:
                raise ValueError(f"Unable to clean configured section: '{name}'.")
            section_cleaner = self.section_cleaners[name](
                self.dirty_sheet, self.style, cnf
            )
            section_cleaner.prepare()
            section_cleaner.tidy_up()
            section_cleaner.generic_check()
            section_cleaner.specific_check()
            section_cleaner.prettify()
            self.tidy_sections[name] = section_cleaner.tidy_df

    def prettify(self) -> None:
        """Rename and standardise stuff, if necessary."""
        pass

    def check(self):
        """Run validation for this sheet.

        By default:
        - Check that template columns are present and in order.
        - Check that that all expected years are present.
        """
        expected_years = utils.get_expected_years(self.metadata)

        for name, tidy_df in self.tidy_sections.items():
            cnf = self.cnf["sections"][name]
            unit = utils.get_units_in_brackets(tidy_df.columns[-1], brackets="[]")
            variable_col = f"{cnf['variable']} [{unit}]"
            template_columns = {name: Column(str) for name in cnf["template_columns"]}
            data_columns = {
                "year": Column(int, checks=Check.isin(expected_years)),
                variable_col: Column(float, nullable=True),
            }
            schema = DataFrameSchema(
                columns=template_columns | data_columns,
                index=Index(int, unique=True),
                ordered=True,
            )
            schema.validate(tidy_df)


class IDEESFile(ABC):
    """Generic IDEES file."""

    SHEET_CLEANERS: list[type[IDEESSheet]]

    def __init__(self, filepath: Path | str, cnf: dict) -> None:
        filepath = Path(filepath)

        self.excel: pd.ExcelFile = pd.ExcelFile(filepath)
        self.cnf: dict = cnf
        self.tidy_sheets: dict[str, dict[str, pd.DataFrame]] = {}
        self.metadata: Metadata = utils.get_filename_metadata(filepath.name)
        self.available_sheets: dict[str, type[IDEESSheet]] = {
            _class.__name__: _class for _class in self.SHEET_CLEANERS
        }

    def prepare(self) -> None:
        """Prepare features for this file, if necessary."""
        pass

    def tidy_up(self) -> None:
        """Clean all sheets configured for this file."""
        target_sheets = self.cnf["sheets"]
        for name, cnf in target_sheets.items():
            if name not in self.available_sheets:
                raise ValueError(f"Unable to clean configured sheet: '{name}'.")
            sheet_cleaner = self.available_sheets[name](self.excel, cnf)
            sheet_cleaner.prepare()
            sheet_cleaner.tidy_up()
            sheet_cleaner.check()
            sheet_cleaner.prettify()
            self.tidy_sheets[name] = sheet_cleaner.tidy_sections

    def prettify(self) -> None:
        """Rename and standardise stuff, if necessary."""
        pass

    @abstractmethod
    def check(self):
        """Run validation for this file."""
