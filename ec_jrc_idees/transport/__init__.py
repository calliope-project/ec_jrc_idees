"""Parsing for the IDEES Transport sector."""

from ec_jrc_idees.utils.generic import IDEESFile


class Transport(IDEESFile):
    """Transport sector file parser."""

    def __init__(self, dir, file, mc, year: int = 2021) -> None:
        super().__init__(dir, file, mc, year)
        self.name = self.__class__.__name__

