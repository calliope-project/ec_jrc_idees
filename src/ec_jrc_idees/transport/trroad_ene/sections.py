"""Transport Road energy sections."""

from pandas import DataFrame
from styleframe import StyleFrame  # type: ignore

from ec_jrc_idees.settings.config import CNF
from ec_jrc_idees.utils.generic import IDEESSection


class TotalEnergyConsumption(IDEESSection):
    """Total energy consumption wrapper."""

    EXCEL_ROW_RANGE = (17, 56)

    def process(self):
        passenger_transport = ()
        total = self.data.iloc[0,1:].sum()
        years = self.data.columns[1:]
        return super().process()



