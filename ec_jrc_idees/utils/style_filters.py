"""Utility functions for filtering data using cell style."""

from typing import Literal

import pandas as pd
from styleframe import StyleFrame  # type: ignore

# TODO: remove

STYLE_OPTIONS = Literal["bg_color", "bold", "font_color", "underline", "border_type"]

def get_background_color(column, style: StyleFrame, index: pd.Index) -> pd.Series:
    """Return hexadecimal codes for the a column and index range."""
    return style[column].style.bg_color[index]

def get_white_cells(column, style: StyleFrame, index: pd.Index) -> pd.Series:
    """Find cells with a white background."""
    background_color = get_background_color(column, style, index)
    return background_color[background_color == "ffffff"]

def get_colored_cells(column, style: StyleFrame, index: pd.Index) -> pd.Series:
    """Find cells with a white background."""
    background_color = get_background_color(column, style, index)
    return background_color[background_color != "ffffff"]

def get_indent_level(column, style: StyleFrame, index: pd.Index, indent: int) -> pd.Series:
    """Return indent applied to a cell."""
    indent_df = style[column].style.indent[index]
    return indent_df[indent_df == indent]
