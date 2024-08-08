"""General IDEES configuration and quality of life stuff."""

from pathlib import Path

import yaml

SUPPORTED_FILES = ("Transport")

SUPPORTED_MC = (
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
)

__cnf_path = Path("ec_jrc_idees/config/")

SHEET_CNF = {}
for file in SUPPORTED_FILES:
    SHEET_CNF[file] = yaml.safe_load(
        (__cnf_path / "files" / f"{file}.yaml").read_text()
    )

CNF = yaml.safe_load((__cnf_path / "config.yaml").read_text())
