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

# In their wisdom, the JRC decided to change the naming of vehicles between versions
TWO_WHEEL_TEXT = ["two-wheelers", "2-wheelers"]


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


def get_vehicle_type_aggregates(idees_text: pd.Series, style: StyleFrame):
    """Identify rows with vehicle subtypes."""
    indent = utils.get_style_feature(style, "indent", idees_text.index)
    vehicle_types = idees_text.loc[indent[indent == VEHICLE_TYPE_INDENT].index]
    return vehicle_types.str.split("(").str[0].str.rstrip()


def get_vehicle_subtype_aggregates(idees_text: pd.Series, style: StyleFrame):
    """Identify rows with vehicle subtypes."""
    indent = utils.get_style_feature(style, "indent", idees_text.index)

    vehicle_types = get_vehicle_type_aggregates(idees_text, style)
    vehicle_subtypes = idees_text.loc[indent[indent == VEHICLE_SUBTYPE_INDENT].index]
    vehicle_subtypes = vehicle_subtypes[~vehicle_subtypes.str.contains("of which")]
    vehicle_subtypes = vehicle_subtypes.str.split("(").str[0].str.rstrip()

    # Fix messy categories
    two_wheel = vehicle_types[vehicle_types.str.contains("|".join(TWO_WHEEL_TEXT))]
    if len(two_wheel) != 1:
        raise ValueError("Expected unique two-wheel category.")
    two_wheel_idx = two_wheel.index[0]
    two_wheel_fuel = "Gasoline"
    vehicle_subtypes[two_wheel_idx] = two_wheel_fuel + " engine"

    return VehicleAggregates(vehicle_types, vehicle_subtypes)


class RoadSection(IDEESSection):
    """Adds generic calculations specific to Road transport."""

    @override
    def check(self):
        years = self.annual_df.columns
        aggregates = [
            get_total_aggregates(self.idees_text, self.style),
            get_category_aggregates(self.idees_text, self.style),
            get_vehicle_type_aggregates(self.idees_text, self.style)
        ]
        for agg in aggregates:
            self.check_subsection(years, agg.index)


class RoadVKM(RoadSection):
    """Road activity per vehicle processing."""

    EXCEL_ROW_RANGE = (30, 55)
    VALID_VERSIONS = (2021, 2015)

    @override
    def tidy_up(self):
        years = self.annual_df.columns

        # Build a template row to add data to
        template = pd.Series(self.cnf["template_columns"])
        template = pd.concat([template, pd.Series(None, index=years)])

        # Get aggregate sections
        total_aggr = get_total_aggregates(self.idees_text, self.style)
        categories = get_category_aggregates(self.idees_text, self.style)
        vehicle_types, vehicle_subtypes = get_vehicle_subtype_aggregates(
            self.idees_text, self.style
        )

        tidy_df = pd.DataFrame(columns=template.index)
        for row in self.annual_df.index:
            entry = template.copy()
            if row in total_aggr or row in categories:
                # Aggregate rows unrelated to tech types should be skipped.
                continue
            if row in vehicle_types and not any(
                [i in vehicle_types[row] for i in TWO_WHEEL_TEXT]
            ):
                # Vehicle type aggregates shouls also be skipped, except two-wheelers.
                continue

            # Identify the characteristics of this row.
            entry[years] = self.annual_df.loc[row]
            entry["category"] = self.find_subsection(row, categories)
            entry["vehicle_type"] = self.find_subsection(row, vehicle_types)
            entry["vehicle_subtype"] = self.find_subsection(row, vehicle_subtypes)

            if None in entry:
                raise ValueError(f"Entry not fully filled: {entry}")
            tidy_df.loc[row] = entry
        self.tidy_df = tidy_df


class RoadEnergyConsumption(RoadSection):
    """Road Energy Consumption processing."""

    EXCEL_ROW_RANGE = (17, 56)
    VALID_VERSIONS = (2015, 2021)

    @override
    def tidy_up(self):
        years = self.annual_df.columns

        # Build a template row to add data to
        template = pd.Series(self.cnf["template_columns"])
        template = pd.concat([template, pd.Series(None, index=years)])

        # Get aggregated sections
        total_aggr = get_total_aggregates(self.idees_text, self.style)
        categories = get_category_aggregates(self.idees_text, self.style)
        vehicle_types, vehicle_subtypes = get_vehicle_subtype_aggregates(
            self.idees_text, self.style
        )
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
            if row in vehicle_types and not any(
                [i in vehicle_types[row] for i in TWO_WHEEL_TEXT]
            ):
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


# Same processing as Road activity, so inheritance makes sense.
class RoadTotalStock(RoadVKM):
    """Road activity per vehicle processing."""

    EXCEL_ROW_RANGE = (57, 82)
    VALID_VERSIONS = (2021, 2015)


class RoadTotalStockTestEfficiency(RoadVKM):
    """Road activity per vehicle processing."""

    EXCEL_ROW_RANGE = (88, 113)
    VALID_VERSIONS = (2021, 2015)

    @override
    def get_annual_dataframe(self) -> pd.DataFrame:
        year_data = self.dirty_df.select_dtypes("number")
        return year_data


class RoadTotalStockTestDiscrepancy(RoadVKM):
    """Road activity per vehicle processing."""

    EXCEL_ROW_RANGE = (115, 140)
    VALID_VERSIONS = (2021, 2015)


class TrRoad_act(IDEESSheet):
    """Transport Road energy."""

    SHEET_NAME = "TrRoad_act"
    SECTION_CLEANERS = [RoadVKM, RoadTotalStock]

    @override
    def check(self):
        # TODO: add checks once all transport files are processed.
        pass


class TrRoad_ene(IDEESSheet):
    """Transport Road energy."""

    SHEET_NAME = "TrRoad_ene"
    SECTION_CLEANERS = [RoadEnergyConsumption]

    @override
    def check(self):
        # TODO: add checks once all transport files are processed.
        pass


class TrRoad_tech(IDEESSheet):
    """Transport Road energy."""

    SHEET_NAME = "TrRoad_tech"
    SECTION_CLEANERS = [RoadTotalStockTestEfficiency]

    @override
    def check(self):
        # TODO: add checks once all transport files are processed.
        pass


class TransportFile(IDEESFile):
    """Processing of transport data."""

    NAME = "Transport"
    SHEET_CLEANERS = [TrRoad_act, TrRoad_ene, TrRoad_tech]

    @override
    def check(self):
        # TODO: add checks once all transport files are processed.
        pass
