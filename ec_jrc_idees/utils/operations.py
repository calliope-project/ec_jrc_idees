"""Common operations for JRC sheets."""

from pathlib import Path

import pandas as pd

from ec_jrc_idees.utils import config

CONFIG = config.CONFIG


class Sheet:
    """Helper class to process JRC - IDEES sheets."""

    def __init__(self, dir: Path, ms: config.MC, file: config.FILES, sheet) -> None:
        filepath = dir / f"JRC-IDEES-2021_{ms}/JRC-IDEES-2021_{file}_{ms}.xlsx"
        raw_df = pd.read_excel(filepath, sheet_name=sheet).dropna(how="all", axis=1)
        self.sheet: pd.DataFrame = raw_df
        self.config: dict = CONFIG[file][sheet]

    def drop_excel_rows(self) -> None:
        """Remove a set of rows.

        Matches Excel numbers.
        """
        dropped = self.config.get("drop_rows")
        if dropped:
            self.sheet = self.sheet.drop(
                index=range(dropped["from"] - 1, dropped["to"])
            )

    def to_codes_only(self) -> None:
        """Remove rows with no code."""
        codes_df = self.sheet.dropna(how="all", axis=1).dropna(
            how="all", subset=CONFIG["code_column"]
        )
        assert not any(codes_df[CONFIG["code_column"]].duplicated())
        self.sheet = codes_df

    def to_tidy(self) -> None:
        """Add tidy columns based on IDEES codes."""
        columns = CONFIG["standard_tidy_columns"] + self.config["sector_tidy_columns"]
        mapping = {i: name for i, name in enumerate(columns)}
        tidy_df = self.sheet["Code"].str.split(".", expand=True).rename(columns=mapping)
        if not all([isinstance(col, str) for col in tidy_df.columns]):
            raise ValueError("Invalid tidy columns configuration.")
        self.sheet = pd.concat([tidy_df, self.sheet])


    def get_variable_datasets(self) -> dict[str, pd.DataFrame]:
        """Split sheet data per IDEES variable."""
        datasets = {}
        for var in self.sheet["variable"].unique():
            datasets[var] = self.sheet[self.sheet["variable"] == var]
        return datasets

