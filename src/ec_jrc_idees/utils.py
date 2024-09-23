"""Generic utility functions that may be used anywhere."""

from pathlib import Path
from typing import Literal, NamedTuple

import inflection
import pandas as pd
from styleframe import StyleFrame

STYLE_FEATURES = Literal[
    "bg_color", "bold", "font_color", "underline", "border_type", "indent"
]
BRACKETS = Literal["()", "[]", "<>"]

MIN_YEAR = 2000
MAX_YEAR_V1 = 2015
MAX_YEAR_V2 = 2021

class Metadata(NamedTuple):
    """Contains important details contained in the filename."""

    version: int
    file: str
    country_eurostat: str


def get_filename_metadata(filepath: str | Path) -> Metadata:
    """Get metadata from the JRC-IDEES filenames."""
    filename = Path(filepath).name
    data = filename.split("-")[-1].split("_")
    metadata = Metadata(
        version=int(data[0]), file=data[1], country_eurostat=data[-1].split(".")[0]
    )
    return metadata


def get_units_in_brackets(text: str, brackets: BRACKETS = "()") -> str:
    """Read text within a parenthesis as unit and standardize it."""
    if text.count(brackets[0]) != 1 or text.count(brackets[-1]) != 1:
        raise ValueError("Invalid string: must be in the form of 'Something (unit)'.")
    unit = text[text.find(brackets[0]) + 1 : text.find(brackets[-1])]
    return unit


def standardize_unit(unit: str):
    """Convert text to underscored lowercase."""
    unit = unit.replace(" of ", "_")
    if "/" in unit:
        if unit[unit.find("/") - 1] == " " and unit[unit.find("/") + 1] == " ":
            unit = unit.replace("/", "per")
        else:
            unit = unit.replace("/", " per ")
    unit = inflection.underscore(unit)
    return unit


def insert_prefix_columns(data: pd.DataFrame, prefixes: dict):
    """Add columns with default values at the start of a dataframe."""
    for column, value in reversed(prefixes.items()):
        data.insert(0, column, value, allow_duplicates=False)


def get_style_feature(
    style: StyleFrame, feature: STYLE_FEATURES, rows: pd.Index | None = None
) -> pd.Series:
    """Search Excel style features of the first column.

    Optionally, return only specific rows.
    """
    series = getattr(style[style.columns[0].value].style, feature)
    if rows is not None:
        series = series[rows]
    return series


def get_expected_years(metadata: Metadata) -> list[int]:
    """Get a range of years for this sheet."""
    if metadata.version == MAX_YEAR_V1:
        max_year = MAX_YEAR_V1
    elif metadata.version == MAX_YEAR_V2:
        max_year = MAX_YEAR_V2
    else:
        raise ValueError(f"Invalid version configured: '{metadata.version}'")
    return list(range(MIN_YEAR, max_year + 1))
