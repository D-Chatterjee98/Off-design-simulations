import os
import openmdao.api as om


om.Problem._mpi_proc_allocator = False
from EngineBuild_i_target import MPSingleSpool
from EngineSettings import EngineSettings
import csv

from pycycle.viewers import plot_compressor_maps
import matplotlib.pyplot as plt
import numpy as np

# Flow Station Names
FS_NAMES = ['fc.Fl_O', 'inlet.Fl_O', 'comp.Fl_O','Hex_cold.Fl_O','Hex.Fl_O_hot',
            'sofc.Fl_Oc', 'sofc.Fl_Oa', 'sofc_mixer.Fl_O', 'burner.Fl_O', 'turb.Fl_O', 'pt.Fl_O', 'nozz.Fl_O']


def mpi_connect(params):
    T4, N_cells, power_fraction, PR = params
    prob = problem_setup_mpi(T4, N_cells, power_fraction, PR)
    try:
        prob.run_model()
    except Exception as e:
        print("Simulation crashed:", e)

    pts = ['DESIGN'] + prob.model.od_pts
    path_save = "Results/"
    for pt in pts:
        filename = path_save + 'T4_'+str(T4)+'_Ncells_'+str(N_cells)+'_PF_'+str(power_fraction)+'_PR_'+str(PR)+'_'+ pt+ '.csv'
        save_data(prob, pt, filename)

def problem_setup_mpi(T4, N_cells, power_fraction ,PR):
    prob = om.Problem()

    settings = EngineSettings(
        Power_target=power_fraction,
    )
    prob.model = mp_single_spool = MPSingleSpool(settings)
    prob.setup()

    # Define the design point
    settings.SOFC_N_cells = N_cells  # Todo: working case =20000
    prob.set_val('DESIGN.sofc.N_cells', settings.SOFC_N_cells)
    prob.model.add_constraint('sofc.T_cell', lower=600, upper=750, units='degC')
    prob.set_val('DESIGN.fc.alt', settings.des_alt, units='ft')
    prob.set_val('DESIGN.fc.MN', settings.des_mach_no)

    pwr_shaft = settings.des_pwr_shaft
    prob.set_val('DESIGN.balance.pwr_target', pwr_shaft * (1), units='hp')
    prob.set_val('DESIGN.balance.pwr_sofc_target', pwr_shaft * (settings.Power_target), units='hp')
    prob.set_val('DESIGN.balance.T4_target', T4, units='K')  # Todo: working case = 1600
    prob.set_val('DESIGN.balance.T_inlet_target', 873, units='K')
    prob.set_val('DESIGN.balance.nozz_PR_target', 1.1)
    prob.set_val('DESIGN.comp.PR', PR)
    prob.set_val('DESIGN.comp.eff', 0.83)
    prob.set_val('DESIGN.turb.eff', 0.86)
    prob.set_val('DESIGN.pt.eff', 0.9)
    prob.set_val('DESIGN.burner.Fl_I:FAR', 1e-10)

    # Set initial guesses for balances
    prob['DESIGN.balance.W'] = power_fraction*(25000.0/0.35)  # g/s Todo: working case =1000 g/s, 2500
    prob['DESIGN.balance.turb_PR'] = 2  # 3.8768
    prob['DESIGN.balance.pt_PR'] = 4  # 3.8768
    prob['DESIGN.balance.mdot_anode_in_excess'] = 10.0  # g/s  Todo: working case =30 g/s
    prob['DESIGN.balance.V_sofc'] = 0.8
    prob['DESIGN.fc.balance.Pt'] = 5.66  # 14.69551131598148
    prob['DESIGN.fc.balance.Tt'] = 518.665288153
    prob['DESIGN.balance.hex_effectiveness'] = 0.8
    #
    for i, pt in enumerate(mp_single_spool.od_pts):
        # hardcoded values
        prob.set_val(pt + '.sofc.N_cells', settings.SOFC_N_cells)
        prob[pt + '.burner.Fl_I:FAR'] = 1e-10
        # initial guesses
        prob[pt + '.balance.W'] = mp_single_spool.od_pwrs_kw[i]*(prob['DESIGN.balance.W']/pwr_shaft)
        # prob[pt + '.balance.FAR'] = 0.0175506829934
        prob[pt + '.balance.mdot_anode_in_excess'] = 40.0  # g/s  Todo: working case =30 g/s
        prob[pt + '.balance.V_sofc'] = 0.5
        prob[pt + '.balance.HP_Nmech'] = 15000.0
        prob[pt + '.fc.balance.Pt'] = 15.703
        prob[pt + '.fc.balance.Tt'] = 558.31
        prob[pt + '.turb.PR'] = 2
        prob[pt + '.pt.PR'] = 4

    return prob

