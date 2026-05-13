import pandas as pd

path_save="Results/"


# Read CSV file
# df = pd.read_csv(path_save+filename+'.csv')
FS_NAMES = ['fc.Fl_O', 'inlet.Fl_O', 'comp.Fl_O','Hex_cold.Fl_O',
            'sofc.Fl_Oc', 'sofc.Fl_Oa', 'Hex.Fl_O_hot', 'sofc_mixer.Fl_O', 'burner.Fl_O', 'turb.Fl_O', 'pt.Fl_O', 'nozz.Fl_O']
quantities = ['tot:P', 'tot:T', 'tot:h', 'tot:S', 'stat:P', 'stat:T', 'stat:W', 'tot:Cp', 'tot:gamma', 'stat:MN',
         'stat:area', 'stat:Vsonic']
units = ['kPa', 'K', 'kJ/kg', 'J/kg/K', 'kPa', 'K', 'kg/s', 'J/kg/K', None, None, 'm**2', 'm/s']


# Take the second row as data
# data_row = df.iloc[0]  # first row of actual data

# Build clean table
def build_table(fs_names, quantities_list, row_data, table_name):
    rows = []
    for fs in fs_names:
        row = {"FlowStation": fs}
        for q in quantities_list:
            col_name = f"{fs}:{q}"
            val = data_row.get(col_name, None)
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
            val = data_row.get(col_name, None)
            if q == 'V_cell':
                print(val)
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
            val = data_row.get(col_name, None)
            if isinstance(val, (int, float)):
                val = round(val, 3)
            row[q] = val
        rows.append(row)
    return pd.DataFrame(rows)



# --- 2. SOFC Data ---
SOFC_NAMES = ['SOFC']
SOFC_QUANTITIES = ['V_cell','i','W_fuel_in','W_fuel_out','W_fuel_excess_in_anode','P_stack','eff_cell','A_cell','N_cells','E_N','T_cell','Hex_E','Hex_UA']  # example subset


# --- 3. Shaft Data ---
SHAFT_NAMES = ['HP_shaft', 'LP_shaft']
SHAFT_QUANTITIES = ['trq_in','trq_out','pwr_in','pwr_out','Nmech']  # replace with your actual shaft quantities

CONDITIONS = ['DESIGN','TOC','Cruise','MTO']#'TOC',

# Create Excel workbook
T4 = 1100
N_cells = 40000
power_fraction = 0.65
PR = 20
Vcell = 1.0
des_pt='TOC'
# excel_filename = 'DES_pt_' + des_pt + '_T4_' + str(T4) + '_Vcell_' + str(Vcell) + '_PR_' + str(PR)
excel_filename = 'DES_pt_'+des_pt+'_PFrac_'+str(power_fraction)+'_T4_'+str(T4)+'_Ncells_'+str(N_cells)+'_PR_'+str(PR)+'ncell_bal_tsofcout'# + '_TH2_300K'
# excel_filename = '_pfrac0.65_v4'
with pd.ExcelWriter(path_save+"Excelfile/"+excel_filename+".xlsx", engine="openpyxl") as writer:
    for condition in CONDITIONS:
        # Read CSV for this condition
        pt = condition
        filename = pt+excel_filename
        df = pd.read_csv(path_save+filename+'.csv')
        data_row = df.iloc[0]  # first row has the data

        # Build tables
        flowstation_table = build_table(FS_NAMES, quantities, data_row, "FlowStations")
        sofc_table = build_table_sofc(SOFC_NAMES, SOFC_QUANTITIES, data_row, "SOFC")
        shaft_table = build_table_shaft(SHAFT_NAMES, SHAFT_QUANTITIES, data_row, "Shaft")

        # Start writing to sheet
        startrow = 0

        for table, name in zip([flowstation_table, sofc_table, shaft_table],
                               ["FlowStations", "SOFC", "Shaft"]):
            # Table title
            pd.DataFrame([[name]]).to_excel(writer, index=False, header=False,
                                            sheet_name=condition, startrow=startrow)
            startrow += 1

            # Table data
            table.to_excel(writer, index=False, sheet_name=condition, startrow=startrow)
            startrow += len(table) + 3  # leave space between tables

print("Excel workbook with Design, Cruise, MTO sheets created successfully!")
