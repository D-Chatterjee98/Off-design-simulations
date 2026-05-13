import sys

import openmdao.api as om

import pycycle.api as pyc

# get references right
import os
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
lib_dir = os.path.join(parentdir, "SOFC_model_HYLENA")
from pathlib import Path
sys.path.insert(0, lib_dir)

for p in sys.path:
    print(p)

from EngineSettings import EngineSettings
import pyCycle_adj.viewers_adj as v_adj
import pyCycle_adj.combustor_MN as c_adj

import pyCycle_elements.SOFC.SOFC_class_voltage_i_target as Sofc
from pyCycle_elements.SOFC.SOFC_mixer import Mixer
from pyCycle_elements.Eletric_Motor import Electric_Motor
from pyCycle_elements.HEX import HEX, HEX_cold
from pyCycle_adj.Performance_Engine import Shaft_power_fraction
from pyCycle_adj.radial_gt_map_gasturb_to_NPSS import RADIAL_GT


class SingleSpoolTurboshaft(pyc.Cycle):

    def initialize(self):
        # self.options.declare('throttle_mode', default='T4', values=['T4', 'percent_thrust'])

        self.options.declare('i_l', default=4.0e4,
                             desc='Limiting current density')
        self.options.declare('ASR', default=0.239e-4,
                             desc='Area Specific Resistance')
        self.options.declare('i0', default=645,
                             desc='Exchange current density')

        super().initialize()

    def setup(self):

        design = self.options['design']

        USE_TABULAR = False
        if USE_TABULAR:
            self.options['thermo_method'] = 'TABULAR'
            self.options['thermo_data'] = pyc.AIR_JETA_TAB_SPEC
            FUEL_TYPE = "FAR"
        else:
            self.options['thermo_method'] = 'CEA'
            self.options['thermo_data'] = pyc.species_data.janaf
            FUEL_TYPE = 'H2'

        # Add engine elements
        self.add_subsystem('fc', pyc.FlightConditions())
        self.add_subsystem('inlet', pyc.Inlet())
        self.add_subsystem('duct1', pyc.Duct())
        #self.add_subsystem('comp', pyc.Compressor(map_data=pyc.AXI5, map_extrap=True),
                           #promotes_inputs=[('Nmech', 'HP_Nmech')])
        self.add_subsystem('comp', pyc.Compressor(map_data=RADIAL_GT, map_extrap=True),
                           promotes_inputs=[('Nmech', 'HP_Nmech')])
        # HEX cold side
        self.add_subsystem('Hex_cold',HEX_cold())



        # SOFC
        self.add_subsystem('sofc',
                           Sofc.SOFC_class(i_l=self.options['i_l'], ASR=self.options['ASR'], i0=self.options['i0']),
                           promotes_outputs=[('Power_stack', 'Power_SOFC'), ('SOFC_0D.W_an_in', 'W_fuel_sofc')])
        # this needs to be defined here immediately after the declaration of the sofc object  to clear ambiguity of
        # units and val of P being promoted by two subcomponenets in the sofc class
        self.set_input_defaults('sofc.Fl_I:tot:P', val=5e5, units='Pa')
        self.set_input_defaults('sofc.Fl_I:tot:h', val=228e3, units='J/kg')
        self.set_input_defaults('sofc.Fl_I:tot:T', val = 873, units='K')

        # HEX hotside
        self.add_subsystem('Hex', HEX())
        self.connect('Hex.Q_dot_cold', 'Hex_cold.Q_dot')



        # Combustor
        # self.add_subsystem('duct3', pyc.Duct())
        # self.add_subsystem('duct4', pyc.Duct())
        self.add_subsystem('sofc_mixer', Mixer(designed_stream=1))
        self.add_subsystem('burner', c_adj.Combustor(fuel_type=FUEL_TYPE))
        # self.add_subsystem('burner', pyc.Combustor(fuel_type=FUEL_TYPE))
        # Turbine
        self.add_subsystem('duct5', pyc.Duct())
        self.add_subsystem('turb', pyc.Turbine(map_data=pyc.LPT2269, map_extrap=True),
                           promotes_inputs=[('Nmech', 'HP_Nmech')])
        # Power turbine
        self.add_subsystem('duct6', pyc.Duct())
        self.add_subsystem('pt', pyc.Turbine(map_data=pyc.LPT2269, map_extrap=True),
                           promotes_inputs=[('Nmech', 'LP_Nmech')])
        # Nozzle
        self.add_subsystem('duct7', pyc.Duct())
        self.add_subsystem('nozz', pyc.Nozzle(nozzType='CV', lossCoef='Cv'))

        # Create shaft instances. Note that LP shaft has 2 ports! => no gearbox, but electric motor
        self.add_subsystem('e_motor', Electric_Motor(),
                           promotes_inputs=[('Nmech', 'LP_Nmech'), ('P_in_elec', 'Power_SOFC')],
                           promotes_outputs=[('trq', 'motor_trq')])
        self.add_subsystem('HP_shaft', pyc.Shaft(num_ports=2), promotes_inputs=[('Nmech', 'HP_Nmech')])
        self.add_subsystem('LP_shaft', pyc.Shaft(num_ports=2), promotes_inputs=[('Nmech', 'LP_Nmech')])
        # two "burners" due to SOFC
        self.add_subsystem('perf', pyc.Performance(num_nozzles=1, num_burners=2))
        # Power split
        self.add_subsystem('Power_fraction', Shaft_power_fraction(),
                           promotes_inputs=[('trq_motor', 'motor_trq'), ('trq_turbine', 'lpt.trq')],
                           promotes_outputs=[('Shaft_fraction', 'P_fraction')])

        # Connect flow stations
        self.pyc_connect_flow('fc.Fl_O', 'inlet.Fl_I', connect_w=False)
        self.pyc_connect_flow('inlet.Fl_O', 'duct1.Fl_I')
        self.pyc_connect_flow('duct1.Fl_O', 'comp.Fl_I')

        # # With HEX
        # self.pyc_connect_flow('comp.Fl_O', 'sofc.Fl_I')
        # self.pyc_connect_flow('sofc.Fl_Oc', 'sofc_mixer.Fl_I1')
        self.pyc_connect_flow('comp.Fl_O', 'Hex.Fl_I_cold')
        self.pyc_connect_flow('comp.Fl_O', 'Hex_cold.Fl_I')
        self.pyc_connect_flow('Hex_cold.Fl_O', 'sofc.Fl_I')

        self.pyc_connect_flow('sofc.Fl_Oc', 'Hex.Fl_I_hot') # Todo: with hex
        self.pyc_connect_flow('Hex.Fl_O_hot', 'sofc_mixer.Fl_I1')
        self.pyc_connect_flow('sofc.Fl_Oa', 'sofc_mixer.Fl_I2')

        self.pyc_connect_flow('sofc_mixer.Fl_O', 'duct5.Fl_I')
        self.pyc_connect_flow('duct5.Fl_O', 'burner.Fl_I')

        self.pyc_connect_flow('burner.Fl_O', 'turb.Fl_I')
        self.pyc_connect_flow('turb.Fl_O', 'duct6.Fl_I')
        self.pyc_connect_flow('duct6.Fl_O', 'pt.Fl_I')
        self.pyc_connect_flow('pt.Fl_O', 'duct7.Fl_I')
        self.pyc_connect_flow('duct7.Fl_O', 'nozz.Fl_I')

        # Connect turbomachinery elements to shaft
        self.connect('comp.trq', 'HP_shaft.trq_0')
        self.connect('turb.trq', 'HP_shaft.trq_1')
        # LP-shaft connections
        self.connect('pt.trq', 'LP_shaft.trq_0')
        self.connect('motor_trq', 'LP_shaft.trq_1')

        # Connnect nozzle exhaust to freestream static conditions
        self.connect('fc.Fl_O:stat:P', 'nozz.Ps_exhaust')

        # Connect outputs to pefromance element
        self.connect('inlet.Fl_O:tot:P', 'perf.Pt2') # Todo: uncomment
        self.connect('comp.Fl_O:tot:P', 'perf.Pt3')
        self.connect('burner.Wfuel', 'perf.Wfuel_1')
        # self.connect('sofc.W_fuel_sofc', 'perf.Wfuel_1')
        self.connect('W_fuel_sofc', 'perf.Wfuel_0') #Todo: uncomment
        self.connect('inlet.F_ram', 'perf.ram_drag')
        # self.connect('nozz.Fg', 'perf.Fg_0')
        self.connect('LP_shaft.pwr_net', 'perf.power') #Todo: uncomment
        # self.connect('Hex.Q_dot_cold', 'Hex_cold.Q_dot')

        # moles = prob.get_val(f'sofc.anode_flow.base_thermo.n')

        # Add balances for design and off-design
        balance = self.add_subsystem('balance', om.BalanceComp())


        if design:
            # balance.add_balance('V_sofc', val=0.5, lower=0.001, upper=1.5, units='V', eq_units='hp',
            #                     rhs_name='pwr_sofc_target')
            # self.connect('balance.V_sofc', 'sofc.V_target')
            # self.connect('e_motor.P_mech', 'balance.lhs:V_sofc')
            #
            # balance.add_balance('V_sofc', val=0.5, lower=0.001, upper=1.5, units='V', eq_units=None,
            #                     rhs_name='pwr_fraction_target')
            # self.connect('balance.V_sofc', 'sofc.V_target')
            # self.connect('P_fraction', 'balance.lhs:V_sofc')

            # Balance hex effectiveness with inlet of the sofc
            balance.add_balance('hex_effectiveness', val=0.7, lower=0.1, upper=0.99, units=None, eq_units='K',
                                rhs_name='T_inlet_target')
            self.connect('balance.hex_effectiveness', 'Hex.E')
            self.connect('Hex.Fl_O_cold:tot:T', 'balance.lhs:hex_effectiveness')

            # balance.add_balance('i_sofc', val=5000, lower=1000, upper=30000, units='A/m**2', eq_units='hp',
            #                     rhs_name='pwr_sofc_target')
            # self.connect('balance.i_sofc', 'sofc.i')
            # self.connect('e_motor.P_mech', 'balance.lhs:i_sofc')

            balance.add_balance('i_sofc', val=5000, lower=100, upper=30000, units='A/m**2', eq_units='V',
                                rhs_name='V_target')
            self.connect('balance.i_sofc', 'sofc.i')
            self.connect('sofc.V_cell', 'balance.lhs:i_sofc')

            balance.add_balance('Ncells_sofc', val=80000, lower=10000, upper=800000, units=None, eq_units='K',
                                rhs_name='T_sofc_target')
            self.connect('balance.Ncells_sofc', 'sofc.N_cells')
            self.connect('sofc.Fl_Oc:tot:T', 'balance.lhs:Ncells_sofc')

            balance.add_balance('W', val=5000.0, lower=50, upper=100000, units='g/s', eq_units=None,
                                rhs_name='nozz_PR_target')
            self.connect('balance.W', 'inlet.Fl_I:stat:W')
            self.connect('nozz.PR', 'balance.lhs:W')

            # balance.add_balance('W', val=5000.0, lower=50, upper=100000, units='g/s', eq_units='K',
            #                     rhs_name='T_sofc_target')
            # self.connect('balance.W', 'inlet.Fl_I:stat:W')
            # self.connect('sofc.Fl_Oc:tot:T', 'balance.lhs:W')

            balance.add_balance('mdot_anode_in_excess', val=50, lower=1.0, upper=20000, units='g/s', eq_units='K',
                                rhs_name='T4_target')
            self.connect('balance.mdot_anode_in_excess', 'sofc.mdot_anode_in_excess')
            self.connect('sofc_mixer.Fl_O:tot:T', 'balance.lhs:mdot_anode_in_excess')

            balance.add_balance('turb_PR', val=1.5, lower=1.001, upper=16, eq_units='hp', rhs_val=0.0)
            self.connect('balance.turb_PR', 'turb.PR')
            self.connect('HP_shaft.pwr_net', 'balance.lhs:turb_PR')

            balance.add_balance('pt_PR', val=1.5, lower=1.001, upper=16, eq_units='hp', rhs_name='pwr_target')
            self.connect('balance.pt_PR', 'pt.PR')
            self.connect('LP_shaft.pwr_net', 'balance.lhs:pt_PR')



        else:
            # balance.add_balance('V_sofc', val=0.5, lower=0.001, upper=1.0, units='V', eq_units='K',
            #                    rhs_name='T_sofc_target')
            # self.connect('balance.V_sofc', 'sofc.V_target')
            # self.connect('sofc.Fl_Oc:tot:T', 'balance.lhs:V_sofc')

            # balance.add_balance('V_sofc', val=0.5, lower=0.001, upper=1.5, units='V', eq_units='hp',
            #                     rhs_name='pwr_sofc_target')
            # self.connect('balance.V_sofc', 'sofc.V_target')
            # self.connect('e_motor.P_mech', 'balance.lhs:V_sofc')
            # balance.add_balance('i_sofc', val=5000, lower=1000, upper=30000, units='A/m**2', eq_units='K',
            #                     rhs_name='T_inlet_target')
            # self.connect('balance.i_sofc', 'sofc.i')
            # self.connect('Hex.Fl_O_cold:tot:T', 'balance.lhs:i_sofc')

            # balance.add_balance('i_sofc', val=5000, lower=1000, upper=30000, units='A/m**2', eq_units='m**2')
            #
            # self.connect('balance.i_sofc', 'sofc.i')
            # self.connect('nozz.Throat:stat:area', 'balance.lhs:i_sofc')

            # balance.add_balance('i_sofc', val=5000, lower=100, upper=30000, units='A/m**2', eq_units='V',
            #                     rhs_name='V_target')
            # self.connect('balance.i_sofc', 'sofc.i')
            # self.connect('sofc.V_cell', 'balance.lhs:i_sofc')

            balance.add_balance('W', val=5000.0, lower=50, upper=100000, units='g/s', eq_units='m**2')
            self.connect('balance.W', 'inlet.Fl_I:stat:W')
            self.connect('nozz.Throat:stat:area', 'balance.lhs:W')

            # balance.add_balance('W', val=5000.0, lower=50, upper=100000, units='g/s', eq_units='K',
            #                     rhs_name='T_sofc_target')
            # self.connect('balance.W', 'inlet.Fl_I:stat:W')
            # self.connect('sofc.Fl_Oc:tot:T', 'balance.lhs:W')




            #balance.add_balance('i_sofc', val=5000, lower=100, upper=30000, units='A/m**2', eq_units='V',
                                #rhs_name='V_target')
            #self.connect('balance.i_sofc', 'sofc.i')
            #self.connect('sofc.V_cell', 'balance.lhs:i_sofc')

            balance.add_balance('i_sofc', val=1000, lower=100, upper=30000, units='A/m**2', eq_units='K',
                                rhs_name='T_sofc_target')
            self.connect('balance.i_sofc', 'sofc.i')
            self.connect('sofc.Fl_Oc:tot:T', 'balance.lhs:i_sofc')

            #balance.add_balance('i_sofc', val=1000, lower=100, upper=30000, units='A/m**2', eq_units='K',
                                #rhs_name='T_inlet_target')
            #self.connect('balance.i_sofc', 'sofc.i')
            #self.connect('Hex.Fl_O_cold:tot:T', 'balance.lhs:i_sofc')




            # balance.add_balance('i_sofc', val=5000, lower=1000, upper=15000, units='A/m**2', eq_units='hp',
            #                     rhs_name='pwr_sofc_target')
            # self.connect('balance.i_sofc', 'sofc.i')
            # self.connect('e_motor.P_mech', 'balance.lhs:i_sofc')


            balance.add_balance('mdot_anode_in_excess', val=50, lower=1.0, upper=20000, units='g/s', eq_units='hp', rhs_name='pwr_target')
            self.connect('balance.mdot_anode_in_excess', 'sofc.mdot_anode_in_excess')
            self.connect('LP_shaft.pwr_net', 'balance.lhs:mdot_anode_in_excess')

            balance.add_balance('HP_Nmech', val=15000, units='rpm', lower=500., eq_units='hp', rhs_val=0.0)
            self.connect('balance.HP_Nmech', 'HP_Nmech')
            self.connect('HP_shaft.pwr_net', 'balance.lhs:HP_Nmech')



        # Setup solver to converge engine
        # self.set_order(
        #     ['fc', 'inlet', 'comp', 'burner', 'turb', 'pt', 'nozz', 'HP_shaft', 'LP_shaft', 'perf', 'balance'])
        # self.set_order(
        #     ['fc', 'inlet','duct1','comp','duct2','sofc','duct3','duct4','sofc_mixer','duct5','turb','duct6','pt','duct7',
        #      'nozz', 'HP_shaft', 'LP_shaft', 'Power_fraction','e_motor','balance','perf'])
        self.set_order(
            ['fc', 'inlet', 'duct1', 'comp','Hex_cold','sofc','Hex','sofc_mixer', 'duct5', 'burner', 'turb', 'HP_shaft', 'duct6',
             'pt', 'duct7','e_motor','LP_shaft', 'nozz', 'balance','perf','Power_fraction'])

        if design:
            newton = self.nonlinear_solver = om.NewtonSolver()  # om.NonlinearBlockGS()#
            newton.options['atol'] = 1e-10
            newton.options['rtol'] = 1e-8
            newton.options['iprint'] = 2
            newton.options['maxiter'] = 200#Todo: change this to 10 for quick results and converges only for DESIGN pt
            newton.options['solve_subsystems'] = True
            newton.options['max_sub_solves'] = 10#10 #Todo: change to 5 for quick results and converges only for DESIGN pt
            newton.options['reraise_child_analysiserror'] = False


            # newton.linesearch = om.BoundsEnforceLS()
            newton.linesearch = om.ArmijoGoldsteinLS()
            newton.linesearch.options['iprint'] = -1
            newton.linesearch.options['maxiter'] = 10
            newton.linesearch.options['rho'] = 0.75

            self.linear_solver = om.DirectSolver()
        else:

            '''
            newton = self.nonlinear_solver = om.NewtonSolver()  # om.NonlinearBlockGS()#
            newton.options['atol'] = 1e-8
            newton.options['rtol'] = 1e-4
            newton.options['iprint'] = 0
            newton.options['maxiter'] = 100
            newton.options['solve_subsystems'] = True
            newton.options['max_sub_solves'] = 5
            newton.options['reraise_child_analysiserror'] = False

            newton.linesearch = om.ArmijoGoldsteinLS()
            newton.linesearch.options['iprint'] = -1
            newton.linesearch.options['maxiter'] = 6
            newton.linesearch.options['rho'] = 0.5
            newton.linesearch.options['alpha'] = 0.3

            '''

            newton = self.nonlinear_solver = om.NewtonSolver()  # om.NonlinearBlockGS()#
            newton.options['atol'] =1e-10
            newton.options['rtol'] = 1e-4
            newton.options['iprint'] = 2
            newton.options[
                'maxiter'] = 100 #750 #850 Todo: change this to 10 for quick results and converges only for DESIGN pt
            newton.options['solve_subsystems'] = True
            newton.options[
                'max_sub_solves'] = 5 #10  # 10 #Todo: change to 5 for quick results and converges only for DESIGN pt
            newton.options['reraise_child_analysiserror'] = False
            # newton.options['relaxation_factor'] = 0.3

            # newton.linesearch = om.BoundsEnforceLS()
            newton.linesearch = om.ArmijoGoldsteinLS()#bound_enforcement='scalar')
            newton.linesearch.options['iprint'] = 2
            newton.linesearch.options['maxiter'] = 6 #12
            newton.linesearch.options['rho'] = 0.75 # contraction factor
            newton.linesearch.options['alpha'] = 0.7 # initial line search step: default=1.0
            


            self.linear_solver = om.DirectSolver()

        super().setup()