def problem_setup(T4, N_cells, power_fraction ,PR, Des_pt):
    prob = om.Problem()
    # power_fraction = 0.75
    settings = EngineSettings()
    # Define the design point
    settings.SOFC_N_cells = N_cells  # Todo: working case =20000
    design_pt = Des_pt #'Cruise'
    settings.Power_target : float =power_fraction
    settings.des_alt : float= settings.alt_ft_dict[design_pt]
    settings.des_mach_no : float= settings.mach_no_dict[design_pt]
    settings.des_pwr_shaft : float = settings.pwr_shaft_kW[design_pt]*1.341 # kw to hp
    settings.des_ISA_dT: float = settings.ISA_dict[design_pt]
    # Power split adjustment for flight phase
    # settings.pwr_frac_dict['TOC'] = power_fraction
    # settings.pwr_frac_dict['Cruise'] = power_fraction
    # settings.pwr_frac_dict['MTO'] = power_fraction
    settings.od_pts = ['TOC']
    settings.__post_init__()



    prob.model = mp_single_spool = MPSingleSpool(settings)
    prob.setup()

    # prob.set_val('DESIGN.sofc.N_cells', settings.SOFC_N_cells)
    prob.set_val('DESIGN.fc.alt', settings.des_alt, units='ft')
    prob.set_val('DESIGN.fc.MN', settings.des_mach_no)
    prob.set_val('DESIGN.fc.dTs', settings.des_ISA_dT, units='K')
    prob.model.add_constraint('sofc.T_cell', lower=600, upper=750, units='degC')
    # Balance targets
    prob.set_val('DESIGN.balance.V_target', 0.7, units='V')
    prob.set_val('DESIGN.balance.pwr_target', settings.des_pwr_shaft, units='hp')
    # prob.set_val('DESIGN.balance.pwr_sofc_target', settings.des_pwr_shaft * (settings.pwr_frac_dict[design_pt]), units='hp')
    prob.set_val('DESIGN.balance.T_sofc_target', 1023,
                 units='K')
    prob.set_val('DESIGN.balance.T4_target', T4, units='K')  # Todo: working case = 1600
    prob.set_val('DESIGN.balance.T_inlet_target', 873, units='K')
    prob.set_val('DESIGN.balance.nozz_PR_target', 1.1)
    # Remaining GT components specs
    prob.set_val('DESIGN.comp.PR', PR)
    prob.set_val('DESIGN.comp.eff', 0.83)
    prob.set_val('DESIGN.turb.eff', 0.86)
    prob.set_val('DESIGN.pt.eff', 0.9)
    prob.set_val('DESIGN.burner.Fl_I:FAR', 1e-10)

    # Set initial guesses for balances
    prob['DESIGN.balance.W'] =2000  # g/s Todo: working case =1000 g/s, 2500
    prob['DESIGN.balance.turb_PR'] = 2  # 3.8768
    prob['DESIGN.balance.pt_PR'] = 4  # 3.8768
    prob['DESIGN.balance.mdot_anode_in_excess'] = 20  # g/s  Todo: working case =30 g/s
    prob['DESIGN.balance.i_sofc'] = 5000
    prob['DESIGN.fc.balance.Pt'] = 5.66  # 14.69551131598148
    prob['DESIGN.fc.balance.Tt'] = 518.665288153
    prob['DESIGN.balance.hex_effectiveness']=0.8

    # Defining off-design pts
    # Defining off-design pts
    w_air_guess = {'Cruise': 2200, 'MTO': 8000, 'TOC': 2200}
    mdot_anode_excess_guess = {'Cruise': 20, 'MTO': 40, 'TOC': 20}
    i_sofc_guess = {'Cruise': 8000, 'MTO': 5000, 'TOC': 8000}
    HP_Nmech_guess = {'Cruise': 10000, 'MTO': 13689, 'TOC': 14000}
    Pt_fc_gues= {'Cruise': 4.64, 'MTO': 14.64, 'TOC': 4.64} #psi
    Tt_fc_guess = {'Cruise': 450, 'MTO': 527, 'TOC': 450}

    # off design initial guesses
    for i, pt in enumerate(mp_single_spool.od_pts):
        # hardcoded values
        # prob.set_val(pt + '.sofc.N_cells', settings.SOFC_N_cells)
        # prob.set_val(pt + '.sofc.N_cells', prob['DESIGN.sofc.N_cells'])
        # prob.set_val(pt + '.balance.pwr_sofc_target', settings.pwr_shaft_kW[pt]*1.341*settings.pwr_frac_dict[pt], units='hp')
        prob.set_val(pt + '.balance.T_sofc_target',1023, units='K')
        # prob.set_val(pt + '.balance.T_inlet_target',873, units='K')
        # prob.set_val(pt + '.balance.V_target', 0.7, units='V')
        prob[pt + '.burner.Fl_I:FAR'] = 1e-10
        # initial guesses
        # prob[pt + '.balance.W'] = w_air_guess[pt]
        prob.set_val(pt + '.balance.W',w_air_guess[pt],units='g/s')
        prob.set_val(pt + '.balance.mdot_anode_in_excess',mdot_anode_excess_guess[pt], units='g/s')  # 40.0  # g/s  Todo: working case =30 g/s
        prob.set_val(pt + '.balance.i_sofc',i_sofc_guess[pt], units='A/m**2')  # prob['DESIGN.balance.i_sofc'] * (settings.pwr_shaft_kW[pt] / settings.pwr_shaft_kW[design_pt])
        prob.set_val(pt + '.balance.HP_Nmech', HP_Nmech_guess[pt], units='rpm')
        # prob[pt + '.balance.W'] = prob.get_val('DESIGN.comp.Fl_O:stat:W', units='g/s')[0]*(settings.pwr_shaft_kW[pt]/settings.pwr_shaft_kW[design_pt])
        # prob[pt + '.balance.mdot_anode_in_excess'] = prob.get_val('DESIGN.sofc.mdot_anode_in_excess', units='g/s')[0] * (settings.pwr_shaft_kW[pt]/settings.pwr_shaft_kW[design_pt])#40.0  # g/s  Todo: working case =30 g/s
        # prob[pt + '.balance.i_sofc'] = 6000*(settings.pwr_shaft_kW[pt]/settings.pwr_shaft_kW[design_pt])
        # prob[pt + '.balance.HP_Nmech'] = prob.get_val('DESIGN.HP_shaft.Nmech', units='rpm')[0]*(settings.pwr_shaft_kW[pt]/settings.pwr_shaft_kW[design_pt])
        prob.set_val(pt + '.fc.balance.Pt',Pt_fc_gues[pt], units='psi') # ambient pressure guess in psi
        prob.set_val(pt + '.fc.balance.Tt',Tt_fc_guess[pt], units='degR') # ambient temperature guess in R
        prob[pt + '.turb.PR'] = 3.0
        prob[pt + '.comp.PR'] = PR
        # prob[pt + '.comp.map.RlineMap'] = 2.0
        # prob[pt + '.sofc.SOFC_0D.n_H2_in'] = 20  # 'n_H2O_out'
        # prob[pt + '.sofc.SOFC_0D.n_H2O_in'] = 1e-3
        # prob[pt + '.sofc.SOFC_0D.n_H2_out'] = 8  # 'n_H2O_out'
        # prob[pt + '.sofc.SOFC_0D.n_H2O_out'] = 12
    #
    # st = time.time()

    prob.set_solver_print(level=-1)
    #prob.set_solver_print(level=1, depth=1)  # (level=2, depth=1)
    # prob.check_config()

    # # Recording
    # rec = om.SqliteRecorder("debug.sql")
    # # solver = prob.model.nonlinear_solver
    # # solver = prob.model.nonlinear_solver = om.DirectSolver()
    #
    # prob.model.nonlinear_solver.add_recorder(rec)
    #
    # prob.model.nonlinear_solver.recording_options['record_outputs'] = True
    # prob.model.nonlinear_solver.recording_options['record_solver_residuals'] = True
    # prob.model.nonlinear_solver.recording_options['includes'] = ["sofc.i", "sofc.V_target", "sofc.mdot_anode_in_excess"]

    prob.model._check_required_connections()

    return prob

