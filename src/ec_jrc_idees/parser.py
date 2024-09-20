"""Easy JRC processing."""

import importlib.resources
import zipfile
from collections import namedtuple
from pathlib import Path

import requests
import yaml

Metadata: tuple[int, str, str] = namedtuple(
    "Metadata", ["version", "file", "country_eurostat"]
)


class EasyIDEES:
    """Easily process JRC-IDEES DATA."""

    def __init__(self, version: str | int) -> None:
        data_path = importlib.resources.files("ec_jrc_idees") / "data" / "parser.yaml"
        config = yaml.safe_load(data_path.read_text())
        self.config: dict = config["version_specific"][str(version)]
        self.config = self.config | config["generic"]

    @staticmethod
    def _get_filename_metadata(filename: str):
        data = filename.split("-")[-1].split("_")
        metadata = Metadata(int(data[0]), data[1], data[-1].split(".")[0])
        return metadata

    def process_files(self, dir: Path):
        for element in dir.iterdir():
            if element.is_file():
                metadata = self._get_filename_metadata(element.name)

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