def viewer(prob, pt, file=sys.stdout):
    """
    print a report of all the relevant cycle properties
    """

    # summary_data = (prob[pt + '.fc.Fl_O:stat:MN'], prob[pt + '.fc.alt'], prob[pt + '.inlet.Fl_O:stat:W'],
    #                 prob[pt + '.perf.Fn'], prob[pt + '.perf.Fg'], prob[pt + '.inlet.F_ram'],
    #                 prob[pt + '.perf.OPR'], prob[pt + '.perf.PSFC'])

    print(file=file, flush=True)
    print(file=file, flush=True)
    print(file=file, flush=True)
    print("----------------------------------------------------------------------------", file=file, flush=True)
    print("                              POINT:", pt, file=file, flush=True)
    print("----------------------------------------------------------------------------", file=file, flush=True)
    print("                       PERFORMANCE CHARACTERISTICS", file=file, flush=True)
    print("    Mach      Alt       W      Fn      Fg    Fram     OPR     PSFC ")
    # print(" %7.5f  %7.1f %7.3f %7.1f %7.1f %7.1f %7.3f  %7.5f" % summary_data)

    # fs_names = ['fc.Fl_O', 'inlet.Fl_O', 'comp.Fl_O', 'Hex.Fl_O_cold',
    #             'sofc.Fl_Oc', 'sofc.Fl_Oa','Hex.Fl_O_hot',
    #             'sofc_mixer.Fl_O', 'burner.Fl_O','turb.Fl_O', 'pt.Fl_O',
    #             'nozz.Fl_O']

    fs_names = ['fc.Fl_O', 'inlet.Fl_O', 'comp.Fl_O','Hex_cold.Fl_O','Hex.Fl_O_cold',
                'sofc.Fl_Oc', 'sofc.Fl_Oa', 'Hex.Fl_O_hot','sofc_mixer.Fl_O',
                'burner.Fl_O','turb.Fl_O', 'pt.Fl_O','nozz.Fl_O']
    # fs_names = ['fc.Fl_O', 'inlet.Fl_O', 'comp.Fl_O',
    #             'sofc.Fl_Oc', 'sofc.Fl_Oa', 'sofc_mixer.Fl_O', 'burner.Fl_I',
    #             'burner.Fl_O', 'turb.Fl_O', 'pt.Fl_O', 'nozz.Fl_O']

    fs_full_names = [f'{pt}.{fs}' for fs in fs_names]
    v_adj.print_flow_station(prob, fs_full_names, file=file)

    comp_names = ['comp']
    comp_full_names = [f'{pt}.{c}' for c in comp_names]
    pyc.print_compressor(prob, comp_full_names, file=file)
    v_adj.print_sofc_wo_Uf(prob, [f'{pt}.sofc'], file=file)

    v_adj.print_burner(prob, [f'{pt}.burner'], file=file)

    v_adj.print_mixer(prob, [f'{pt}.sofc_mixer'], file=file)

    burner_names = ['burner']
    burner_full_names = [f'{pt}.{br}' for br in burner_names]
    v_adj.print_burner(prob, burner_full_names, file=file)

    turb_names = ['turb', 'pt']
    turb_full_names = [f'{pt}.{t}' for t in turb_names]
    pyc.print_turbine(prob, turb_full_names, file=file)

    noz_names = ['nozz']
    noz_full_names = [f'{pt}.{n}' for n in noz_names]
    pyc.print_nozzle(prob, noz_full_names, file=file)

    shaft_names = ['HP_shaft', 'LP_shaft']
    shaft_full_names = [f'{pt}.{s}' for s in shaft_names]
    pyc.print_shaft(prob, shaft_full_names, file=file)