def design_problem_setup_Vcell(T4, PR, Des_pt,V_cell):
    prob = om.Problem()
    # power_fraction = 0.75
    settings = EngineSettings()
    # Define the design point
    # settings.SOFC_N_cells = N_cells  # Todo: working case =20000
    design_pt = Des_pt #'Cruise'
    # settings.Power_target : float =power_fraction
    settings.des_alt : float= settings.alt_ft_dict[design_pt]
    settings.des_mach_no : float= settings.mach_no_dict[design_pt]
    settings.des_pwr_shaft : float = settings.pwr_shaft_kW[design_pt]*1.341 # kw to hp
    settings.des_ISA_dT: float = settings.ISA_dict[design_pt]
    settings.od_pts = []
    # Power split adjustment for flight phase
    # settings.pwr_frac_dict['TOC'] = power_fraction
    # settings.pwr_frac_dict['Cruise'] = power_fraction
    # settings.pwr_frac_dict['MTO'] = power_fraction



    prob.model = mp_single_spool = MPSingleSpool(settings)
    prob.setup()

    # prob.set_val('DESIGN.sofc.N_cells', settings.SOFC_N_cells)
    prob.set_val('DESIGN.fc.alt', settings.des_alt, units='ft')
    prob.set_val('DESIGN.fc.MN', settings.des_mach_no)
    prob.set_val('DESIGN.fc.dTs', settings.des_ISA_dT, units='K')
    prob.model.add_constraint('sofc.T_cell', lower=600, upper=750, units='degC')
    # Balance targets
    prob.set_val('DESIGN.balance.V_target', V_cell, units='V')
    prob.set_val('DESIGN.balance.pwr_target', settings.des_pwr_shaft, units='hp')
    # prob.set_val('DESIGN.balance.pwr_sofc_target', settings.des_pwr_shaft * (settings.pwr_frac_dict[design_pt]), units='hp')
    prob.set_val('DESIGN.balance.T_sofc_target', 1023,
                 units='K')
    prob.set_val('DESIGN.balance.T4_target', T4, units='K')  # Todo: working case = 1600
    prob.set_val('DESIGN.balance.T_inlet_target', 873, units='K')
    prob.set_val('DESIGN.balance.nozz_PR_target', 1.1)
    # Remaining GT components specs
    prob.set_val('DESIGN.comp.PR', PR)
    prob.set_val('DESIGN.comp.eff', 0.83)
    prob.set_val('DESIGN.turb.eff', 0.86)
    prob.set_val('DESIGN.pt.eff', 0.9)
    prob.set_val('DESIGN.burner.Fl_I:FAR', 1e-10)

    # Set initial guesses for balances
    prob['DESIGN.balance.W'] =2000  # g/s Todo: working case =1000 g/s, 2500
    prob['DESIGN.balance.turb_PR'] = 2  # 3.8768
    prob['DESIGN.balance.pt_PR'] = 4  # 3.8768
    prob['DESIGN.balance.mdot_anode_in_excess'] = 20  # g/s  Todo: working case =30 g/s
    prob['DESIGN.balance.i_sofc'] = 5000
    prob['DESIGN.fc.balance.Pt'] = 5.66  # 14.69551131598148
    prob['DESIGN.fc.balance.Tt'] = 518.665288153
    prob['DESIGN.balance.hex_effectiveness']=0.8


    prob.set_solver_print(level=-1)
    prob.set_solver_print(level=1, depth=1)  # (level=2, depth=1)
    # prob.check_config()

    # # Recording
    # rec = om.SqliteRecorder("debug.sql")
    # # solver = prob.model.nonlinear_solver
    # # solver = prob.model.nonlinear_solver = om.DirectSolver()
    #
    # prob.model.nonlinear_solver.add_recorder(rec)
    #
    # prob.model.nonlinear_solver.recording_options['record_outputs'] = True
    # prob.model.nonlinear_solver.recording_options['record_solver_residuals'] = True
    # prob.model.nonlinear_solver.recording_options['includes'] = ["sofc.i", "sofc.V_target", "sofc.mdot_anode_in_excess"]

    prob.model._check_required_connections()

    return prob


