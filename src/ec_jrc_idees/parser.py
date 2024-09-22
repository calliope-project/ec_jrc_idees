"""Easy JRC processing."""

import importlib.resources
import zipfile
from pathlib import Path

import requests
import yaml


class EasyIDEES:
    """Easily process JRC-IDEES DATA."""

    def __init__(self, version: str | int) -> None:
        data_path = importlib.resources.files("ec_jrc_idees") / "data" / "parser.yaml"
        config = yaml.safe_load(data_path.read_text())
        self.config: dict = config["version_specific"][str(version)]
        self.config = self.config | config["generic"]

    def process_files(self):
        """Call all parsing functionality."""
        pass

    def download_country(self, country: str, zip: Path):
        """Download a large file from the internet."""
        url = self.config["url"]
        filename = self.config["prefix"] + country + self.config["suffix"]
        response = requests.get(url + filename, stream=True)
        with open(zip, mode="wb") as file:
            for chunk in response.iter_content(chunk_size=10 * 1024):
                file.write(chunk)

    @staticmethod
    def unzip(zip_path: Path, output_dir: Path):
        """Unzip a file to a specified location."""
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(output_dir)