class MPSingleSpool(pyc.MPCycle):
    def __init__(self, settings, **kwargs):
        super().__init__(**kwargs)
        self.settings = settings  # store the dict
        self.dT_ISA_design = 10 # K
        self.od_pts = settings.od_pts
        self.od_ISA_dT = settings.od_ISA_dT
        self.od_MNs = settings.od_MNs
        self.od_alts = settings.od_alts
        self.od_pwrs_kw = settings.od_pwrs_kw
        self.od_pwr_frac = settings.od_pwr_frac
        self.od_nmechs = settings.od_nmechs

        # self.od_pts = ['Cruise', 'TOC', 'MTO']
        # self.od_ISA_dT = [0,10,15]
        # self.od_MNs = [0.44,0.35, 0.18]
        # self.od_alts = [24000,24000, 0.0]
        # self.od_pwrs_kw = [1320,1500, 3450]
        # self.od_pwr_frac = [0.45, 0.45, 0.15]
        # self.od_nmechs = [15000, 15000, 20000]

    def setup(self):
        # Create design instance of model
        self.pyc_add_pnt('DESIGN', SingleSpoolTurboshaft(thermo_method='CEA', i_l=self.settings.SOFC_i_l, ASR=self.settings.SOFC_ASR,
                                        i0=self.settings.SOFC_i0))
        # self.set_input_defaults('DESIGN.inlet.Fl_I:stat:W', 100.264, units='kg/s')
        self.set_input_defaults('DESIGN.HP_Nmech', 14800.0, units='rpm')
        self.set_input_defaults('DESIGN.LP_Nmech', 12750.0, units='rpm')
        self.set_input_defaults('DESIGN.inlet.MN', 0.1)
        self.set_input_defaults('DESIGN.comp.MN', 0.20)
        self.set_input_defaults('DESIGN.burner.MN', 0.20)
        self.set_input_defaults('DESIGN.turb.MN', 0.3)
        self.set_input_defaults('DESIGN.pt.MN', 0.4)
        # self.set_input_defaults('DESIGN.Hex_cold.MN', 0.2)
        # self.set_input_defaults('DESIGN.Hex.Fl_I_cold:stat.MN', 0.2)
        # self.set_input_defaults('DESIGN.Hex.Fl_I_hot:stat.MN', 0.2)
        # self.set_input_defaults('DESIGN.pt.PR', val=3.0)

        # self.pyc_add_cycle_param('burner.dPqP', .03)
        self.pyc_add_cycle_param('nozz.Cv', 0.99)

        # --- Set up SOFC values ---
        self.set_input_defaults('DESIGN.sofc.MN', self.settings.des_sofc_MN)  # Same as combustor for now
        self.set_input_defaults('DESIGN.fc.dTs', self.dT_ISA_design, units= 'K')

        self.pyc_add_cycle_param('sofc.dPqP', self.settings.SOFC_dPqP_cathode)
        self.pyc_add_cycle_param('sofc.dPqP_anode', self.settings.SOFC_dPqP_anode)
        # self.pyc_add_cycle_param('sofc.alpha', self.settings.SOFC_alpha)
        self.pyc_add_cycle_param('sofc.A_cell', self.settings.SOFC_A_cell, units='cm**2')
        self.pyc_add_cycle_param('sofc.x_H2', self.settings.SOFC_x_H2)
        self.pyc_add_cycle_param('e_motor.eff', self.settings.motor_eff)




        for i, pt in enumerate(self.od_pts):
            self.pyc_add_pnt(pt, SingleSpoolTurboshaft(design=False, thermo_method='CEA',i_l=self.settings.SOFC_i_l, ASR=self.settings.SOFC_ASR,
                                        i0=self.settings.SOFC_i0))

            self.set_input_defaults(pt + '.fc.alt', self.od_alts[i], units='ft')
            self.set_input_defaults(pt + '.fc.MN', self.od_MNs[i])
            self.set_input_defaults(pt + '.LP_Nmech', self.od_nmechs[i], units='rpm')
            self.set_input_defaults(pt + '.balance.pwr_target', self.od_pwrs_kw[i]*1.341, units='hp')
            # self.set_input_defaults(pt + '.balance.T_sofc_target', 750+273.15, units='K')
            # self.set_input_defaults(pt + '.balance.pwr_sofc_target', self.od_pwrs_kw[i] * 1.341 * self.od_pwr_frac[i], units='hp')
            self.set_input_defaults(pt + '.fc.dTs', self.od_ISA_dT[i], units='K')

        if len(self.od_pts)>0:
            self.pyc_use_default_des_od_conns()
            self.pyc_connect_des_od('nozz.Throat:stat:area', 'balance.rhs:W')
            # self.pyc_connect_des_od('nozz.Throat:stat:area', 'balance.rhs:i_sofc')
            # self.pyc_connect_des_od('nozz.Throat:stat:area', 'nozz.Throat:stat:area')

        super().setup()