def design_problem_setup(T4, N_cells, power_fraction, PR, Des_pt):
    prob = om.Problem()
    # power_fraction = 0.75
    settings = EngineSettings()
    # Define the design point
    settings.SOFC_N_cells = N_cells  # Todo: working case =20000
    design_pt = Des_pt  # 'Cruise'
    settings.Power_target: float = power_fraction
    settings.des_alt: float = settings.alt_ft_dict[design_pt]
    settings.des_mach_no: float = settings.mach_no_dict[design_pt]
    settings.des_pwr_shaft: float = settings.pwr_shaft_kW[design_pt] * 1.341  # kw to hp
    settings.des_ISA_dT: float = settings.ISA_dict[design_pt]
    # Power split adjustment for flight phase
    settings.pwr_frac_dict['TOC'] = power_fraction
    settings.pwr_frac_dict['Cruise'] = power_fraction
    settings.pwr_frac_dict['Cruise'] = power_fraction
    settings.od_pts=[]

    prob.model = mp_single_spool = MPSingleSpool(settings)
    prob.setup()

    prob.set_val('DESIGN.sofc.N_cells', settings.SOFC_N_cells)
    prob.set_val('DESIGN.fc.alt', settings.des_alt, units='ft')
    prob.set_val('DESIGN.fc.MN', settings.des_mach_no)
    prob.set_val('DESIGN.fc.dTs', settings.des_ISA_dT, units='K')
    prob.model.add_constraint('sofc.T_cell', lower=600, upper=750, units='degC')
    # Balance targets
    # prob.set_val('DESIGN.balance.V_target', 0.7, units='V')
    prob.set_val('DESIGN.balance.pwr_target', settings.des_pwr_shaft, units='hp')
    prob.set_val('DESIGN.balance.pwr_sofc_target', settings.des_pwr_shaft * (settings.pwr_frac_dict[design_pt]),
                 units='hp')
    prob.set_val('DESIGN.balance.T4_target', T4, units='K')  # Todo: working case = 1600
    prob.set_val('DESIGN.balance.T_inlet_target', 873, units='K')
    prob.set_val('DESIGN.balance.nozz_PR_target', 1.1)
    # Remaining GT components specs
    prob.set_val('DESIGN.comp.PR', PR)
    prob.set_val('DESIGN.comp.eff', 0.83)
    prob.set_val('DESIGN.turb.eff', 0.86)
    prob.set_val('DESIGN.pt.eff', 0.9)
    prob.set_val('DESIGN.burner.Fl_I:FAR', 1e-10)

    # Set initial guesses for balances
    prob['DESIGN.balance.W'] = 7000  # g/s Todo: working case =1000 g/s, 2500
    prob['DESIGN.balance.turb_PR'] = 2  # 3.8768
    prob['DESIGN.balance.pt_PR'] = 4  # 3.8768
    prob['DESIGN.balance.mdot_anode_in_excess'] = 20  # g/s  Todo: working case =30 g/s
    prob['DESIGN.balance.i_sofc'] = 4000
    prob['DESIGN.fc.balance.Pt'] = 5.66  # 14.69551131598148
    prob['DESIGN.fc.balance.Tt'] = 518.665288153
    prob['DESIGN.balance.hex_effectiveness'] = 0.8


    prob.set_solver_print(level=-1)
    prob.set_solver_print(level=1, depth=1)  # (level=2, depth=1)
    # prob.check_config()

    # # Recording
    # rec = om.SqliteRecorder("debug.sql")
    # # solver = prob.model.nonlinear_solver
    # # solver = prob.model.nonlinear_solver = om.DirectSolver()
    #
    # prob.model.nonlinear_solver.add_recorder(rec)
    #
    # prob.model.nonlinear_solver.recording_options['record_outputs'] = True
    # prob.model.nonlinear_solver.recording_options['record_solver_residuals'] = True
    # prob.model.nonlinear_solver.recording_options['includes'] = ["sofc.i", "sofc.V_target", "sofc.mdot_anode_in_excess"]

    prob.model._check_required_connections()

    return prob

def save_data(prob, pt,filename):
    rows = []
    data = datafile_definition(prob, pt)
    data['point'] = pt  # add operating point label
    rows.append(data)

    # extract header from dictionary keys
    header = rows[0].keys()

    # write csv
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Data saved to {filename}")

def DOE_run_model():
    T4_list =[1100]# [1000,1200, 1300, 1400, 1500, 1600, 1800]
    power_fraction_list =[0.65]#[0.45,0.65,0.85]#[0.85, 0.65,0.45]
    N_cells_list = [20000]#[80000,100000,120000,160000]#[40000, 60000, 80000,100000,120000,160000]#[100000]#,120000,160000]#
    PR_list = [40]
    Des_pt = 'TOC'
    for PR in PR_list:
        for N_cells in N_cells_list:
            for power_fraction in power_fraction_list:
                for T4 in T4_list:
                    prob = design_problem_setup(T4, N_cells, power_fraction, PR, Des_pt)
                    try:
                        try:
                            prob.run_model()
                        except Exception as e:
                            print("Simulation crashed:", e)

                        pts = ['DESIGN'] + prob.model.od_pts

                        path_save = "Results_H2_873K_repeat/"
                        for pt in pts:
                            filename = path_save + pt + 'DES_pt_' + Des_pt + '_PFrac_' + str(power_fraction) + '_T4_' + str(
                                T4) + '_Ncells_' + str(N_cells) + '_PR_' + str(PR)+'.csv'
                            save_data(prob, pt, filename)
                    except:
                        continue

