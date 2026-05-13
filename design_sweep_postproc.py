import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.lines as mlines
import pandas as pd
import numpy as np
import os

path_save="Results_H2_873K_repeat/"#

PR=20
power_fraction = 0.85
T4_list = [1000, 1200]#[1000, 1200, 1300,1400,1500, 1600, 1800]
power_fraction_list = [0.25,0.45,0.65,0.85]#[0.85, 0.65,0.45]
N_cells_list = [70000, 80000,100000,120000,160000]
PR_list = [10, 15, 20, 25]
Des_pt = 'TOC'
condition = 'DESIGN'


def carpet_plots():
    # Create empty grids
    Z1 = np.zeros((len(T4_list), len(N_cells_list)))  # quantity 1
    Z2 = np.zeros((len(T4_list), len(N_cells_list)))  # quantity 2

    for i, T4 in enumerate(T4_list):
        for j, N_cells in enumerate(N_cells_list):

            filename = f"{condition}DES_pt_{Des_pt}_PFrac_{power_fraction}_T4_{T4}_Ncells_{N_cells}_PR_{PR}"
            full_path = path_save + filename + ".csv"

            if not os.path.exists(full_path):
                print(f"Missing: {full_path}")
                Z1[i, j] = np.nan
                Z2[i, j] = np.nan
                continue

            df = pd.read_csv(full_path)
            row = df.iloc[0]

            #CHANGE THESE to your column names
            W_fuel = row['W_fuel_in'] #g/s
            Power_lpshaft = row['LP_shaft.pwr_in'] # W
            PSFC = (W_fuel*3600)/(Power_lpshaft*1e-3) #g/kWh
            T_sofc_out = (row['sofc.Fl_Oc:tot:T']+row['sofc.Fl_Oa:tot:T'])/2
            #checks
            V_cell = row['V_cell']
            if V_cell>0 and V_cell<2 and T_sofc_out<2000:
                Z1[i, j] = PSFC
                Z2[i, j] = T_sofc_out
            else:
                continue


    plt.figure(figsize=(8,6))

    plt.figure(figsize=(8,6))

    for i, T4 in enumerate(T4_list):
        plt.plot(Z2[i, :], Z1[i, :], marker='o', label=f"T4={T4}")

    for j, N_cells in enumerate(N_cells_list):
        plt.plot(Z2[:, j], Z1[:, j], linestyle='--', color='gray')

    # for i, T4 in enumerate(T4_list):
    #     plt.text(Z2[i, -1], Z1[i, -1], f"{T4}", fontsize=8)
    #
    # for j, N_cells in enumerate(N_cells_list):
    #     plt.text(Z2[-1, j], Z1[-1, j], f"{N_cells}", fontsize=8)

    plt.xlabel("T SOFC out [K]")   # your X variable
    plt.ylabel("PSFC [g/kWh]")        # your Y variable
    plt.title("Carpet Plot")

    plt.legend()
    plt.grid(True)

    plt.show()
