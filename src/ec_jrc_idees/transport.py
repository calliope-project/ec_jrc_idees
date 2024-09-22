"""Processing of transport files."""

from typing import NamedTuple, override

import pandas as pd
from styleframe import StyleFrame

from ec_jrc_idees import utils
from ec_jrc_idees.generics import IDEESFile, IDEESSection, IDEESSheet

TOTAL_INDENT = 0
CATEGORY_INDENT = 1
VEHICLE_TYPE_INDENT = 2
VEHICLE_SUBTYPE_INDENT = 3


class VehicleAggregates(NamedTuple):
    """Vehicle types (passenger cars) and subtypes (gasoline engine) handler."""

    vehicle_types: pd.Series
    vehicle_supbtypes: pd.Series


def get_total_aggregates(idees_text: pd.Series, style: StyleFrame):
    """Identify rows with totals, for checksums."""
    indent = utils.get_style_feature(style, "indent", idees_text.index)
    return idees_text.loc[indent[indent == TOTAL_INDENT].index]


def get_category_aggregates(idees_text: pd.Series, style: StyleFrame):
    """Identify rows with category aggregates (e.g., Passenger transport)."""
    indent = utils.get_style_feature(style, "indent", idees_text.index)
    return idees_text.loc[indent[indent == CATEGORY_INDENT].index]


def get_vehicle_aggregates(idees_text: pd.Series, style: StyleFrame):
    """Identify rows with vehicle subtypes."""
    indent = utils.get_style_feature(style, "indent", idees_text.index)

    vehicle_types = idees_text.loc[indent[indent == VEHICLE_TYPE_INDENT].index]
    vehicle_types = vehicle_types.str.split("(").str[0].str.rstrip()

    vehicle_subtypes = idees_text.loc[indent[indent == VEHICLE_SUBTYPE_INDENT].index]
    vehicle_subtypes = vehicle_subtypes[~vehicle_subtypes.str.contains("of which")]
    vehicle_subtypes = vehicle_subtypes.str.split("(").str[0].str.rstrip()

    # Fix messy categories
    two_wheel = vehicle_types[vehicle_types.str.contains("two-wheelers")]
    if len(two_wheel) != 1:
        raise ValueError("Expected unique two-wheel category.")
    two_wheel_idx = two_wheel.index[0]
    two_wheel_fuel = idees_text[two_wheel_idx].split("(")[1].split(")")[0]
    vehicle_subtypes[two_wheel_idx] = two_wheel_fuel + " engine"

    return VehicleAggregates(vehicle_types, vehicle_subtypes)


class RoadEnergyConsumption(IDEESSection):
    """Road Energy Consumption processing."""

    NAME = "RoadEnergyConsumption"
    EXCEL_ROW_RANGE = (17, 56)

    @override
    def tidy_up(self):
        years = self.annual_df.columns
        units = utils.get_unit_in_parenthesis(self.idees_text.iloc[0])

        # Build a template row to add data to
        template = pd.Series(self.cnf["template_columns"])
        template["units"] = units
        template = pd.concat([template, pd.Series(None, index=years)])

        # Get aggregated sections
        total_aggr = get_total_aggregates(self.idees_text, self.style)
        categories = get_category_aggregates(self.idees_text, self.style)
        vehicle_types, vehicle_subtypes = get_vehicle_aggregates(self.idees_text, self.style)
        carriers = self._find_carriers(vehicle_subtypes)

        of_which = self.idees_text.loc[self.idees_text.str.contains("of which")]
        if set(of_which.index) & set(carriers.index):
            raise ValueError("Carriers and 'of which' compliments must not overlap.")

        tidy_df = pd.DataFrame(columns=template.index)
        for row in self.annual_df.index:
            entry = template.copy()
            # Aggregated rows should be skipped, except for special cases.
            if row in total_aggr or row in categories:
                continue
            if row in vehicle_types and "two-wheelers" not in vehicle_types[row]:
                continue

            entry[years] = self.annual_df.loc[row]
            entry["category"] = self.find_subsection(row, categories)
            entry["vehicle_type"] = self.find_subsection(row, vehicle_types)
            entry["vehicle_subtype"] = self.find_subsection(row, vehicle_subtypes)
            entry["carrier"] = self.find_subsection(row, carriers)
            if row in of_which:
                if "bio" in of_which[row]:
                    entry["carrier"] = "Bio" + entry["carrier"]
                elif "electricity" in of_which[row]:
                    entry["carrier"] = "Electricity"
                else:
                    raise ValueError("Could not identify carrier.")
                carrier_idx = self.find_subsection(row, carriers, find="index")
                tidy_df.loc[carrier_idx, years] -= entry[years]
            if None in entry:
                raise ValueError(f"Entry not fully filled: {entry}.")
            tidy_df.loc[row] = entry

        self.tidy_df = tidy_df
        self.check_subsection(years, vehicle_types.index)

    @staticmethod
    def _find_carriers(vehicle_subtypes: pd.Series) -> pd.Series:
        carriers = pd.Series(index=vehicle_subtypes.index, dtype="object")
        for idx in carriers.index:
            subtype = vehicle_subtypes[idx]
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