def DOE_run_model_Vcellvar():
    T4_list =[900,1200,1400]# [1000,1200, 1300, 1400, 1500, 1600, 1800]
    PR_list = [20]
    V_cell_list=[1.0]#[0.7,0.75,0.8,0.85,0.9]
    Des_pt = 'TOC'
    for PR in PR_list:
        for Vcell in V_cell_list:
            for T4 in T4_list:
                prob = design_problem_setup_Vcell(T4,PR,Des_pt,Vcell)
                try:
                    try:
                        prob.run_model()
                    except Exception as e:
                        print("Simulation crashed:", e)

                    pts = ['DESIGN'] + prob.model.od_pts

                    path_save = "Results_H2_300K/"
                    for pt in pts:
                        filename = path_save + pt + 'DES_pt_' + Des_pt + '_T4_' + str(
                            T4) + '_Vcell_' + str(Vcell) + '_PR_' + str(PR)+'.csv'
                        save_data(prob, pt, filename)
                except:
                    continue



def run_model():
    T4 = 1100
    N_cells = 40000
    power_fraction : float = 0.65
    PR = 20
    Des_pt = 'TOC'
    prob = problem_setup(T4, N_cells, power_fraction ,PR,Des_pt)
    try:
        prob.run_model()
    except Exception as e:
        print("Simulation crashed:", e)

    pts = ['DESIGN']+ prob.model.od_pts

    path_save = "Results/"
    for pt in pts:
        filename = path_save+pt+'DES_pt_'+ Des_pt +'_PFrac_'+str(power_fraction)+'_T4_'+str(T4)+'_Ncells_'+str(N_cells)+'_PR_'+str(PR)+'ncell_bal_tsofcout'+'.csv'
        save_data(prob,pt,filename)

    plot_compressor_map_with_points(prob, 'DESIGN')
    plot_compressor_map_with_points(prob, 'DESIGN', mp_single_spool.od_pts)

def run_TOC_full_load_check():
    T4 = 1100
    N_cells = 40000
    power_fraction = 0.65
    PR = 20
    Des_pt = 'TOC'

    prob = problem_setup(T4, N_cells, power_fraction, PR, Des_pt)

    toc_target_hp = 1500.0 * 1.341
    prob.set_val('TOC.balance.pwr_target', toc_target_hp, units='hp')

    print('Running 100% TOC off-design check...')
    print(f"Target TOC LP shaft net power = {toc_target_hp:.3f} hp")

    try:
        prob.run_model()
    except Exception as e:
        print("Simulation crashed:", e)
        return

    os.makedirs("Results", exist_ok=True)
    save_data(prob, 'TOC', "Results/TOC_partload_100.csv")

    actual_hp = prob.get_val('TOC.LP_shaft.pwr_net', units='hp')[0]
    target_hp = prob.get_val('TOC.balance.pwr_target', units='hp')[0]

    print(f"TOC.balance.pwr_target = {target_hp:.6f} hp")
    print(f"TOC.LP_shaft.pwr_net   = {actual_hp:.6f} hp")
    print(f"Absolute error         = {abs(actual_hp - target_hp):.6f} hp")
    print(f"Relative error         = {abs(actual_hp - target_hp)/target_hp*100:.6f} %")

