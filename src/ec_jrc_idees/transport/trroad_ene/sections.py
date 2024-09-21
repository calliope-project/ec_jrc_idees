"""Transport Road energy sections."""


from ec_jrc_idees._utils.generic import IDEESSection


class TotalEnergyConsumption(IDEESSection):
    """Total energy consumption wrapper."""

    EXCEL_ROW_RANGE = (17, 56)

    def process(self):
        passenger_transport = ()
        total = self.data.iloc[0,1:].sum()
        years = self.data.columns[1:]
        return super().process()



