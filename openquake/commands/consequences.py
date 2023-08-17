# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2017-2023 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.
import os
import csv
import numpy as np
from openquake.baselib import performance
from openquake.commonlib import datastore
import pandas as pd
# from tqdm import tqdm  # FIXME: add it to requirements or remove it

CD = os.path.join(os.path.dirname(__file__), os.pardir, 'risklib', 'data')
params_file = os.path.join(CD, "Hazus_Consequence_Parameters.xlsx")


def read_square_footage(xlsx):
    square_footage_df = pd.read_excel(
        xlsx, sheet_name="Square Footage", skiprows=1, index_col=0)
    return square_footage_df


def read_repair_ratio_str(xlsx):
    repair_ratio_str_df = pd.read_excel(
        xlsx, sheet_name="Structural Repair Ratios", skiprows=2, index_col=0)
    repair_ratio_str_df.index.name = "Occupancy"
    repair_ratio_str_df.rename_axis(
        "Structural Damage State", axis="columns", inplace=True)
    return repair_ratio_str_df/100


def read_repair_ratio_nsa(xlsx):
    repair_ratio_nsa_df = pd.read_excel(
        xlsx, sheet_name="NonstrAccel Repair Ratios", skiprows=2, index_col=0)
    repair_ratio_nsa_df.index.name = "Occupancy"
    repair_ratio_nsa_df.rename_axis(
        "Acceleration Sensitive Non-structural Damage State",
        axis="columns", inplace=True)
    return repair_ratio_nsa_df/100


def read_repair_ratio_nsd(xlsx):
    repair_ratio_nsd_df = pd.read_excel(
        xlsx, sheet_name="NonstrDrift Repair Ratios", skiprows=2, index_col=0)
    repair_ratio_nsd_df.index.name = "Occupancy"
    repair_ratio_nsd_df.rename_axis(
        "Drift Sensitive Non-structural Damage State",
        axis="columns", inplace=True)
    return repair_ratio_nsd_df/100


def read_repair_ratio_con(xlsx):
    repair_ratio_con_df = pd.read_excel(
        xlsx, sheet_name="Contents Damage Ratios", skiprows=2, index_col=0)
    repair_ratio_con_df.index.name = "Occupancy"
    repair_ratio_con_df.rename_axis(
        "Acceleration Sensitive Non-structural Damage State",
        axis="columns", inplace=True)
    return repair_ratio_con_df/100


def read_collapse_rate(xlsx):
    collapse_rate_df = pd.read_excel(
        xlsx, sheet_name="Collapse Rates", skiprows=1, index_col=0)
    return collapse_rate_df/100


def read_casualty_rate_in(xlsx):
    casualty_rate_in_df = pd.read_excel(
        xlsx, sheet_name="Indoor Casualty Rates",
        skiprows=1, index_col=0, header=[0, 1])
    casualty_rate_in_df.index.name = "Building Type"
    casualty_rate_in_df.columns.names = ["Damage State", "Severity Level"]
    return casualty_rate_in_df/100


def read_casualty_rate_out(xlsx):
    casualty_rate_out_df = pd.read_excel(
        xlsx, sheet_name="Outdoor Casualty Rates",
        skiprows=1, index_col=0, header=[0, 1])
    casualty_rate_out_df.index.name = "Building Type"
    casualty_rate_out_df.columns.names = ["Damage State", "Severity Level"]
    return casualty_rate_out_df/100


def read_debris_weight(xlsx):
    debris_df = pd.read_excel(
        xlsx, sheet_name="Debris", index_col=0, header=[0, 1, 2])
    debris_df.index.name = "Building Type"
    debris_df.columns.names = ["Item", "Material", "Component"]
    return debris_df


def read_repair_time(xlsx):
    repair_time_df = pd.read_excel(
        xlsx, sheet_name="Building Repair Time", skiprows=2, index_col=0)
    repair_time_df.index.name = "Occupancy"
    repair_time_df.rename_axis(
        "Structural Damage State", axis="columns", inplace=True)
    return repair_time_df


def read_recovery_time(xlsx):
    recovery_time_df = pd.read_excel(
        xlsx, sheet_name="Building Recovery Time", skiprows=2, index_col=0)
    recovery_time_df.index.name = "Occupancy"
    recovery_time_df.rename_axis(
        "Structural Damage State", axis="columns", inplace=True)
    return recovery_time_df