def run_TOC_partload_sweep_2():
    T4 = 1100
    N_cells = 40000
    power_fraction = 0.65
    PR = 20
    Des_pt = 'TOC'

    # March from high load to low load
    #load_fracs = [1.0, 0.9, 0.8,0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
    load_fracs = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5]

    '''

    guess_map = {
        #1.0: {'W': 2200, 'mdot': 22, 'i': 10000, 'HP_Nmech': 14800, 'Pt': 4.27, 'Tt': 450, 'turbPR': 3.0},
        #0.9: {'W': 3300, 'mdot': 22, 'i': 10000, 'HP_Nmech': 14800, 'Pt': 4.27, 'Tt': 450, 'turbPR': 3.0},
        #0.8: {'W': 2200, 'mdot': 22, 'i': 10000, 'HP_Nmech': 14800, 'Pt': 4.27, 'Tt': 450, 'turbPR': 3.0},
        1.0: {'W': 3200, 'mdot': 22, 'i': 10000, 'HP_Nmech': 14800, 'Pt': 4.27, 'Tt': 460, 'turbPR': 3.0},
        # 0.9: {'W': 3300, 'mdot': 22, 'i': 10000, 'HP_Nmech': 14800, 'Pt': 4.27, 'Tt': 256, 'turbPR': 3.0},
        # 0.8: {'W': 2200, 'mdot': 22, 'i': 10000, 'HP_Nmech': 14800, 'Pt': 4.27, 'Tt': 256, 'turbPR': 3.0},
        0.7: {'W': 2500, 'mdot': 14, 'i': 8500, 'HP_Nmech': 13600, 'Pt': 4.27, 'Tt': 460, 'turbPR': 6},
        # 0.6: {'W': 2100, 'mdot': 12,  'i': 8000, 'HP_Nmech': 13600, 'Pt': 4.27, 'Tt': 256, 'turbPR': 2.4},
        # 0.5: {'W': 2000,  'mdot': 16,  'i': 8000, 'HP_Nmech': 13000, 'Pt': 4.27, 'Tt': 256, 'turbPR': 2.4},
        # 0.4: {'W': 2000,  'mdot': 16,  'i': 8000, 'HP_Nmech': 13000, 'Pt': 4.27, 'Tt': 256, 'turbPR': 2.4},
    }
    '''

    guess_map = {
        1.0: {'W': 3200, 'mdot': 22, 'i': 10000, 'HP_Nmech': 14800, 'Pt': 4.27, 'Tt': 450, 'turbPR': 3.0},
        0.9: {'W': 3000, 'mdot': 20, 'i': 8000, 'HP_Nmech': 14000, 'Pt': 4.27, 'Tt': 450, 'turbPR': 3.0},
        0.8: {'W': 2200, 'mdot': 20, 'i': 8000, 'HP_Nmech': 14000, 'Pt': 4.64, 'Tt': 450, 'turbPR': 3.0},
        0.7: {'W': 2200, 'mdot': 14, 'i': 8000, 'HP_Nmech': 13600, 'Pt': 4.27, 'Tt': 450, 'turbPR': 6},
        0.6: {'W': 2200, 'mdot': 14, 'i': 7500, 'HP_Nmech': 13121, 'Pt': 4.27, 'Tt': 450, 'turbPR': 6},
        0.5: {'W': 2200, 'mdot': 12, 'i': 6500, 'HP_Nmech': 13121, 'Pt': 4.27, 'Tt': 450, 'turbPR': 6},
        #0.4: {'W': 2200, 'mdot': 12, 'i': 5500, 'HP_Nmech': 13000, 'Pt': 4.27, 'Tt': 450, 'turbPR': 6},
        #0.3: {'W': 1700, 'mdot': 8, 'i': 4200, 'HP_Nmech': 11900, 'Pt': 4.27, 'Tt': 450, 'turbPR': 5.8},
        #0.2: {'W': 1500, 'mdot': 7.5, 'i': 3150, 'HP_Nmech': 11500, 'Pt': 4.27, 'Tt': 450, 'turbPR': 5.8},
        #0.1: {'W': 1090, 'mdot': 6, 'i': 2200, 'HP_Nmech': 10900, 'Pt': 4.27, 'Tt': 450, 'turbPR': 5.8},
    }

    os.makedirs("Results", exist_ok=True)

    # Build the model only once
    prob = problem_setup(T4, N_cells, power_fraction, PR, Des_pt)

    comp_points = []

    for k, frac in enumerate(load_fracs):
        toc_target_hp = frac * 1500.0 * 1.341
        prob.set_val('TOC.balance.pwr_target', toc_target_hp, units='hp')

        # For the first case, apply your full initial guesses
        # For later cases, only nudge if you really want to
        if k == 0:
            g = guess_map[frac]
            prob.set_val('TOC.balance.W', g['W'], units='g/s')
            prob.set_val('TOC.balance.mdot_anode_in_excess', g['mdot'], units='g/s')
            prob.set_val('TOC.balance.i_sofc', g['i'], units='A/m**2')
            prob.set_val('TOC.balance.HP_Nmech', g['HP_Nmech'], units='rpm')
            prob.set_val('TOC.fc.balance.Pt', g['Pt'], units='psi')
            prob.set_val('TOC.fc.balance.Tt', g['Tt'], units='degR')
            prob['TOC.turb.PR'] = g['turbPR']
            prob['TOC.comp.PR'] = PR
        else:
            # Continuation strategy:
            # keep previous converged state as the main initial guess
            # optionally only reset one or two sensitive values
            if frac in guess_map:
                g = guess_map[frac]
                prob.set_val('TOC.balance.mdot_anode_in_excess', g['mdot'], units='g/s')
                prob.set_val('TOC.balance.i_sofc', g['i'], units='A/m**2')

        print(f"\nRunning TOC part-load case: {int(frac*100)}%")
        print(f"Target TOC LP shaft net power = {toc_target_hp:.3f} hp")

        try:
            prob.run_model()
        except Exception as e:
            print(f"Simulation crashed at {int(frac*100)}% load: {e}")
            continue



        plot_compressor_map_with_points(prob, 'DESIGN', prob.model.od_pts)

        actual_hp = prob.get_val('TOC.LP_shaft.pwr_net', units='hp')[0]
        target_hp = prob.get_val('TOC.balance.pwr_target', units='hp')[0]

        print(f"TOC.balance.pwr_target = {target_hp:.6f} hp")
        print(f"TOC.LP_shaft.pwr_net   = {actual_hp:.6f} hp")
        print(f"Absolute error         = {abs(actual_hp - target_hp):.6f} hp")
        print(f"Relative error         = {abs(actual_hp - target_hp)/target_hp*100:.6f} %")

        Wc_val = prob.get_val('TOC.comp.Wc')[0]
        PR_val = prob.get_val('TOC.comp.PR')[0]
        comp_points.append((f'TOC {int(frac*100)}%', Wc_val, PR_val))

        if frac == 1.0:
            save_data(prob, 'DESIGN', "Results/DESIGN_TOC_partload_sweep.csv")
            print("Saved: Results/DESIGN_TOC_partload_sweep.csv")

        save_data(prob, 'TOC', f"Results/TOC_partload_{int(frac * 100)}.csv")
        print(f"Saved: Results/TOC_partload_{int(frac * 100)}.csv")

    plot_compressor_map_with_custom_points(prob, 'DESIGN', comp_points)


