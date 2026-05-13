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


def build_table(fs_names, quantities_list, row_data, table_name):
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


def build_table_sofc(fs_names, quantities_list, row_data, table_name):
    rows = []
    for fs in fs_names:
        row = {"FlowStation": fs}
        for q in quantities_list:
            col_name = f"{q}"
            val = row_data.get(col_name, None)
            if isinstance(val, (int, float)):
                val = round(val, 3)
            row[q] = val
        rows.append(row)
    return pd.DataFrame(rows)


def build_table_shaft(fs_names, quantities_list, row_data, table_name):
    rows = []
    for fs in fs_names:
        row = {"FlowStation": fs}
        for q in quantities_list:
            col_name = f"{fs}.{q}"
            val = row_data.get(col_name, None)
            if isinstance(val, (int, float)):
                val = round(val, 3)
            row[q] = val
        rows.append(row)
    return pd.DataFrame(rows)


SOFC_NAMES = ['SOFC']
SOFC_QUANTITIES = ['V_cell', 'i', 'W_fuel_in', 'W_fuel_out',
                   'W_fuel_excess_in_anode', 'P_stack', 'eff_cell',
                   'A_cell', 'N_cells', 'E_N', 'T_cell', 'Hex_E', 'Hex_UA']

SHAFT_NAMES = ['HP_shaft', 'LP_shaft']
SHAFT_QUANTITIES = ['trq_in', 'trq_out', 'pwr_in', 'pwr_out', 'Nmech']

#CONDITIONS = [ 'TOC_80', 'TOC_90', 'TOC_100']
#CSV_FILES = [ 'TOC_partload_80', 'TOC_partload_90', 'TOC_partload_100']

#CONDITIONS = ['TOC_40','TOC_50','TOC_60','TOC_70','TOC_80', 'TOC_90', 'TOC_100','DESIGN']
#CSV_FILES = ['TOC_partload_40','TOC_partload_50','TOC_partload_60','TOC_partload_70','TOC_partload_80',
             #'TOC_partload_90', 'TOC_partload_100', 'DESIGN_TOC_partload_sweep']

CONDITIONS = ['TOC_50', 'TOC_60', 'TOC_70', 'TOC_80', 'TOC_90', 'TOC_100', 'DESIGN']
CSV_FILES = ['TOC_partload_50', 'TOC_partload_60', 'TOC_partload_70','TOC_partload_80','TOC_partload_90', 'TOC_partload_100', 'DESIGN_TOC_partload_sweep']


#CONDITIONS = ['TOC_10','TOC_20','TOC_30','TOC_40','TOC_50','TOC_60','TOC_70','TOC_80','TOC_90', 'TOC_100', 'DESIGN']
#CSV_FILES = ['TOC_partload_10','TOC_partload_20','TOC_partload_30','TOC_partload_40',
             #'TOC_partload_50','TOC_partload_60','TOC_partload_70','TOC_partload_80','TOC_partload_90', 'TOC_partload_100',
             #'DESIGN_TOC_partload_sweep']

excel_filename = 'TOC_partload_sweep'
output_excel = path_save + "Excelfile/" + excel_filename + ".xlsx"

written_sheets = 0

with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
    for condition, csv_name in zip(CONDITIONS, CSV_FILES):
        csv_path = path_save + csv_name + ".csv"

        if not os.path.exists(csv_path):
            print(f"Missing file: {csv_path}")
            continue

        df = pd.read_csv(csv_path)
        data_row = df.iloc[0]

        flowstation_table = build_table(FS_NAMES, quantities, data_row, "FlowStations")
        sofc_table = build_table_sofc(SOFC_NAMES, SOFC_QUANTITIES, data_row, "SOFC")
        shaft_table = build_table_shaft(SHAFT_NAMES, SHAFT_QUANTITIES, data_row, "Shaft")

        startrow = 0

        for table, name in zip(
            [flowstation_table, sofc_table, shaft_table],
            ["FlowStations", "SOFC", "Shaft"]
        ):
            pd.DataFrame([[name]]).to_excel(
                writer, index=False, header=False,
                sheet_name=condition, startrow=startrow
            )
            startrow += 1

            table.to_excel(writer, index=False, sheet_name=condition, startrow=startrow)
            startrow += len(table) + 3

        written_sheets += 1
        print(f"Added sheet: {condition}")

if written_sheets == 0:
    print("No valid part-load CSV files were found.")
else:
    print(f"Part-load Excel workbook created successfully: {output_excel}")