def plot_func(df_all, var_name, label):
    pathsave = "Images/"
    label_size = 18
    legend_label_size = 12
    tick_size = 15
    # Sorted T4 values (important for color mapping)
    T4_values = sorted(df_all["T4"].unique())
    n = len(T4_values)

    # Dark blue → red colormap (avoid very light colors)
    # cmap = plt.cm.coolwarm
    # colors = cmap(np.linspace(0.15, 0.85, n))  # trims bright ends

    # Dark, scientific palette (Viridis subset)
    # colors = plt.cm.viridis(np.linspace(0.1, 0.9, df_all["T4"].nunique()))#['#1b1b1b', '#00429d', '#2a9d8f', '#e9c46a', '#d62828']#
    # Dark, balanced colors (same intensity family)
    colors = [#"#8B008B",  # dark magenta
        "#006400",  # dark green
              "#1B3A6F",  # dark blue
              "#8B0000",  # dark red

              ]

    fig, ax1 = plt.subplots(figsize=(8, 5))

    for i, ((T4,T_H2), group) in enumerate(df_all.groupby(["T4","T_H2"])):
        group = group.sort_values("power_fraction")

        if var_name == "sofc_params":
            # Left axis → Vcell
            ax1.plot(
                group["power_fraction"],
                group["V_cell"],
                marker='o',
                linewidth=2,
                markersize=5,
                color=colors[i],
                linestyle='-',
                label=f"$T_4 = {T4}$K"
            )
        elif var_name =="T_sofc_out":
            if T_H2==300:
                linecolor = colors[i]
                leg_label  = f"$T_4 = {T4}$K,"+"T$_{H_2}$=300K"
            else:
                linecolor = colors[i]
                leg_label = f"$T_4 = {T4}$K"
            ax1.plot(
                group["power_fraction"],
                group[var_name],
                marker='o',
                linewidth=2,
                markersize=5,
                color=linecolor,
                linestyle='-',
                label=leg_label
            )
            ax1.plot(
                group["power_fraction"],
                group["T_comb_in"],
                marker='s',
                linewidth=2,
                markersize=5,
                color=linecolor,
                linestyle='--',
                # label=f"$T_4 = {T4}$K"
            )
        else:
            ax1.plot(
                group["power_fraction"],
                group[var_name],
                marker='o',
                linewidth=2,
                markersize=5,
                color=colors[i],
                label=f"$T_4 = {T4}$K"
            )

    # Special handling for SOFC params
    if var_name == "sofc_params":
        ax2 = ax1.twinx()

        for i, (T4, group) in enumerate(df_all.groupby("T4")):
            group = group.sort_values("power_fraction")

            # Right axis → current density i
            ax2.plot(
                group["power_fraction"],
                group["i"],
                marker='s',
                linewidth=2,
                markersize=5,
                linestyle='--',
                color=colors[i],
                # label=f"$T_4 = {T4}$K (i)"
            )

        ax1.set_ylabel("Cell Voltage [V]", fontsize=label_size)
        ax2.set_ylabel("Current density [A/m$^2$]", fontsize=label_size)
    elif var_name=="lambda_FC":
        ax2 = ax1.twinx()

        for i, (T4, group) in enumerate(df_all.groupby("T4")):
            group = group.sort_values("power_fraction")

            # Right axis → current density i
            ax2.plot(
                group["power_fraction"],
                group["Uf"],
                marker='s',
                linewidth=2,
                markersize=5,
                linestyle='--',
                color=colors[i],
                # label=f"$T_4 = {T4}$K (i)"
            )

        ax1.set_ylabel("Excess Air Ratio ($\lambda$) [-]", fontsize=label_size)
        ax2.set_ylabel("Fuel Utilization [-]", fontsize=label_size)
    elif var_name=="T_sofc_out":
        ax1.set_ylabel("Temperature [K]", fontsize=label_size)
    elif var_name=='UA':
        ax1.set_yscale('log')
        ax1.set_ylabel(label, fontsize=label_size)
    else:
        ax1.set_ylabel(label, fontsize=label_size)

    # Horizontal line if needed
    if var_name == "T_sofc_out":
        ax1.axhline(
            y=1023,
            color='black',
            linestyle='--',
            linewidth=1.5
        )

    ax1.set_xlabel("Power fraction (-)", fontsize=label_size)

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    if var_name == "sofc_params":
        lines2, labels2 = ax2.get_legend_handles_labels()
        # ax1.legend(lines1 + lines2, labels1 + labels2,bbox_to_anchor=(0.25, 0.88),
        #     frameon=True,
        #     fontsize=legend_label_size)
    elif var_name=="T_sofc_out":
        # --- Get sorted T4 values ---
        lines1, labels1 = ax1.get_legend_handles_labels()
        T4_values = labels1#sorted(df_all["T4"].unique())

        # --- Color handles (auto-generated) ---
        color_handles = [
            mlines.Line2D([], [], color=colors[i], linewidth=3,
                          label=T4)#f"$T_4 = {T4}$K")
            for i, T4 in enumerate(T4_values)
        ]

        # --- Marker handles (only once) ---
        marker_handles = [
            mlines.Line2D([], [], color='black', marker='o', linestyle='-',
                          markersize=6, label='SOFC outlet'),
            mlines.Line2D([], [], color='black', marker='s', linestyle='--',
                          markersize=6, label='Combustor inlet')
        ]

        # --- Combine and plot legend ---
        ax1.legend(
            handles=color_handles + marker_handles,
            loc='upper left',
            bbox_to_anchor=(0.02, 0.95),  # adjust if needed
            frameon=False,
            fontsize=legend_label_size
        )

    elif var_name=="lambda_FC":
        ax1.legend(frameon=True,bbox_to_anchor=(0.7, 0.98),
                   fontsize=legend_label_size)

    else:
        ax1.legend(frameon=True,
            fontsize=legend_label_size)

    # Clean grid
    ax1.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7)

    # Ticks
    ax1.tick_params(axis='both', which='major', labelsize=11)

    # Legend (conditional placement)
    lines1, labels1 = ax1.get_legend_handles_labels()

    # if var_name == "sofc_params":
    #     lines2, labels2 = ax2.get_legend_handles_labels()
    #     ax1.legend(
    #         lines1,
    #         labels1,
    #         bbox_to_anchor=(0.25, 0.88),
    #         frameon=True,
    #         fontsize=legend_label_size
    #     )
    #
    # elif var_name == "T_sofc_out":
    #     ax1.legend(
    #         lines1,
    #         labels1,
    #         loc="upper right",
    #         bbox_to_anchor=(0.98, 0.85),
    #         frameon=True,
    #         fontsize=legend_label_size
    #     )
    #
    # else:
    #     ax1.legend(
    #         lines1,
    #         labels1,
    #         frameon=True,
    #         fontsize=legend_label_size
    #     )

    # Remove top/right spines for cleaner look
    # ax1.spines['top'].set_visible(False)
    # ax1.spines['right'].set_visible(False)

    # If twin axis exists, clean it too
    # if var_name == "sofc_params":
    #     ax2.spines['top'].set_visible(False)

    plt.tight_layout()
    figname = var_name + "_PSvar"
    fig.savefig(pathsave + figname + ".png", dpi=600, bbox_inches='tight')

