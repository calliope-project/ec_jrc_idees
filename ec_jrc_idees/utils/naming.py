"""Renaming functionality."""

import inflection
import pandas as pd

from ec_jrc_idees.utils.config import SHEETS


def _to_snake_case(column: pd.Series) -> pd.Series:
    """Rename variables to make them human readable."""
    return column.apply(inflection.underscore)


# def _replace_strings(column: pd.Series, file: str | None = None) -> pd.Series:
#     """In-place replacement of strings in a column."""
#     if file:
#         mapping = CONFIG[file][column.name]["replace"]
#     else:
#         mapping = CONFIG[column.name]["replace"]
#     for old, new in mapping.items():
#         column = column.str.replace(old, new)
#     return column
