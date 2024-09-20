"""General IDEES configuration and quality of life stuff."""

from pathlib import Path

import yaml

SUPPORTED_FILES = {"Transport"}

SUPPORTED_MC = {
    "BE",
    "BG",
    "CZ",
    "DK",
    "DE",
    "EE",
    "IE",
    "EL",
    "ES",
    "FR",
    "HR",
    "IT",
    "CY",
    "LV",
    "LT",
    "LU",
    "HU",
    "MT",
    "NL",
    "AT",
    "PL",
    "PT",
    "RO",
    "SI",
    "SK",
    "FI",
    "SE",
}

SUPPORTED_YEARS = {2021}

__here = Path(__file__).parent
CNF = yaml.safe_load((__here / "files/config.yaml").read_text())
CNF["files"] = {}
for file in SUPPORTED_FILES:
    CNF["files"][file] = yaml.safe_load((__here / f"files/{file}.yaml").read_text())


def tidy_columns_cnf(
    file: str, sheet: str | None = None, section: str | None = None
) -> dict[str, str]:
    """Return a dictionary with the tidy columns configured."""
    txt = "tidy_columns"

    tidy = CNF["files"][file][txt]
    if sheet:
        tidy |= CNF["files"][file]["sheets"][sheet][txt]
        if section:
            tidy |= CNF["files"][file]["sheets"][sheet]["sections"][section][txt]

    return tidy
