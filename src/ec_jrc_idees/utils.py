"""Generic utility functions that may be used anywhere."""

from typing import Literal, NamedTuple

import inflection
import pandas as pd
from styleframe import StyleFrame

STYLE_FEATURES = Literal[
    "bg_color", "bold", "font_color", "underline", "border_type", "indent"
]


class Metadata(NamedTuple):
    """Contains important details contained in the filename."""

    version: int
    file: str
    country_eurostat: str


def get_filename_metadata(filename: str) -> Metadata:
    """Get metadata from the JRC-IDEES filenames."""
    data = filename.split("-")[-1].split("_")
    metadata = Metadata(
        version=int(data[0]), file=data[1], country_eurostat=data[-1].split(".")[0]
    )
    return metadata


def get_unit_in_parenthesis(text: str) -> str:
    """Read text within a parenthesis as unit and standardize it."""
    if text.count("(") != 1 or text.count(")") != 1:
        raise ValueError("Invalid string: must be in the for of 'Something (unit)'.")
    unit = standardize_unit(text[text.find("(") + 1 : text.find(")")])
    return unit


def standardize_unit(unit: str):
    """Convert text to underscored lowercase."""
    unit = unit.replace(" of ", "_")
    if "/" in unit:
        if unit[unit.find("/") - 1] == " " and unit[unit.find("/") + 1] == " ":
            unit = unit.replace("/", "per")
        else:
            unit = unit.replace("/", " per ")
    unit = unit.replace(" ", "_")
    unit = inflection.underscore(unit)
    return unit


def insert_prefix_columns(data: pd.DataFrame, prefixes: dict):
    """Add columns with default values at the start of a dataframe."""
    for column, value in reversed(prefixes.items()):
        data.insert(0, column, value, allow_duplicates=False)


def get_style_feature(
    style: StyleFrame,
    feature: STYLE_FEATURES,
    rows: pd.Index | None = None,
) -> pd.Series:
    """Search Excel style features of the first column.

    Optionally, return only specific rows.
    """
    series = getattr(style[style.columns[0].value].style, feature)
    if rows is not None:
        series = series[rows]
    return series