def plot_func_Ncells(df_all, var_name, label):
    label_size = 18
    legend_label_size = 12
    tick_size = 15
    plt.figure(figsize=(8, 5))

    # Dark, scientific palette (Viridis subset)
    colors = ['#1b1b1b', '#00429d', '#2a9d8f', '#e9c46a', '#d62828']#plt.cm.viridis(np.linspace(0.1, 0.9, df_all["T4"].nunique()))

    for i, (N_cells, group) in enumerate(df_all.groupby("N_cells")):
        group = group.sort_values("power_fraction")

        plt.plot(
            group["power_fraction"],
            group[var_name],
            marker='o',
            linewidth=2,
            markersize=5,
            color=colors[i],
            label=f"$N_cells = {N_cells}$"
        )

    # Labels (LaTeX-style for scientific look)
    plt.xlabel("Power fraction (-)", fontsize=12)
    plt.ylabel(label, fontsize=12)

    # Clean grid
    plt.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7)

    # Ticks
    plt.tick_params(axis='both', which='major', labelsize=11)

    # Legend
    plt.legend(frameon=False, fontsize=legend_label_size)

    # Remove top/right spines for cleaner look
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    # plt.savefig("figure.png", dpi=300, bbox_inches='tight')


def plot_func_Vcellvar(df_all, var_name, label):
    pathsave="Images/"
    label_size = 18
    legend_label_size = 12
    tick_size = 15

    # Dark, scientific palette (Viridis subset)
    # colors = ["#006400","#1B3A6F",'#1b1b1b', '#00429d', '#2a9d8f', '#e9c46a', '#d62828']#plt.cm.viridis(np.linspace(0.1, 0.9, df_all["T4"].nunique()))

    colors = ["#006400",  # dark green
              "#1B3A6F",  # dark blue
              # "#8B008B",  # dark magenta
              "#8B0000"  # dark red
              ]

    fig, ax1 = plt.subplots(figsize=(8, 5))


    for i, (T4, group) in enumerate(df_all.groupby("T4")):
        if var_name=="PSFC" or var_name=="eta_thermo" or var_name=="lambda_FC":
            group[var_name] = group[var_name].round(2)
        if var_name == "sofc_params":
            # Left axis → Vcell
            ax1.plot(
                group["V_cell"],
                group["i"],
                marker='o',
                linewidth=2,
                markersize=5,
                color=colors[i],
                linestyle='-',
                label=f"$T_4 = {T4}$K"
            )
        elif var_name == "T_sofc_out":
            ax1.plot(
                group["V_cell"],
                group[var_name],
                marker='o',
                linewidth=2,
                markersize=5,
                color=colors[i],
                linestyle='-',
                label=f"$T_4 = {T4}$K"
            )
            ax1.plot(
                group["N_cells"]/1000,
                group["T_comb_in"],
                marker='s',
                linewidth=2,
                markersize=5,
                color=colors[i],
                linestyle='--',
                # label=f"$T_4 = {T4}$K"
            )

        else:
            ax1.plot(
                group["V_cell"],
                group[var_name],
                marker='o',
                linewidth=2,
                markersize=5,
                color=colors[i],
                label=f"$T_4 = {T4}$K"
            )

    if var_name=="lambda_FC":
        ax2 = ax1.twinx()

        for i, (T4, group) in enumerate(df_all.groupby("T4")):

            # Right axis → current density i
            ax2.plot(
                group["V_cell"],
                group["Uf"],
                marker='s',
                linewidth=2,
                markersize=5,
                linestyle='--',
                color=colors[i],
                # label=f"$T_4 = {T4}$K (i)"
            )

        ax1.set_ylabel("Excess Air Ratio ($\lambda$) [-]", fontsize=label_size)
        ax2.set_ylabel("Fuel Utilization [-]", fontsize=label_size)
    else:
        ax1.set_ylabel(label, fontsize=label_size)
        ax1.set_xlabel('Cell Voltage [V]', fontsize=label_size)
    ax1.legend()
    plt.tight_layout
    figname = var_name + "_Vcellvar"
    fig.savefig(pathsave + figname + ".png", dpi=600, bbox_inches='tight')



