"""General IDEES configuration and quality of life stuff."""

import typing
from pathlib import Path

import yaml

FILES = typing.Literal[
    "EmissionBalance",
    "EnergyBalance",
    "Industry",
    "Macro",
    "PowerGen",
    "Residential",
    "Tertiary",
    "Transport",
]

MC = typing.Literal[
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
    "EU27",
]

config_path = Path("ec_jrc_idees/resources/")

CONFIG = yaml.safe_load((config_path / "config.yaml").read_text())
for file in list(typing.get_args(FILES)):
    CONFIG[file] = yaml.safe_load((config_path / f"config_{file}.yaml").read_text())


IDEES_CONFIG = yaml.safe_load(Path("ec_jrc_idees/resources/config.yaml").read_text())