def plot_compressor_map_with_custom_points(prob, design_pt='DESIGN', custom_points=None, comp_name='comp'):
    """
    Plot compressor map with design point and a custom list of off-design points.
    custom_points should be a list of tuples: [(label, Wc, PR), ...]
    """

    import matplotlib.pyplot as plt
    import numpy as np

    s_Wc = prob.get_val(f'{design_pt}.{comp_name}.s_Wc')
    s_PR = prob.get_val(f'{design_pt}.{comp_name}.s_PR')
    s_eff = prob.get_val(f'{design_pt}.{comp_name}.s_eff')
    s_Nc = prob.get_val(f'{design_pt}.{comp_name}.s_Nc')

    comp = prob.model._get_subsystem(f'{design_pt}.{comp_name}')
    map_data = comp.options['map_data']

    alpha = 0
    scaled_PR = (map_data.PRmap[alpha, :, :] - 1.0) * s_PR + 1.0

    plt.figure(figsize=(11, 8))

    Nc = plt.contour(
        map_data.WcMap[alpha, :, :] * s_Wc,
        scaled_PR,
        map_data.NcMap[:, None] * s_Nc,
        colors='k',
        levels=map_data.NcMap * s_Nc
    )

    R = plt.contour(
        map_data.WcMap[alpha, :, :] * s_Wc,
        scaled_PR,
        map_data.RlineMap[None, :],
        colors='k',
        levels=map_data.RlineMap
    )

    eff = plt.contourf(
        map_data.WcMap[alpha, :, :] * s_Wc,
        scaled_PR,
        map_data.effMap[alpha, :, :] * s_eff,
        levels=np.linspace(0.6, 0.9, 10)
    )

    plt.colorbar(eff, label='Efficiency')

    design_Wc = prob.get_val(f'{design_pt}.{comp_name}.Wc')[0]
    design_PR = prob.get_val(f'{design_pt}.{comp_name}.map.scalars.PR')[0]
    plt.plot(design_Wc, design_PR, 'rs', markersize=10, label=f'Design: {design_pt}')

    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
    colors = ['blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan', 'magenta']

    if custom_points:
        for i, (label, Wc, PR) in enumerate(custom_points):
            marker = markers[i % len(markers)]
            color = colors[i % len(colors)]
            plt.plot(Wc, PR, marker=marker, color=color, linestyle='None',
                     markersize=8, label=label)

    plt.clabel(Nc, fontsize=9, inline=False)
    plt.clabel(R, fontsize=9, inline=False)
    plt.xlabel('Corrected Mass Flow (Wc), lbm/s')
    plt.ylabel('Pressure Ratio (PR)')
    plt.title('Compressor Map with All Design / Part-Load Points')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()



def run_TOC_partload_sweep():
    T4 = 1100
    N_cells = 40000
    power_fraction = 0.65
    PR = 20
    Des_pt = 'TOC'

    load_fracs = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]

    os.makedirs("Results", exist_ok=True)

    for frac in load_fracs:
        prob = problem_setup(T4, N_cells, power_fraction, PR, Des_pt)

        toc_target_hp = frac * 1500.0 * 1.341
        prob.set_val('TOC.balance.pwr_target', toc_target_hp, units='hp')

        print(f"\nRunning TOC part-load case: {int(frac*100)}%")
        print(f"Target TOC LP shaft net power = {toc_target_hp:.3f} hp")

        try:
            prob.run_model()
        except Exception as e:
            print(f"Simulation crashed at {int(frac*100)}% load:", e)
            continue

        actual_hp = prob.get_val('TOC.LP_shaft.pwr_net', units='hp')[0]
        target_hp = prob.get_val('TOC.balance.pwr_target', units='hp')[0]

        print(f"TOC.balance.pwr_target = {target_hp:.6f} hp")
        print(f"TOC.LP_shaft.pwr_net   = {actual_hp:.6f} hp")
        print(f"Absolute error         = {abs(actual_hp - target_hp):.6f} hp")
        print(f"Relative error         = {abs(actual_hp - target_hp)/target_hp*100:.6f} %")

        save_data(prob, 'TOC', f"Results/TOC_partload_{int(frac*100)}.csv")