def plot_func2_Ncells(df_all, var_name, label):
    pathsave="Images/"
    label_size = 18
    legend_label_size = 12
    tick_size = 15

    # Dark, scientific palette (Viridis subset)
    colors = ["#006400","#1B3A6F",'#1b1b1b', '#00429d', '#2a9d8f', '#e9c46a', '#d62828']#plt.cm.viridis(np.linspace(0.1, 0.9, df_all["T4"].nunique()))

    fig, ax1 = plt.subplots(figsize=(8, 5))


    for i, (T4, group) in enumerate(df_all.groupby("T4")):
        group = group.sort_values("power_fraction")
        if var_name=="PSFC" or var_name=="eta_thermo" or var_name=="lambda_FC":
            group[var_name] = group[var_name].round(2)
        if var_name == "sofc_params":
            # Left axis → Vcell
            ax1.plot(
                group["N_cells"]/1000,
                group["V_cell"],
                marker='o',
                linewidth=2,
                markersize=5,
                color=colors[i],
                linestyle='-',
                label=f"$T_4 = {T4}$K"
            )
        elif var_name == "T_sofc_out":
            ax1.plot(
                group["N_cells"]/1000,
                group[var_name],
                marker='o',
                linewidth=2,
                markersize=5,
                color=colors[i],
                linestyle='-',
                label=f"$T_4 = {T4}$K"
            )
            ax1.plot(
                group["N_cells"]/1000,
                group["T_comb_in"],
                marker='s',
                linewidth=2,
                markersize=5,
                color=colors[i],
                linestyle='--',
                # label=f"$T_4 = {T4}$K"
            )

        else:
            ax1.plot(
                group["N_cells"]/1000,
                group[var_name],
                marker='o',
                linewidth=2,
                markersize=5,
                color=colors[i],
                label=f"$T_4 = {T4}$K"
            )

    # Special handling for SOFC params
    if var_name == "sofc_params":
        ax2 = ax1.twinx()

        for i, (T4, group) in enumerate(df_all.groupby("T4")):
            group = group.sort_values("power_fraction")

            # Right axis → current density i
            ax2.plot(
                group["N_cells"]/1000,
                group["i"],
                marker='s',
                linewidth=2,
                markersize=5,
                linestyle='--',
                color=colors[i],
                label=f"$T_4 = {T4}$K (i)"
            )

        ax1.set_ylabel("Cell Voltage [V]", fontsize=label_size)
        ax2.set_ylabel("Current density [A/m$^2$]", fontsize=label_size)
    elif var_name == "T_sofc_out":
        ax1.set_ylabel("Temperature [K]", fontsize=label_size)
    elif var_name=="lambda_FC":
        ax2 = ax1.twinx()

        for i, (T4, group) in enumerate(df_all.groupby("T4")):
            group = group.sort_values("power_fraction")

            # Right axis → current density i
            ax2.plot(
                group["N_cells"]/1000,
                group["Uf"],
                marker='s',
                linewidth=2,
                markersize=5,
                linestyle='--',
                color=colors[i],
                # label=f"$T_4 = {T4}$K (i)"
            )

        ax1.set_ylabel("Excess Air Ratio ($\lambda$) [-]", fontsize=label_size)
        ax2.set_ylabel("Fuel Utilization [-]", fontsize=label_size)

    else:
        ax1.set_ylabel(label, fontsize=label_size)

    # Horizontal line if needed
    if var_name == "T_sofc_out":
        ax1.axhline(
            y=1023,
            color='black',
            linestyle='--',
            linewidth=1.5
        )

    ax1.set_xlabel("N cells x 1000 [-]", fontsize=label_size)

    # Combine legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    if var_name == "sofc_params":
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2)
    else:
        ax1.legend()

    # Clean grid
    ax1.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7)

    # Ticks
    ax1.tick_params(axis='both', which='major', labelsize=11)
    if var_name=="PSFC":
        ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))
    # Legend (conditional placement)
    lines1, labels1 = ax1.get_legend_handles_labels()

    if var_name == "sofc_params":
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(
            lines1,
            labels1,
            bbox_to_anchor=(0.6, 0.88),
            frameon=True,
            fontsize=legend_label_size
        )


    elif var_name == "T_sofc_out":

        # --- Get sorted T4 values ---

        T4_values = sorted(df_all["T4"].unique())

        # --- Color handles (auto-generated) ---

        color_handles = [

            mlines.Line2D([], [], color=colors[i], linewidth=3,

                          label=f"$T_4 = {T4}$K")

            for i, T4 in enumerate(T4_values)

        ]

        # --- Marker handles (only once) ---

        marker_handles = [

            mlines.Line2D([], [], color='black', marker='o', linestyle='-',

                          markersize=6, label='SOFC outlet'),

            mlines.Line2D([], [], color='black', marker='s', linestyle='--',

                          markersize=6, label='Combustor inlet')

        ]

        # --- Combine and plot legend ---

        ax1.legend(

            handles=color_handles + marker_handles,

            loc='upper left',

            bbox_to_anchor=(0.6, 0.85),  # adjust if needed

            frameon=False,

            fontsize=legend_label_size

        )

    else:
        ax1.legend(
            lines1,
            labels1,
            frameon=True,
            fontsize=legend_label_size
        )
    ax1.tick_params(axis='both', which='major', labelsize=tick_size)
    try:
        ax2.tick_params(axis='both', which='major', labelsize=tick_size)
    except:
        pass
    plt.tight_layout
    figname = var_name + "_Ncellsvar"
    fig.savefig(pathsave + figname + ".png", dpi=600, bbox_inches='tight')

