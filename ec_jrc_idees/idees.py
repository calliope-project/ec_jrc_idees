"""Manage JRC data."""

from pathlib import Path

import pandas as pd

from ec_jrc_idees.utils import config


class EasyIDEES:
    """Main JRC-IDES handler."""

    _config = config.CONFIG

    def __init__(self, path: str | Path) -> None:
        self._raw_path: Path = Path(path)

    def download(self, code: str):
        """Download a file from the JRC website."""
        ...

    def get_cleaned_sheet(
        self, ms: config.MC, file: config.FILES, sheet: str
    ) -> pd.DataFrame:
        """Get a cleaned dataframe."""
        filepath = (
            self._raw_path / f"JRC-IDEES-2021_{ms}/JRC-IDEES-2021_{file}_{ms}.xlsx"
        )
        cleaned_df = (
            pd.read_excel(filepath, sheet_name=sheet)
            .dropna(how="all", axis=1)
            .dropna(how="all", subset=self._config["code_column"])
        )
        cleaned_df = cleaned_df.rename(columns={cleaned_df.columns[0]: "IDEES text"})
        return cleaned_df
