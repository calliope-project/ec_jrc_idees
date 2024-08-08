"""Manage JRC data."""

from pathlib import Path

from ec_jrc_idees.utils import SHEET_CNF, CleanSheet


class EasyIDEES:
    """Main JRC-IDES handler."""

    def __init__(self, idees_path: str | Path, ec_path: str | Path) -> None:
        self.idees_path: Path = Path(idees_path)
        self.ec_path: Path = Path(ec_path)

    def download(self):
        """Download a file from the JRC website."""
        ...

    def process(self):
        """Get a cleaned dataframe."""
        mc = "FR"
        for file, file_config in SHEET_CNF.items():
            if file_config:
                for sheet, sheet_config in file_config.items():
                    clean_sheet = CleanSheet(self.idees_path, mc, file, sheet)