def plot_func2_PR(df_all, var_name, label):
    label_size = 18
    legend_label_size = 12
    tick_size = 15
    pathsave="Images/"
    # plt.figure(figsize=(8, 5))

    groups = list(df_all.groupby("T4"))
    n = len(groups)

    # Sample from a colormap (avoid very light colors)
    # cmap = plt.cm.inferno  # good dark-to-warm palette
    # colors = [cmap(x) for x in np.linspace(0.2, 0.8, n)]

    # Dark, scientific palette (Viridis subset)
    # colors = ['#00429d', '#2a9d8f', '#e9c46a', '#d62828']#plt.cm.viridis(np.linspace(0.1, 0.9, df_all["T4"].nunique()))'#1b1b1b',
    # colors = ["#8B008B",  # dark magenta
    #           "#006400",  # dark green
    #           "#8B0000"]  # dark red
    colors=["#006400",  # dark green
        "#1B3A6F",  # dark blue
        # "#8B008B",  # dark magenta
        "#8B0000"  # dark red
    ]

    fig, ax1 = plt.subplots(figsize=(8, 5))

    for i, (T4, group) in enumerate(df_all.groupby("T4")):
        group = group.sort_values("power_fraction")

        if var_name == "sofc_params":
            # Left axis → Vcell
            ax1.plot(
                group["PR"],
                group["V_cell"],
                marker='o',
                linewidth=2,
                markersize=5,
                color=colors[i],
                linestyle='-',
                label=f"$T_4 = {T4}$K"
            )
        elif var_name =="T_sofc_out":
            ax1.plot(
                group["PR"],
                group[var_name],
                marker='o',
                linewidth=2,
                markersize=5,
                color=colors[i],
                linestyle='-',
                label=f"$T_4 = {T4}$K"
            )
            ax1.plot(
                group["PR"],
                group["T_comb_in"],
                marker='s',
                linewidth=2,
                markersize=5,
                color=colors[i],
                linestyle='--',
                # label=f"$T_4 = {T4}$K"
            )

        else:
            ax1.plot(
                group["PR"],
                group[var_name],
                marker='o',
                linewidth=2,
                markersize=5,
                color=colors[i],
                label=f"$T_4 = {T4}$K"
            )

    # Special handling for SOFC params
    if var_name == "sofc_params":
        ax2 = ax1.twinx()

        for i, (T4, group) in enumerate(df_all.groupby("T4")):
            group = group.sort_values("power_fraction")

            # Right axis → current density i
            ax2.plot(
                group["PR"],
                group["i"],
                marker='s',
                linewidth=2,
                markersize=5,
                linestyle='--',
                color=colors[i],
                label=f"$T_4 = {T4}$K (i)"
            )

        ax1.set_ylabel("Cell Voltage [V]", fontsize=label_size)
        ax2.set_ylabel("Current density [A/m$^2$]", fontsize=label_size)
    elif var_name=="T_sofc_out":
        ax1.set_ylabel("Temperature [K]", fontsize=label_size)
    elif var_name=="lambda_FC":
        ax2 = ax1.twinx()

        for i, (T4, group) in enumerate(df_all.groupby("T4")):
            group = group.sort_values("power_fraction")

            # Right axis → current density i
            ax2.plot(
                group["PR"],
                group["Uf"],
                marker='s',
                linewidth=2,
                markersize=5,
                linestyle='--',
                color=colors[i],
                # label=f"$T_4 = {T4}$K (i)"
            )

        ax1.set_ylabel("Excess Air Ratio ($\lambda$) [-]", fontsize=label_size)
        ax2.set_ylabel("Fuel Utilization [-]", fontsize=label_size)
    else:
        ax1.set_ylabel(label, fontsize=label_size)

    # Horizontal line if needed
    if var_name == "T_sofc_out":
        ax1.axhline(
            y=1023,
            color='black',
            linestyle='--',
            linewidth=1.5
        )

    ax1.set_xlabel("OPR (-)", fontsize=label_size)

    # Combine legends
    # lines1, labels1 = ax1.get_legend_handles_labels()
    # if var_name == "sofc_params":
    #     lines2, labels2 = ax2.get_legend_handles_labels()
    #     ax1.legend(lines1 + lines2, labels1 + labels2)
    # else:
    #     ax1.legend()

    # Clean grid
    ax1.grid(True, which='major', linestyle='--', linewidth=0.6, alpha=0.7)

    # Ticks
    ax1.tick_params(axis='both', which='major', labelsize=11)

    # Legend (conditional placement)
    lines1, labels1 = ax1.get_legend_handles_labels()

    if var_name == "sofc_params":
        lines2, labels2 = ax2.get_legend_handles_labels()
        # ax1.legend(
        #     lines1 ,
        #     labels1,
        #     bbox_to_anchor=(0.25, 0.88),
        #     frameon=True,
        #     fontsize=legend_label_size
        # )
    elif var_name=="T_sofc_out":
        # --- Get sorted T4 values ---
        T4_values = sorted(df_all["T4"].unique())

        # --- Color handles (auto-generated) ---
        color_handles = [
            mlines.Line2D([], [], color=colors[i], linewidth=3,
                          label=f"$T_4 = {T4}$K")
            for i, T4 in enumerate(T4_values)
        ]

        # --- Marker handles (only once) ---
        marker_handles = [
            mlines.Line2D([], [], color='black', marker='o', linestyle='-',
                          markersize=6, label='SOFC outlet'),
            mlines.Line2D([], [], color='black', marker='s', linestyle='--',
                          markersize=6, label='Combustor inlet')
        ]

        # --- Combine and plot legend ---
        ax1.legend(
            handles=color_handles + marker_handles,
            loc='upper left',
            bbox_to_anchor=(0.02, 0.70),  # adjust if needed
            frameon=False,
            fontsize=legend_label_size
        )


    # elif var_name == "T_sofc_out":
    #     ax1.legend(
    #         lines1,
    #         labels1,
    #         loc="upper right",
    #         bbox_to_anchor=(0.98, 0.85),
    #         frameon=True,
    #         fontsize=legend_label_size
    #     )

    else:
        ax1.legend(
            lines1,
            labels1,
            frameon=True,
            fontsize=legend_label_size
        )

    # Remove top/right spines for cleaner look
    # ax1.spines['top'].set_visible(False)
    # ax1.spines['right'].set_visible(False)

    # If twin axis exists, clean it too
    # if var_name == "sofc_params":
    #     ax2.spines['top'].set_visible(False)

    plt.tight_layout()
    figname=var_name+"_OPRvar"
    fig.savefig(pathsave+figname+".png", dpi=600, bbox_inches='tight')

