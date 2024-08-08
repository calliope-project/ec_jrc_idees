"""Renaming functionality."""

import inflection
import pandas as pd


def _to_snake_case(column: pd.Series) -> pd.Series:
    """Rename variables to make them human readable."""
    return column.apply(inflection.underscore)


def _replace_strings(column: pd.Series, mapping: dict) -> pd.Series:
    """In-place replacement of strings in a column."""
    for old, new in mapping.items():
        column = column.str.replace(old, new)
    return column
