"""Common operations for JRC sheets."""

from pathlib import Path

import pandas as pd

from ec_jrc_idees.utils.config import CNF, SUPPORTED_FILES, SUPPORTED_MC


class CleanSheet:
    """Helper class to process JRC - IDEES sheets."""

    def __init__(self, dir: str | Path, ms: str, file: str, sheet) -> None:

        if ms not in SUPPORTED_MC or file not in SUPPORTED_FILES:
            raise ValueError(f"Unsupported sheet: {file}::{ms}")

        self.ms: str = ms
        self.file: str = file
        self.name: str = sheet

        filepath = Path(dir) / f"JRC-IDEES-2021_{ms}/JRC-IDEES-2021_{file}_{ms}.xlsx"
        raw_df = pd.read_excel(filepath, sheet_name=sheet).dropna(how="all", axis=1)
        raw_df = raw_df.rename(columns={raw_df.columns[0]: "description"})

        self.data: pd.DataFrame = raw_df
        self._preprocess()

    def _preprocess(self) -> None:
        """Turn the IDEES sheet into group of tidy dataframes."""
        self._remove_rows_without_code()
        self._add_tidy_columns()
        self._add_file_column()

    def _remove_rows_without_code(self) -> None:
        """Remove rows with no code."""
        codes_df = self.data.dropna(how="all", axis=1).dropna(
            how="all", subset=CNF["code_col"]
        )
        assert not any(codes_df[CNF["code_col"]].duplicated())
        self.data = codes_df

    def _add_tidy_columns(self) -> None:
        """Add tidy columns based on IDEES codes."""
        columns = CNF["standard_cols"]
        mapping = {i: name for i, name in enumerate(columns)}
        tidy_df = self.data["Code"].str.split(".", expand=True).rename(columns=mapping)
        self.data = pd.concat([tidy_df, self.data], axis=1)

    def _add_file_column(self):
        """Add file column."""
        file_col = pd.Series(index=self.data.index, data=self.file)
        self.data = pd.concat([self.data, file_col], axis=1)