def line_plots():
    data = []
    N_cells_list = [120000]
    power_fraction_list=[0.25,0.45,0.65,0.85]
    T4_list=[1200,1400,1600]
    PR=20
    for T4 in T4_list:
        for N_cells in N_cells_list:
            for pf in power_fraction_list:
                for T_H2 in [873]:
                    if T_H2 == 873:
                        filename = f"{condition}DES_pt_{Des_pt}_PFrac_{pf}_T4_{T4}_Ncells_{N_cells}_PR_{PR}"
                    else:
                        filename = f"{condition}DES_pt_{Des_pt}_PFrac_{pf}_T4_{T4}_Ncells_{N_cells}_PR_{PR}"+ '_T_H2_300K'
                    full_path = path_save + filename + ".csv"

                    if not os.path.exists(full_path):
                        continue

                    df = pd.read_csv(full_path)
                    row = df.iloc[0]
                    W_fuel = row['W_fuel_in']  # g/s
                    W_fuel_excess = row['W_fuel_excess_in_anode']
                    Power_lpshaft = row['LP_shaft.pwr_in']  # W
                    PSFC = (W_fuel * 3600) / (Power_lpshaft * 1e-3)  # g/kWh
                    T_sofc_out = (row['sofc.Fl_Oc:tot:T'] + row['sofc.Fl_Oa:tot:T']) / 2
                    # checks
                    V_cell = row['V_cell']
                    E_Nernst = row['E_N']
                    curr_density = row['i']
                    UA = row['Hex_UA']
                    Hex_E = row['Hex_E']
                    T_hex_hot_out = row['Hex.Fl_O_hot:tot:T']
                    T_comp_out = row['comp.Fl_O:tot:T']
                    pf_real = row['P_stack']*0.95/Power_lpshaft
                    W_air = row['comp.Fl_O:stat:W'] #kg/s
                    Uf = (W_fuel-W_fuel_excess)/W_fuel
                    lambda_FC = (W_air*1000/W_fuel)/(0.5*4.76*28.8/2)
                    eta_thermo = 100*(Power_lpshaft)/(W_fuel*120*1000)
                    T_comb_in = row['Hex.Fl_O_hot:tot:T']
                    # T_anode_out = row['sofc.Fl_Oa:tot:T']

                    if V_cell > 0 and V_cell < 2 and T_hex_hot_out>=T_comp_out and T_sofc_out<1500:
                        print(pf_real)
                        data.append({
                            "T4": T4,
                            "N_cells": N_cells,
                            "power_fraction": pf_real,
                            "T_sofc_out": T_sofc_out,
                            "PSFC":PSFC,
                            "V_cell":V_cell,
                            "E_N":E_Nernst,
                            "i":curr_density,
                            "W_air":W_air,
                            "UA":UA,
                            "Hex_E":Hex_E,
                            "Uf":Uf,
                            "lambda_FC":lambda_FC,
                            "eta_thermo":eta_thermo,
                            "T_H2":T_H2,
                            "T_comb_in":T_comb_in
                        })

    df_all = pd.DataFrame(data)
    # plot_func(df_all, "T_sofc_out", "Temperature SOFC outlet [K]")
    plot_func(df_all, "PSFC", "PSFC [g/kwh]")
    plot_func(df_all, "V_cell", "Cell Voltage [V]")
    plot_func(df_all, "E_N", "Nernst Voltage [V]")
    plot_func(df_all, "i", "Current density [A/m$^2$]")
    plot_func(df_all, "W_air", "Air mass flow [kg/s]")
    plot_func(df_all, "UA", " UA [W/K]")
    plot_func(df_all, "Hex_E", "Heat Exchanger Effectiveness [-]")
    plot_func(df_all, "Uf", "Fuel Utilization [-]")
    plot_func(df_all, "lambda_FC", "Excess Air ratio ($\lambda$) [-]")
    plot_func(df_all, "eta_thermo", "Thermodynamic Efficiency [%]")
    plot_func(df_all, "sofc_params", "")

    # plt.show()

