"""Common operations for JRC sheets."""

from pathlib import Path

import pandas as pd

from ec_jrc_idees.utils import config
from ec_jrc_idees.utils.config import CONFIG, SHEETS


class Sheet:
    """Helper class to process JRC - IDEES sheets."""

    def __init__(self, dir: str, ms: config.MC, file: config.FILES, sheet) -> None:
        filepath = Path(dir) / f"JRC-IDEES-2021_{ms}/JRC-IDEES-2021_{file}_{ms}.xlsx"
        raw_df = pd.read_excel(filepath, sheet_name=sheet).dropna(how="all", axis=1)
        self.ms: str = ms
        self.file: str = file
        self.sheet: str = sheet
        self.data: pd.DataFrame = raw_df

    @property
    def config(self) -> dict:
        """Get sheet configuration value."""
        try:
            return SHEETS[self.file][self.sheet]
        except KeyError:
            raise NotImplementedError(f"Requested {self.file}:{self.sheet} missing.")

    def tidy_up(self) -> None:
        """Turn the IDEES sheet into group of tidy dataframes."""
        self._drop_excel_rows()
        self._to_codes_only()
        self._add_code_cols()
        self._add_file_col()

    def _drop_excel_rows(self) -> None:
        """Remove a set of rows.

        Matches Excel numbers.
        """
        drop = self.config.get("drop_excel_rows")
        if drop:
            self.data = self.data.drop(index=range(drop["from"]-2, drop["to"]-1))

    def _to_codes_only(self) -> None:
        """Remove rows with no code."""
        codes_df = self.data.dropna(how="all", axis=1).dropna(
            how="all", subset=CONFIG["code_col"]
        )
        assert not any(codes_df[CONFIG["code_col"]].duplicated())
        self.data = codes_df

    def _add_code_cols(self) -> None:
        """Add tidy columns based on IDEES codes."""
        columns = CONFIG["standard_cols"]
        mapping = {i: name for i, name in enumerate(columns)}
        tidy_df = self.data["Code"].str.split(".", expand=True).rename(columns=mapping)
        self.data = pd.concat([tidy_df, self.data], axis=1)

    def _add_file_col(self):
        """Add file column."""
        file_col = pd.Series(index=self.data.index, data=self.file)
        self.data = pd.concat([self.data, file_col], axis=1)

    def get_variable_datasets(self) -> dict[str, pd.DataFrame]:
        """Split sheet data per IDEES variable."""
        datasets = {}
        for var in self.data["variable"].unique():
            datasets[var] = self.data[self.data["variable"] == var]
        return datasets
