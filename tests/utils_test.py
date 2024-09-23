"""Test generic utility functions."""

import pandas as pd
import pytest
from styleframe import StyleFrame

from ec_jrc_idees import utils


@pytest.mark.parametrize("filename", ["JRC-IDEES-2021_Industry_DE.xlsx"])
def test_filename_metadata(filename):
    """Metadata should be extracted correctly for IDEES version."""
    metadata = utils.get_filename_metadata(filename)

    assert all(
        [
            metadata.version == 2021,  # noqa: PLR2004
            metadata.file == "Industry",
            metadata.country_eurostat == "DE",
        ]
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Stock of vehicles - total (vehicles)", "vehicles"),
        ("CO2 emissions (kt CO2)", "kt_co2"),
        ("something subsector (kt of CO2)", "kt_co2"),
        ("Market shares (%)", "%"),
        ("Emission intensity (kt of CO2 / ktoe)", "kt_co2_per_ktoe"),
        ("yadda (toe useful/t of output) yadda", "toe_useful_per_t_output"),
        ("thing (toe useful / t of output)", "toe_useful_per_t_output"),
    ],
)
def test_unit_extraction(text, expected):
    """Units within a cell should be cleaned approprietly."""
    assert utils.get_unit_in_parenthesis(text) == expected


@pytest.mark.parametrize("prefix", [{"foo": "bar", "empty": ""}])
def test_prefix_columns(prefix):
    """Prefix columns should be added in the right order."""
    suffix = ["things", "given"]
    data = pd.DataFrame(None, columns=suffix, index=[1, 2, 3])
    utils.insert_prefix_columns(data, prefix)
    assert list(data.columns) == list(prefix.keys()) + suffix
    assert all([data[col].unique() == prefix[col] for col in prefix])


@pytest.mark.parametrize(("feature", "expected"), [("indent", set(range(0, 6)))])
def test_style(country_path, version, feature, expected):
    """Style feature extraction should work."""
    style = StyleFrame.read_excel(
        country_path / f"JRC-IDEES-{version}_Industry_DE.xlsx",
        read_style=True,
        sheet_name="NFM_emi",
    )
    values = utils.get_style_feature(style, feature)
    assert not set(values.unique()) - expected
