"""Processing of transport files."""

from typing import override

import pandas as pd

from ec_jrc_idees import utils
from ec_jrc_idees.generics import IDEESFile, IDEESSection, IDEESSheet

TOTAL_INDENT = 0
CATEGORY_INDENT = 1
TYPE_INDENT = 2
SUBTYPE_INDENT = 3


class RoadEnergyConsumption(IDEESSection):
    """Road Energy Consumption processing."""

    NAME = "RoadEnergyConsumption"
    EXCEL_ROW_RANGE = (17, 56)



    @override
    def tidy_up(self):
        annual_df = self.get_annual_dataframe()
        years = annual_df.columns
        text_col = self.get_text_column()
        units = utils.get_unit_in_parenthesis(text_col.iloc[0])

        preset = pd.Series(self.cnf["cols"])
        preset["units"] = units
        preset = pd.concat([preset, pd.Series(None, index=years)])

        indent = utils.get_style_feature(self.style, "indent", text_col.index)

        # Get aggregated sections
        total = text_col.loc[indent[indent == TOTAL_INDENT].index]
        category = text_col.loc[indent[indent == CATEGORY_INDENT].index]

        # Get useful data sections
        vehicle_type = text_col.loc[indent[indent == TYPE_INDENT].index]
        vehicle_type = vehicle_type.str.split("(").str[0].str.rstrip()

        vehicle_subtype = text_col.loc[indent[indent == SUBTYPE_INDENT].index]
        vehicle_subtype = vehicle_subtype[~vehicle_subtype.str.contains("of which")]
        vehicle_subtype = vehicle_subtype.str.split("(").str[0].str.rstrip()

        # Fix messy subtypes
        two_wheel = vehicle_type[vehicle_type.str.contains("two-wheelers")]
        if len(two_wheel) != 1:
            raise ValueError("Expected unique two-wheel category.")
        two_wheel_idx = two_wheel.index[0]
        two_wheel_fuel = text_col[two_wheel_idx].split("(")[1].split(")")[0]
        vehicle_subtype[two_wheel_idx] = two_wheel_fuel + " engine"

        carrier = self.find_carrier(vehicle_subtype)

        of_which = text_col.loc[text_col.str.contains("of which")]
        if set(of_which.index) & set(carrier.index):
            raise ValueError("Carriers and 'of which' compliments must not overlap.")

        tidy_df = pd.DataFrame(columns=preset.index)
        for row in annual_df.index:
            entry = preset.copy()
            # Aggregated rows should be skipped, except for special cases.
            if row in total or row in category:
                continue
            if row in vehicle_type and "two-wheelers" not in vehicle_type[row]:
                continue

            entry[years] = annual_df.loc[row]
            entry["transport_category"] = self.find_subsection(row, category)
            entry["vehicle_type"] = self.find_subsection(row, vehicle_type)
            entry["vehicle_subtype"] = self.find_subsection(row, vehicle_subtype)
            entry["carrier"] = self.find_subsection(row, carrier)
            if row in of_which:
                if "bio" in of_which[row]:
                    entry["carrier"] = "Bio" + entry["carrier"]
                elif "electricity" in of_which[row]:
                    entry["carrier"] = "Electricity"
                else:
                    raise ValueError("Could not identify carrier.")
                carrier_idx = self.find_subsection(row, carrier, find="index")
                tidy_df.loc[carrier_idx, years] -= entry[years]
            if None in entry:
                raise ValueError(f"Entry not fully filled: {entry}.")
            tidy_df.loc[row] = entry

        self.tidy_df = tidy_df
        self.check_subsection(years, vehicle_type.index)

    @staticmethod
    def find_carrier(vehicle_subtype: pd.Series) -> pd.Series:
        carriers = pd.Series(index=vehicle_subtype.index, dtype="object")
        for idx in carriers.index:
            subtype = vehicle_subtype[idx]
            if "Gasoline" in subtype or "Plug-in" in subtype:
                carriers[idx] = "Gasoline"
            elif any([i in subtype for i in ["Diesel", "Domestic", "International"]]):
                carriers[idx] = "Diesel"
            elif "LPG" in subtype:
                carriers[idx] = "LPG"
            elif "Battery" in subtype:
                carriers[idx] = "Electricity"
            elif "Natural gas" in subtype:
                carriers[idx] = "Natural gas"
            else:
                raise ValueError(f"Could not identify carrier for '{subtype}'.")
        return carriers


class TrRoad_ene(IDEESSheet):
    """Transport Road energy."""

    NAME = "TrRoad_ene"
    TARGET_SECTIONS = [RoadEnergyConsumption]


class TransportFile(IDEESFile):
    """Processing of transport data."""

    NAME = "Transport"
    TARGET_SHEETS = [TrRoad_ene]
