"""Generic dataset operations."""

import pandas as pd

from ec_jrc_idees.settings import CNF


def drop_empty_rows_and_cols(data: pd.DataFrame) -> pd.DataFrame:
    """Remove all empty spaces in a dataframe."""
    return data.dropna(how="all").dropna(how="all", axis=1)


def get_code_cols(data:pd.DataFrame, column_names: list[str]) -> pd.DataFrame:
    """Add extra columns based on the IDEES code."""
    mapping = {i: name for i, name in enumerate(column_names)}
    tidy_df = data[CNF["code_col"]].str.split(".", expand=True).rename(columns=mapping)
    if len(tidy_df.columns != column_names):
        raise ValueError(f"Column mismatch: '{column_names}' vs '{tidy_df.columns}")
    return pd.concat([tidy_df, data], axis=1)


def get_excel_row_slice(row_range: tuple[int, int]):
    """Get a dataframe section based on excel numbers."""
    return slice(row_range[0]-2, row_range[1]-1)