def line_plots_vcellvar():
    data = []
    T4_list = [900, 1200, 1400]#,1400,1600]#,1400,1600, 1800]
    V_cell_list=[0.7,0.75,0.8,0.85,0.9]#,0.95,1.0]
    PR = 20
    des_pt = "TOC"
    path_save = "Results_H2_300K/"#
    for T4 in T4_list:
        for Vcell in V_cell_list:

            filename = condition+'DES_pt_' + des_pt + '_T4_' + str(T4) + '_Vcell_' + str(Vcell) + '_PR_' + str(PR)
            full_path = path_save + filename + ".csv"

            if not os.path.exists(full_path):
                continue

            df = pd.read_csv(full_path)
            row = df.iloc[0]
            num_engines = 2
            W_fuel = row['W_fuel_in']  # g/s
            W_fuel_excess = row['W_fuel_excess_in_anode']
            Power_lpshaft = row['LP_shaft.pwr_in']  # W
            PSFC = (W_fuel * 3600) / (Power_lpshaft * 1e-3)  # g/kWh
            T_sofc_out = (row['sofc.Fl_Oc:tot:T'] + row['sofc.Fl_Oa:tot:T']) / 2
            # checks
            V_cell = row['V_cell']
            A_cell = row['A_cell'] # m**2
            N_cells = row['N_cells']

            E_Nernst = row['E_N']
            curr_density = row['i']
            wt_cell=3.293/1000#kg
            A_lepmi_cell=9.079*1e-4#m**2
            wt_single_cell=A_cell*wt_cell/A_lepmi_cell
            Wt_sofc = num_engines*N_cells*wt_single_cell#V_cell*curr_density*A_cell*N_cells/(2*1000) #wt in kg ; Assuming stack powerdensity of 2kW/kg
            UA = row['Hex_UA']
            Hex_E = row['Hex_E']
            # hex wt
            U_assume = 100 # W/K
            A_by_V = 700 # m2/m3
            Vol_hex = (UA/U_assume)/A_by_V #m3
            rho_inconel = 8140 # kg/m3
            eta_packing=0.25
            Wt_hex = num_engines*Vol_hex*eta_packing*rho_inconel # kg

            T_hex_hot_out = row['Hex.Fl_O_hot:tot:T']
            T_comp_out = row['comp.Fl_O:tot:T']
            pf_real = row['P_stack'] * 0.95 / Power_lpshaft
            W_air = row['comp.Fl_O:stat:W']  # kg/s
            Uf = (W_fuel - W_fuel_excess) / W_fuel
            lambda_FC = (W_air * 1000 / W_fuel) / (0.5 * 4.76 * 28.8 / 2)
            eta_thermo = 100 * (Power_lpshaft) / (W_fuel * 120 * 1000)
            T_comb_in = row['Hex.Fl_O_hot:tot:T']
            Wt_fuel_total = 1.5*num_engines*W_fuel*3600*3.7685/1000 # kg 3.7685 hrs avg flight time and 2 engines, reverse calculated from Ardya's Excel sheet
            Wt_fuel_plus_tank  = Wt_fuel_total/0.2
            #GT weight
            wt_pw127 = 480 # kg
            W_air_pw127= 6.447 # kg/s
            Wt_gt = num_engines*(wt_pw127/(W_air_pw127**1.45))*(W_air**1.45)

            if V_cell > 0 and V_cell < 2 and T_hex_hot_out>=T_comp_out and T_sofc_out<1500:
                print(pf_real)
                data.append({
                    "T4": T4,
                    "N_cells": N_cells,
                    "power_fraction": pf_real,
                    "T_sofc_out": T_sofc_out,
                    "PSFC": PSFC,
                    "V_cell": V_cell,
                    "E_N": E_Nernst,
                    "i": curr_density,
                    "W_air": W_air,
                    "UA": UA,
                    "Hex_E": Hex_E,
                    "Uf": Uf,
                    "lambda_FC": lambda_FC,
                    "eta_thermo": eta_thermo,
                    "PR":PR,
                    "T_comb_in": T_comb_in,
                    "Wt_sofc":Wt_sofc,
                    "Wt_hex":Wt_hex,
                    "Wt_fuel_plus_tank":Wt_fuel_plus_tank,
                    "Wt_GT": Wt_gt,
                    "Wt_fuel_tank_sofc_hex":Wt_sofc+Wt_hex+Wt_fuel_plus_tank+Wt_gt

                })

    df_all = pd.DataFrame(data)
    plot_func_Vcellvar(df_all, "N_cells", "Number of Cells [-]")
    plot_func_Vcellvar(df_all, "eta_thermo", "Electrothermal efficiency [%]")
    plot_func_Vcellvar(df_all, "UA", "Heat Exchanger Size")
    plot_func_Vcellvar(df_all, "PSFC", "PSFC [g/kwh]")
    plot_func_Vcellvar(df_all, "i", "Current Density [A/m$^2$]")
    plot_func_Vcellvar(df_all, "power_fraction", "Power Split [-]")
    plot_func_Vcellvar(df_all, "Wt_sofc", "Weight SOFC (x2) [kg]")
    plot_func_Vcellvar(df_all, "Wt_hex", "Weight HEX (x2) [kg]")
    plot_func_Vcellvar(df_all, "Wt_fuel_plus_tank", "Weight Fuel+Tank [kg]")
    plot_func_Vcellvar(df_all, "Wt_GT", "Wt Gas Turbine (x2) [kg]")
    plot_func_Vcellvar(df_all, "Wt_fuel_tank_sofc_hex", "System Weight [kg]")
    plot_func_Vcellvar(df_all, "W_air", "Air mass flow [kg/s]")
    plot_func_Vcellvar(df_all, "lambda_FC", "Excess Air ratio ($\lambda$) [-]")