import matplotlib.pyplot as plt

class SolverMonitor:
    def __init__(self, prob, vars_to_track):
        self.prob = prob
        self.vars = vars_to_track
        self.data = {v: [] for v in vars_to_track}
        self.iters = []

        plt.ion()
        self.fig, self.ax = plt.subplots()

    def update(self, iteration):
        self.iters.append(iteration)

        for v in self.vars:
            val = self.prob.get_val(v)
            self.data[v].append(val)

        self.ax.clear()

        for v in self.vars:
            self.ax.plot(self.iters, self.data[v], label=v)

        self.ax.legend()
        self.ax.set_xlabel("Iteration")
        self.ax.set_ylabel("Value")

        plt.pause(0.01)

if __name__ == "__main__":

    import time

    prob = om.Problem()

    settings = EngineSettings(
        Power_target=0.85,
    )

    prob.model = mp_single_spool = MPSingleSpool(settings)

    prob.setup()

    # Define the design point
    settings.SOFC_N_cells =80000#Todo: working case =20000
    prob.set_val('DESIGN.sofc.N_cells', settings.SOFC_N_cells)
    prob.model.add_constraint('sofc.T_cell', lower=600, upper=750,units='degC')
    # prob.set_val('DESIGN.sofc.mdot_anode_in_excess', 10, units='g/s')
    # prob.set_val('DESIGN.sofc.i', 4500, units='A/m**2')
    # prob.set_val('DESIGN.balance.V_target', 0.6)

    # Max_power = 3.5 / (2500 * 1000) * (settings.SOFC_N_cells * settings.SOFC_A_cell)

    # prob.set_val('DESIGN.fc.alt', 10000, units='ft')
    # prob.set_val('DESIGN.fc.MN', 0.3)
    prob.set_val('DESIGN.fc.alt', settings.des_alt, units='ft')
    prob.set_val('DESIGN.fc.MN', settings.des_mach_no)
    #minimize T_SOFC_target
    # ivc = om.IndepVarComp()
    # ivc.add_output('T_SOFC_target', val=700,units='degC')
    # prob.model.add_subsystem('ivc', ivc, promotes=['T_SOFC_target'])
    # prob.model.add_design_var('T_SOFC_target', lower=600, upper=750,units='degC')
    # prob.model.add_design_var('T_SOFC_target', lower=1661, upper=1841, units='degR')
    # prob.model.add_objective('T_SOFC_target', scaler=-1.0)
    # prob.set_val('DESIGN.balance.T_sofc_target', 1023.0, units='K')
    pwr_shaft = settings.des_pwr_shaft
    prob.set_val('DESIGN.balance.pwr_target', pwr_shaft*(1), units='hp')
    # prob.set_val('DESIGN.balance.power_gt_fraction_target', (1-settings.Power_target), units=None)
    prob.set_val('DESIGN.balance.pwr_sofc_target', pwr_shaft * (settings.Power_target), units='hp')
    # prob.set_val('DESIGN.balance.pwr_fraction_target', (settings.Power_target), units=None)
    # prob.set_val('DESIGN.balance.i_sofc_target', 9000, units='A/m**2')
    # prob.set_val('DESIGN.balance.power_fraction_target', (settings.Power_target), units=None)
    prob.set_val('DESIGN.balance.T4_target', 1200, units='K') # Todo: working case = 1600
    prob.set_val('DESIGN.balance.T_inlet_target', 873, units='K')
    # prob.set_val('DESIGN.balance.eta_sofc_target', 0.50, units=None)
    # prob.set_val('DESIGN.balance.pwr_fraction', settings.Power_target, units=None)
    # prob.set_val('DESIGN.balance.Power_target', (settings.Power_target), units=None)
    prob.set_val('DESIGN.balance.nozz_PR_target', 1.2)
    prob.set_val('DESIGN.comp.PR', 10)
    # prob.set_val('DESIGN.balance.comp_PR_target', 10)
    prob.set_val('DESIGN.comp.eff', 0.83)
    prob.set_val('DESIGN.turb.eff', 0.86)
    prob.set_val('DESIGN.pt.eff', 0.9)
    # prob.set_val('DESIGN.nozz.PR', 1.1)

    prob.set_val('DESIGN.burner.Fl_I:FAR', 1e-10)


    # Set initial guesses for balances
    # prob['DESIGN.balance.FAR'] = 0.012#0.0175506829934

    prob['DESIGN.balance.W'] = 1000.0 #g/s Todo: working case =1000 g/s
    prob['DESIGN.balance.turb_PR'] = 2#3.8768
    prob['DESIGN.balance.pt_PR'] = 4  # 3.8768
    prob['DESIGN.balance.mdot_anode_in_excess'] = 20.0  #g/s  Todo: working case =30 g/s

    # prob['DESIGN.balance.pt_PR'] = 1.5#1.5#2.
    # prob['DESIGN.balance.Ncells_sofc'] = 40000
    prob['DESIGN.balance.i_sofc'] = 3000
    prob['DESIGN.fc.balance.Pt'] = 5.66#14.69551131598148
    prob['DESIGN.fc.balance.Tt'] = 518.665288153
    # prob['DESIGN.balance.hex_effectiveness']=0.8
    #
    for i, pt in enumerate(mp_single_spool.od_pts):
        #hardcoded values
        prob.set_val(pt+'.sofc.N_cells', settings.SOFC_N_cells)
        prob[pt + '.burner.Fl_I:FAR']= 1e-10
        # initial guesses
        prob[pt + '.balance.W'] = 7500.0
        # prob[pt + '.balance.FAR'] = 0.0175506829934
        prob[pt + '.balance.mdot_anode_in_excess'] = 40.0  # g/s  Todo: working case =30 g/s
        # prob[pt + '.balance.V_sofc'] = 0.5
        prob[pt + '.balance.HP_Nmech'] = 15000.0
        prob[pt + '.fc.balance.Pt'] = 15.703
        prob[pt + '.fc.balance.Tt'] = 558.31
        prob[pt + '.turb.PR'] = 2
        prob[pt + '.pt.PR'] = 4
    #
    # st = time.time()

    prob.set_solver_print(level=-1)
    prob.set_solver_print(level=1, depth=1)#(level=2, depth=1)
    # prob.check_config()

    #Recording
    rec = om.SqliteRecorder("debug.sql")
    # solver = prob.model.nonlinear_solver
    # solver = prob.model.nonlinear_solver = om.DirectSolver()

    prob.model.nonlinear_solver.add_recorder(rec)

    prob.model.nonlinear_solver.recording_options['record_outputs'] = True
    prob.model.nonlinear_solver.recording_options['record_solver_residuals'] = True
    prob.model.nonlinear_solver.recording_options['includes'] = [ "sofc.i","sofc.V_target","sofc.mdot_anode_in_excess"]



    # solver.add_recorder(rec)
    # prob.driver.add_recorder(rec)
    #
    # # solver.recording_options['record_outputs'] = True
    # prob.driver.recording_options['record_outputs'] = True
    # prob.driver.recording_options['record_inputs'] = True
    # prob.driver.recording_options['record_objectives'] = True
    # prob.driver.recording_options['record_constraints'] = True
    # prob.driver.recording_options['record_desvars'] = True
    # prob.driver.recording_options['includes'] = [
    #     'DESIGN.sofc.anode_flow_inlet.composition'
    # ]
    # solver.recording_options['includes'] = [
    #     'DESIGN.sofc.anode_flow_inlet.composition'
    # ]

    # prob.find_feasible()

    # monitor = SolverMonitor(
    #     prob,
    #     [
    #         "sofc.i",
    #         "sofc.V_target",
    #         "sofc.mdot_anode_in_excess"
    #     ]
    # )
    prob.model._check_required_connections()



    try:
        prob.run_model()
    except Exception as e:
        print("Simulation crashed:", e)

    #plot_compressor_map_with_points(prob, 'DESIGN', prob.model.od_pts)


    for pt in ['DESIGN'] + mp_single_spool.od_pts:
        viewer(prob, pt)





    # Add this command after prob.run_model():
    #plot_compressor_map_with_points(prob, 'DESIGN')
    #plot_compressor_map_with_points(prob, 'DESIGN', mp_single_spool.od_pts)

    print()
    # print("time", time.time() - st)