def datafile_definition(prob, pt):
    names = ['tot:P', 'tot:T', 'tot:h', 'tot:S', 'stat:P', 'stat:T', 'stat:W', 'tot:Cp', 'tot:gamma', 'stat:MN',
             'stat:area', 'stat:Vsonic']
    units = ['kPa', 'K', 'kJ/kg', 'J/kg/K', 'kPa', 'K', 'kg/s', 'J/kg/K', None, None, 'm**2', 'm/s']

    data={}

    data['Power_fraction'] = prob.get_val(f'{pt}.P_fraction')[0]
    data['Hex_E'] = prob.get_val(f'{pt}.Hex.E')[0]
    data['Hex_UA'] = prob.get_val(f'{pt}.Hex.UA')[0]
    # ___SOFC___
    data['V_cell'] = prob.get_val(f'{pt}.sofc.V_cell', units='V')[0]
    data['i'] = prob.get_val(f'{pt}.sofc.i', units='A/m**2')[0]
    data['W_fuel_in'] =prob.get_val(f'{pt}.sofc.SOFC_0D.W_an_in_cell', units='g/s')[0]
    data['W_fuel_out'] = prob.get_val(f'{pt}.sofc.SOFC_0D.W_an_out', units='g/s')[0]
    data['W_fuel_excess_in_anode'] = prob.get_val(f'{pt}.sofc.mdot_anode_in_excess', units='g/s')[0]
    data['P_stack'] = prob.get_val(f'{pt}.Power_SOFC', units='W')[0]
    data['eff_cell'] = prob.get_val(f'{pt}.sofc.eta_sofc', units=None)[0]
    data['A_cell'] = prob.get_val('sofc.A_cell', units='m**2')[0]
    data['N_cells'] = prob.get_val(f'{pt}.sofc.N_cells', units=None)[0]
    data['U_o'] = prob.get_val(f'{pt}.sofc.SOFC_0D.U_o', units=None)[0]
    data['E_N'] = prob.get_val(f'{pt}.sofc.SOFC_0D.E_N', units='V')[0]

    data['eta_ASR'] = prob.get_val(f'{pt}.sofc.SOFC_0D.eta_ASR', units='V')[0]

    # data['eta_a'] = prob.get_val(f'{pt}.sofc.SOFC_0D.eta_a', units='V')[0]
    # data['eta_o'] = prob.get_val(f'{pt}.sofc.SOFC_0D.eta_o', units='V')[0]
    # data['eta_c'] = prob.get_val(f'{pt}.sofc.SOFC_0D.eta_c', units='V')[0]
    data['T_cell'] = prob.get_val(f'{pt}.sofc.cell_temp.T_cell', units='K')[0]
    data['T_inlet'] = prob.get_val(f'{pt}.sofc.Fl_I:tot:T', units='K')[0]

    # ___Flow Stations___
    for fs_name in FS_NAMES:
        for i, name in enumerate(names):
            full_name = '{}:{}'.format(fs_name, name)
            data[full_name] = prob.get_val(f'{pt}.'+full_name, units=units[i])[0]
    # ___Shafts___
    shaft_names = ['HP_shaft', 'LP_shaft']
    shaft_quant_names=['trq_in','trq_out','pwr_in','pwr_out','Nmech']
    shaft_units=['N*m','N*m','W','W','rpm']
    for shaft_id in shaft_names:
        for i,names in enumerate(shaft_quant_names):
            full_name = shaft_id +'.'+names
            data[full_name] = prob.get_val(f'{pt}.'+full_name, units=shaft_units[i])[0]


    return data


#for pt in ['DESIGN'] + mp_single_spool.od_pts:
    #viewer(prob, pt)


def plot_compressor_map_with_points(prob, design_pt='DESIGN', off_design_pts=None):
    """
    Plot compressor map with design and off-design operating points
    """
    comp_name = 'comp'

    # Get scaling factors from design point
    s_Wc = prob[design_pt + '.' + comp_name + '.s_Wc']
    s_PR = prob[design_pt + '.' + comp_name + '.s_PR']
    s_eff = prob[design_pt + '.' + comp_name + '.s_eff']
    s_Nc = prob[design_pt + '.' + comp_name + '.s_Nc']

    # Get map data
    comp = prob.model._get_subsystem(design_pt + '.' + comp_name)
    map_data = comp.options['map_data']

    # Create meshgrid for contours
    RlineMap, NcMap = np.meshgrid(map_data.RlineMap, map_data.NcMap, sparse=False)

    # Plot the map
    alpha = 0  # Use first alpha map
    scaled_PR = (map_data.PRmap[alpha, :, :] - 1.) * s_PR + 1.

    plt.figure(figsize=(11, 8))

    # Plot contours
    Nc = plt.contour(map_data.WcMap[alpha, :, :] * s_Wc, scaled_PR, NcMap * s_Nc,
                     colors='k', levels=map_data.NcMap * s_Nc)
    R = plt.contour(map_data.WcMap[alpha, :, :] * s_Wc, scaled_PR, RlineMap,
                    colors='k', levels=map_data.RlineMap)
    eff = plt.contourf(map_data.WcMap[alpha, :, :] * s_Wc, scaled_PR,
                       map_data.effMap[alpha, :, :] * s_eff, levels=np.linspace(0.6, 0.9, 10))

    plt.colorbar(eff, label='Efficiency')

    # Plot design point (red square)
    design_Wc = prob[design_pt + '.' + comp_name + '.Wc'][0]
    design_PR = prob[design_pt + '.' + comp_name + '.map.scalars.PR'][0]
    plt.plot(design_Wc, design_PR, 'rs', markersize=10, label='Design Point')

    # Define different markers and colors for off-design points
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', '*', 'h']
    colors = ['blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan', 'magenta']

    # Plot off-design points with different markers
    if off_design_pts:
        for i, pt in enumerate(off_design_pts):
            off_design_Wc = prob[pt + '.' + comp_name + '.Wc'][0]
            off_design_PR = prob[pt + '.' + comp_name + '.PR'][0]

            # Cycle through markers and colors
            marker = markers[i % len(markers)]
            color = colors[i % len(colors)]

            plt.plot(off_design_Wc, off_design_PR, marker=marker, color=color,
                     markersize=8, label=f'Off-Design: {pt}')

    plt.clabel(Nc, fontsize=9, inline=False)
    plt.clabel(R, fontsize=9, inline=False)
    plt.xlabel('Corrected Mass Flow (Wc), lbm/s')
    plt.ylabel('Pressure Ratio (PR)')
    plt.title('Compressor Map with Operating Points')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()

    # Add this command after prob.run_model():


#plot_compressor_map_with_points(prob, 'DESIGN')
#plot_compressor_map_with_points(prob, 'DESIGN', mp_single_spool.od_pts)

#print()
#print("time", time.time() - st)




if __name__=="__main__":




    #run_model()
    #run_TOC_full_load_check()
    run_TOC_partload_sweep_2()
    plot_compressor_map_with_points()


    # Add this command after prob.run_model():

    # DOE_run_model_Vcellvar()
    # DOE_run_model()