def line_plots_ncellsvar():
    data = []
    T4_list = [1200]#,1400,1600]#,1400,1600, 1800]
    power_fraction_list = [0.65]
    # pf = 0.65
    N_cells_list = [80000, 100000, 120000, 160000]
    PR = 10
    for T4 in T4_list:
        for N_cells in N_cells_list:
            for pf in power_fraction_list:
            # for PR in PR_list:

                filename = f"{condition}DES_pt_{Des_pt}_PFrac_{pf}_T4_{T4}_Ncells_{N_cells}_PR_{PR}"
                full_path = path_save + filename + ".csv"

                if not os.path.exists(full_path):
                    continue

                df = pd.read_csv(full_path)
                row = df.iloc[0]
                W_fuel = row['W_fuel_in']  # g/s
                W_fuel_excess = row['W_fuel_excess_in_anode']
                Power_lpshaft = row['LP_shaft.pwr_in']  # W
                PSFC = (W_fuel * 3600) / (Power_lpshaft * 1e-3)  # g/kWh
                T_sofc_out = (row['sofc.Fl_Oc:tot:T'] + row['sofc.Fl_Oa:tot:T']) / 2
                # checks
                V_cell = row['V_cell']
                E_Nernst = row['E_N']
                curr_density = row['i']
                UA = row['Hex_UA']
                Hex_E = row['Hex_E']
                T_hex_hot_out = row['Hex.Fl_O_hot:tot:T']
                T_comp_out = row['comp.Fl_O:tot:T']
                pf_real = row['P_stack'] * 0.95 / Power_lpshaft
                W_air = row['comp.Fl_O:stat:W']  # kg/s
                Uf = (W_fuel - W_fuel_excess) / W_fuel
                lambda_FC = (W_air * 1000 / W_fuel) / (0.5 * 4.76 * 28.8 / 2)
                eta_thermo = 100 * (Power_lpshaft) / (W_fuel * 120 * 1000)
                T_comb_in = row['Hex.Fl_O_hot:tot:T']

                if V_cell > 0 and V_cell < 2 and T_hex_hot_out>=T_comp_out and T_sofc_out<1500:
                    print(pf_real)
                    data.append({
                        "T4": T4,
                        "N_cells": N_cells,
                        "power_fraction": pf_real,
                        "T_sofc_out": T_sofc_out,
                        "PSFC": PSFC,
                        "V_cell": V_cell,
                        "E_N": E_Nernst,
                        "i": curr_density,
                        "W_air": W_air,
                        "UA": UA,
                        "Hex_E": Hex_E,
                        "Uf": Uf,
                        "lambda_FC": lambda_FC,
                        "eta_thermo": eta_thermo,
                        "PR":PR,
                        "T_comb_in": T_comb_in
                    })

    df_all = pd.DataFrame(data)
    # plot_func_Ncells(df_all, "T_sofc_out", "Temperature SOFC outlet [K]")
    # plot_func_Ncells(df_all, "PSFC", "PSFC [g/kwh]")
    # plot_func_Ncells(df_all, "V_cell", "Cell Voltage [V]")
    # plot_func_Ncells(df_all, "E_N", "Nernst Voltage [V]")
    # plot_func_Ncells(df_all, "i", "Current density [A/m$^2$]")
    # plot_func_Ncells(df_all, "W_air", "Air mass flow [kg/s]")
    # plot_func_Ncells(df_all, "UA", " UA [W/K]")
    # plot_func_Ncells(df_all, "Hex_E", "Heat Exchanger Effectiveness [-]")
    # plot_func_Ncells(df_all, "Uf", "Fuel Utilization [-]")
    # plot_func_Ncells(df_all, "lambda_FC", "Excess Air ratio ($\lambda$) [-]")
    # plot_func_Ncells(df_all, "eta_thermo", "Thermodynamic Efficiency [%]")

    plot_func2_Ncells(df_all, "T_sofc_out", "Temperature [K]")
    # plot_func2_Ncells(df_all, "PSFC", "PSFC [g/kwh]")
    # plot_func2_Ncells(df_all, "V_cell", "Cell Voltage [V]")
    # plot_func2_Ncells(df_all, "E_N", "Nernst Voltage [V]")
    # plot_func2_Ncells(df_all, "i", "Current density [A/m$^2$]")
    # plot_func2_Ncells(df_all, "W_air", "Air mass flow [kg/s]")
    # plot_func2_Ncells(df_all, "UA", " UA [W/K]")
    # plot_func2_Ncells(df_all, "Hex_E", "Heat Exchanger Effectiveness [-]")
    # plot_func2_Ncells(df_all, "Uf", "Fuel Utilization [-]")
    # plot_func2_Ncells(df_all, "lambda_FC", "Excess Air ratio ($\lambda$) [-]")
    # plot_func2_Ncells(df_all, "eta_thermo", "Thermodynamic Efficiency [%]")
    # plot_func2_Ncells(df_all, "sofc_params", "")

    # plot_func2_PR(df_all, "T_sofc_out", "Temperature SOFC outlet [K]")
    # plot_func2_PR(df_all, "PSFC", "PSFC [g/kwh]")
    # plot_func2_PR(df_all, "V_cell", "Cell Voltage [V]")
    # plot_func2_PR(df_all, "E_N", "Nernst Voltage [V]")
    # plot_func2_PR(df_all, "i", "Current density [A/m$^2$]")
    # plot_func2_PR(df_all, "W_air", "Air mass flow [kg/s]")
    # plot_func2_PR(df_all, "UA", " UA [W/K]")
    # plot_func2_PR(df_all, "Hex_E", "Heat Exchanger Effectiveness [-]")
    # plot_func2_PR(df_all, "Uf", "Fuel Utilization [-]")
    # plot_func2_PR(df_all, "lambda_FC", "Excess Air ratio ($\lambda$) [-]")
    # plot_func2_PR(df_all, "eta_thermo", "Thermodynamic Efficiency [%]")
    # plot_func2_PR(df_all, "sofc_params", "")

    plt.show()

if __name__=="__main__":
    # line_plots()
    # line_plots_ncellsvar()
    line_plots_vcellvar()