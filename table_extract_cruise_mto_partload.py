import pandas as pd
import os

path_save = "Results/"
os.makedirs(path_save + "Excelfile", exist_ok=True)

FS_NAMES = ['fc.Fl_O', 'inlet.Fl_O', 'comp.Fl_O', 'Hex_cold.Fl_O',
            'sofc.Fl_Oc', 'sofc.Fl_Oa', 'Hex.Fl_O_hot', 'sofc_mixer.Fl_O',
            'burner.Fl_O', 'turb.Fl_O', 'pt.Fl_O', 'nozz.Fl_O']

quantities = ['tot:P', 'tot:T', 'tot:h', 'tot:S', 'stat:P', 'stat:T', 'stat:W',
              'tot:Cp', 'tot:gamma', 'stat:MN', 'stat:area', 'stat:Vsonic']

units = ['kPa', 'K', 'kJ/kg', 'J/kg/K', 'kPa', 'K', 'kg/s', 'J/kg/K',
         None, None, 'm**2', 'm/s']


def build_table(fs_names, quantities_list, row_data):
    rows = []
    for fs in fs_names:
        row = {"FlowStation": fs}
        for q in quantities_list:
            col_name = f"{fs}:{q}"
            val = row_data.get(col_name, None)
            if isinstance(val, (int, float)):
                val = round(val, 3)
            row[q] = val
        rows.append(row)
    return pd.DataFrame(rows)


def build_table_sofc(row_data):
    sofc_quantities = ['V_cell', 'i', 'W_fuel_in', 'W_fuel_out',
                       'W_fuel_excess_in_anode', 'P_stack', 'eff_cell',
                       'A_cell', 'N_cells', 'U_o', 'E_N', 'eta_ASR',
                       'T_cell', 'T_inlet', 'Hex_E', 'Hex_UA', 'Hex_h_hot_out_prelim', 'Hex_h_cold_out_prelim']
    row = {"FlowStation": "SOFC"}
    for q in sofc_quantities:
        val = row_data.get(q, None)
        if isinstance(val, (int, float)):
            val = round(val, 3)
        row[q] = val
    return pd.DataFrame([row])


def build_table_shaft(row_data):
    shaft_names = ['HP_shaft', 'LP_shaft']
    shaft_quantities = ['trq_in', 'trq_out', 'pwr_in', 'pwr_out', 'Nmech']

    rows = []
    for shaft in shaft_names:
        row = {"FlowStation": shaft}
        for q in shaft_quantities:
            col_name = f"{shaft}.{q}"
            val = row_data.get(col_name, None)
            if isinstance(val, (int, float)):
                val = round(val, 3)
            row[q] = val
        rows.append(row)
    return pd.DataFrame(rows)


def write_case_sheet(writer, sheet_name, csv_path):
    if not os.path.exists(csv_path):
        print(f"Missing file: {csv_path}")
        return False

    df = pd.read_csv(csv_path)
    data_row = df.iloc[0]

    flowstation_table = build_table(FS_NAMES, quantities, data_row)
    sofc_table = build_table_sofc(data_row)
    shaft_table = build_table_shaft(data_row)

    startrow = 0

    for table, title in zip(
        [flowstation_table, sofc_table, shaft_table],
        ["FlowStations", "SOFC", "Shaft"]
    ):
        pd.DataFrame([[title]]).to_excel(
            writer, index=False, header=False,
            sheet_name=sheet_name, startrow=startrow
        )
        startrow += 1

        table.to_excel(writer, index=False, sheet_name=sheet_name, startrow=startrow)
        startrow += len(table) + 3

    print(f"Added sheet: {sheet_name}")
    return True


def build_workbook(point_name, load_list, include_design=True):
    excel_filename = f"{point_name}_partload_sweep"
    output_excel = path_save + "Excelfile/" + excel_filename + ".xlsx"

    written_sheets = 0

    with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
        if include_design:
            design_csv = path_save + f"DESIGN_TOC_basis_for_{point_name}.csv"
            if write_case_sheet(writer, "DESIGN", design_csv):
                written_sheets += 1

        for load in load_list:
            csv_name = f"{point_name}_partload_{load}"
            csv_path = path_save + csv_name + ".csv"
            sheet_name = f"{point_name}_{load}"

            if write_case_sheet(writer, sheet_name, csv_path):
                written_sheets += 1

    if written_sheets == 0:
        print(f"No valid CSV files were found for {point_name}.")
    else:
        print(f"{point_name} Excel workbook created successfully: {output_excel}")


if __name__ == "__main__":
    # Change these if you generated different part-load percentages
    load_cases = [100, 90]#, 80, 70, 60, 50, 40, 30, 20, 10, 7]

    build_workbook("Cruise", load_cases, include_design=True)
    build_workbook("MTO", load_cases, include_design=True)