def read_interruption_time(xlsx):
    interruption_time_df = pd.read_excel(
        xlsx, sheet_name="Interruption Time Multipliers",
        skiprows=2, index_col=0)
    interruption_time_df.index.name = "Occupancy"
    interruption_time_df.rename_axis(
        "Structural Damage State", axis="columns", inplace=True)
    return interruption_time_df


# FIXME: add openpyxl to requirements (optional pandas requirement)
xlsx = pd.ExcelFile(params_file)
read_params = {
    "Square Footage": read_square_footage,
    "Structural Repair Ratios": read_repair_ratio_str,
    "NonstrAccel Repair Ratios": read_repair_ratio_nsa,
    "NonstrDrift Repair Ratios": read_repair_ratio_nsd,
    "Contents Damage Ratios": read_repair_ratio_con,
    "Collapse Rates": read_collapse_rate,
    "Indoor Casualty Rates": read_casualty_rate_in,
    "Outdoor Casualty Rates": read_casualty_rate_out,
    "Debris": read_debris_weight,
    "Building Repair Time": read_repair_time,
    "Building Recovery Time": read_recovery_time,
    "Interruption Time Multipliers": read_interruption_time,
}


def calculate_consequences(calc_id, output_dir):
    calc_id = datastore.get_last_calc_id() if calc_id == -1 else int(calc_id)
    dstore = datastore.read(calc_id)
    lt = 0  # structural damage
    stat = 0  # damage state mean values
    num_rlzs = len(dstore["weights"])
    assetcol = dstore['assetcol']
    taxonomies = assetcol.tagcol.taxonomy

    # Read the asset damage table from the calculation datastore
    calculation_mode = dstore['oqparam'].calculation_mode
    if calculation_mode == 'scenario_damage':
        damages = dstore['damages-rlzs']
    elif calculation_mode == 'classical_damage':
        damages = dstore['damages-stats']
    else:
        print("Consequence calculations not supported for ", calculation_mode)
        return

    # Read the various consequences tables from the spreadsheet
    square_footage_df = read_params["Square Footage"](xlsx)

    # NOTE: unused
    # repair_ratio_str_df = read_params["Structural Repair Ratios"](xlsx)
    # repair_ratio_nsa_df = read_params["NonstrAccel Repair Ratios"](xlsx)
    # repair_ratio_nsd_df = read_params["NonstrDrift Repair Ratios"](xlsx)
    # repair_ratio_con_df = read_params["Contents Damage Ratios"](xlsx)

    collapse_rate_df = read_params["Collapse Rates"](xlsx)
    casualty_rate_in_df = read_params["Indoor Casualty Rates"](xlsx)

    # NOTE: unused
    # casualty_rate_out_df = read_params["Outdoor Casualty Rates"](xlsx)

    repair_time_df = read_params["Building Repair Time"](xlsx)
    recovery_time_df = read_params["Building Recovery Time"](xlsx)
    interruption_time_df = read_params["Interruption Time Multipliers"](xlsx)
    debris_df = read_params["Debris"](xlsx)
    unit_weight_df = debris_df["Unit Weight (tons per 1,000 sqft)"]
    debris_brick_wood_pct_df = debris_df[
        "Brick, Wood, and Other Debris Generated (in Percentage of Weight)"]
    debris_concrete_steel_pct_df = debris_df[
        "Reinforced Concrete and Wrecked Steel Generated"
        " (in Percentage of Weight)"]

    # Initialize lists / dicts to store the asset level casualty estimates
    severity_levels = ["Severity 1", "Severity 2", "Severity 3", "Severity 4"]
    casualties_day = {
        "Severity 1": 0, "Severity 2": 0, "Severity 3": 0, "Severity 4": 0}
    casualties_night = {
        "Severity 1": 0, "Severity 2": 0, "Severity 3": 0, "Severity 4": 0}
    casualties_transit = {
        "Severity 1": 0, "Severity 2": 0, "Severity 3": 0, "Severity 4": 0}

    for rlzi in range(num_rlzs):
        print("Processing realization {} of {}".format(rlzi+1, num_rlzs))
        filename = os.path.join(
            output_dir, f"consequences-rlz-{rlzi:03}_{calc_id}.csv")
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            # Write the header row to the csv file
            writer.writerow(
                ["asset_ref", "number_of_buildings",
                 "value_structural", "value_nonstructural", "value_contents",
                 "occupants_day", "occupants_night", "occupants_transit",
                 "collapse_ratio", "mean_repair_time",
                 "mean_recovery_time", "mean_interruption_time",
                 "casualties_day_severity_1", "casualties_day_severity_2",
                 "casualties_day_severity_3", "casualties_day_severity_4",
                 "casualties_night_severity_1", "casualties_night_severity_2",
                 "casualties_night_severity_3", "casualties_night_severity_4",
                 "casualties_transit_severity_1",
                 "casualties_transit_severity_2",
                 "casualties_transit_severity_3",
                 "casualties_transit_severity_4",
                 "sc_Displ3", "sc_Displ30", "sc_Displ90",
                 "sc_Displ180", "sc_Displ360",
                 "sc_BusDispl30", "sc_BusDispl90",
                 "sc_BusDispl180", "sc_BusDispl360",
                 "debris_brick_wood_tons", "debris_concrete_steel_tons"])

            # FIXME: use tqdm if we can add it to the requirements
            # for asset in tqdm(assetcol):
            for asset in assetcol:
                asset_ref = asset['id'].decode()
                asset_occ, asset_typ, code_level = taxonomies[
                    asset['taxonomy']].split('-')
                if calculation_mode == 'scenario_damage':
                    # Note: engine versions <3.10 require an additional
                    # 'stat' variable as the previous output includes mean and
                    # stddev fields
                    # asset_damages = damages[asset['ordinal'], rlzi, lt, stat]
                    asset_damages = damages[asset['ordinal'], rlzi, lt]
                elif calculation_mode == 'classical_damage':
                    asset_damages = damages[asset['ordinal'], stat, rlzi]
                    asset_damages = [max(0, d) for d in asset_damages]
                asset_damage_ratios = [d/asset['value-number']
                                       for d in asset_damages]

                # Repair and recovery time estimates
                # Hazus tables 15.9, 15.10, 15.11
                repair_time = np.dot(
                    asset_damage_ratios, repair_time_df.loc[asset_occ])
                recovery_time = np.dot(
                    asset_damage_ratios, recovery_time_df.loc[asset_occ])
                interruption_time = np.dot(
                    asset_damage_ratios,
                    recovery_time_df.loc[asset_occ] * interruption_time_df.loc[
                        asset_occ])

                # Debris weight estimates
                # Hazus tables 12.1, 12.2, 12.3
                unit_weight = unit_weight_df.loc[asset_typ]
                weight_brick_wood = (
                    unit_weight["Brick, Wood and Other"]
                    * square_footage_df.loc[asset_occ].values[0] / 1000
                    * asset['value-number'])
                weight_concrete_steel = (
                    unit_weight["Reinforced Concrete and Steel"]
                    * square_footage_df.loc[asset_occ].values[0] / 1000
                    * asset['value-number'])
                debris_brick_wood_pct = debris_brick_wood_pct_df.loc[asset_typ]
                debris_concrete_steel_pct = debris_concrete_steel_pct_df.loc[
                    asset_typ]

                debris_brick_wood_str = weight_brick_wood[
                    "Structural"] * np.dot(
                        asset_damage_ratios,
                        debris_brick_wood_pct["Structural Damage State"] / 100)
                debris_brick_wood_nst = weight_brick_wood[
                    "Nonstructural"] * np.dot(
                        asset_damage_ratios,
                        debris_brick_wood_pct[
                            "Nonstructural Damage State"] / 100)
                debris_concrete_steel_str = weight_concrete_steel[
                    "Structural"] * np.dot(
                        asset_damage_ratios,
                        debris_concrete_steel_pct[
                            "Structural Damage State"] / 100)
                debris_concrete_steel_nst = weight_concrete_steel[
                    "Nonstructural"] * np.dot(
                        asset_damage_ratios,
                        debris_concrete_steel_pct[
                            "Nonstructural Damage State"] / 100)

                debris_brick_wood = (
                    debris_brick_wood_str + debris_brick_wood_nst)
                debris_concrete_steel = (
                    debris_concrete_steel_str + debris_concrete_steel_nst)

                # Estimate number of displaced occupants based on heuristics
                # provided by Murray
                sc_Displ3 = (
                    asset["occupants_night"]
                    if recovery_time > 3 and recovery_time < 30 else 0)
                sc_Displ30 = (
                    asset["occupants_night"] if recovery_time > 30 else 0)
                sc_Displ90 = (
                    asset["occupants_night"] if recovery_time > 90 else 0)
                sc_Displ180 = (
                    asset["occupants_night"] if recovery_time > 180 else 0)
                sc_Displ360 = (
                    asset["occupants_night"] if recovery_time > 360 else 0)
                sc_BusDispl30 = (
                    asset["occupants_day"] if recovery_time > 30 else 0)
                sc_BusDispl90 = (
                    asset["occupants_day"] if recovery_time > 90 else 0)
                sc_BusDispl180 = (
                    asset["occupants_day"] if recovery_time > 180 else 0)
                sc_BusDispl360 = (
                    asset["occupants_day"] if recovery_time > 360 else 0)

                # Split complete damage state into collapse and non-collapse
                # This distinction is then used for the casualty estimates
                # Collapse rates given complete damage are from Hazus table
                # 13.8
                collapse_rate = collapse_rate_df.loc[asset_typ].values[0]
                dmg = {
                    "Slight Damage": asset_damage_ratios[1],
                    "Moderate Damage": asset_damage_ratios[2],
                    "Extensive Damage": asset_damage_ratios[3],
                    "Complete Damage (No Collapse)": (
                        asset_damage_ratios[4] * (1 - collapse_rate)),
                    "Complete Damage (With Collapse)": (
                        asset_damage_ratios[4] * collapse_rate)
                    }
                collapse_ratio = dmg["Complete Damage (With Collapse)"]
                collapse_ratio_str = "{:.2e}".format(
                    collapse_ratio) if collapse_ratio else '0'

                # Estimate casualties (day/night/transit) at four
                # severity levels
                # Hazus tables 13.3, 13.4, 13.5, 13.6, 13.7
                for severity_level in severity_levels:
                    casualty_ratio = np.dot(
                        list(dmg.values()),
                        casualty_rate_in_df.loc[asset_typ][:, severity_level])
                    casualties_day[severity_level] = (
                        casualty_ratio * asset["occupants_day"])
                    casualties_night[severity_level] = (
                        casualty_ratio * asset["occupants_night"])
                    casualties_transit[severity_level] = (
                        casualty_ratio * asset["occupants_transit"])

                # Write all consequence estimates for this asset to the csv
                # file
                writer.writerow(
                    [asset_ref,
                     "{0:,.1f}".format(asset['value-number']),
                     "{0:,.1f}".format(asset["value-structural"]),
                     "{0:,.1f}".format(asset["value-nonstructural"]),
                     "{0:,.1f}".format(asset["value-contents"]),
                     "{0:,.1f}".format(asset["occupants_day"]),
                     "{0:,.1f}".format(asset["occupants_night"]),
                     "{0:,.1f}".format(asset["occupants_transit"]),
                     collapse_ratio_str,
                     "{0:,.1f}".format(repair_time),
                     "{0:,.1f}".format(recovery_time),
                     "{0:,.1f}".format(interruption_time),
                     "{0:,.2f}".format(casualties_day["Severity 1"]),
                     "{0:,.2f}".format(casualties_day["Severity 2"]),
                     "{0:,.2f}".format(casualties_day["Severity 3"]),
                     "{0:,.2f}".format(casualties_day["Severity 4"]),
                     "{0:,.2f}".format(casualties_night["Severity 1"]),
                     "{0:,.2f}".format(casualties_night["Severity 2"]),
                     "{0:,.2f}".format(casualties_night["Severity 3"]),
                     "{0:,.2f}".format(casualties_night["Severity 4"]),
                     "{0:,.2f}".format(casualties_transit["Severity 1"]),
                     "{0:,.2f}".format(casualties_transit["Severity 2"]),
                     "{0:,.2f}".format(casualties_transit["Severity 3"]),
                     "{0:,.2f}".format(casualties_transit["Severity 4"]),
                     "{0:,.1f}".format(sc_Displ3),
                     "{0:,.1f}".format(sc_Displ30),
                     "{0:,.1f}".format(sc_Displ90),
                     "{0:,.1f}".format(sc_Displ180),
                     "{0:,.1f}".format(sc_Displ360),
                     "{0:,.1f}".format(sc_BusDispl30),
                     "{0:,.1f}".format(sc_BusDispl90),
                     "{0:,.1f}".format(sc_BusDispl180),
                     "{0:,.1f}".format(sc_BusDispl360),
                     "{0:,.1f}".format(debris_brick_wood),
                     "{0:,.1f}".format(debris_concrete_steel),
                     ])
        print(f'Saved {filename}')


def main(calc_id: int = -1,
         output_dir='.'):
    """
    TODO
    """
    with performance.Monitor('consequences', measuremem=True) as mon:
        calculate_consequences(calc_id, output_dir)
    if mon.duration > 1:
        print(mon)


main.calc_id = 'number of the calculation'
main.output_dir = 'directory where to write the consequence data'
