from dataclasses import dataclass, field

@dataclass
class EngineSettings:
    # --- Core cycle settings ---
    alt_ft_dict={'Cruise':24000, 'MTO': 0, 'TOC': 24000}
    mach_no_dict={'Cruise':0.44, 'MTO': 0.18, 'TOC': 0.35}
    ISA_dict={'Cruise':0, 'MTO': 15, 'TOC': 10}
    pwr_shaft_kW = {'Cruise':1320, 'MTO': 3450, 'TOC': 1500}
    pwr_frac_dict = {'Cruise':0.45, 'MTO': 0.10, 'TOC': 0.65}
    LP_NMech_dict = {'Cruise': 12000, 'MTO': 15000, 'TOC': 12750}
    des_alt: float = 24000        # [ft]
    des_mach_no: float = 0.44
    des_pwr_shaft: float = 1320 *1.341#1320 *1.341# [kW*1.341]=[hp]
    des_ISA_dT = 0
    od_pts = ['TOC','Cruise','MTO']#,'MTO']#'TOC',



    # --- SOFC integration ---
    Power_target: float = 0.1   # Fraction of total input
    des_sofc_MN: float = 0.02#15   # Mach number at SOFC exit
    SOFC_dPqP_cathode: float = 0.05     # Fractional pressure drop across cathode
    SOFC_dPqP_anode: float = 0.05       # Fractional pressure drop across anode
    SOFC_P_anode_inlet: float = 1000    # Pressure at anode inlet [kPa]
    SOFC_alpha: float = 0.5     # Cathode Utilization Factor
    SOFC_i_l: float = 4.0e4     # Limiting current density [A/m^2]
    SOFC_ASR: float = 0.239e-4    # Area Specific Resistance [Ohm*m**2]
    SOFC_i0: float = 645.0       # Exchange current density [A/m^2]
    SOFC_A_cell: float = 50#1000   # [cm^2]
    SOFC_N_cells: int = 2500    # Number of cells
    SOFC_x_H2: float = 1        # Hydrogen mole fraction
    motor_eff: float = 0.95     # Motor efficiency

    def __post_init__(self):
        self.od_ISA_dT = [self.ISA_dict[i] for i in self.od_pts]
        self.od_MNs = [self.mach_no_dict[i] for i in self.od_pts]
        self.od_alts = [self.alt_ft_dict[i] for i in self.od_pts]
        self.od_pwrs_kw = [self.pwr_shaft_kW[i] for i in self.od_pts]
        self.od_pwr_frac = [self.pwr_frac_dict[i] for i in self.od_pts]
        self.od_nmechs = [self.LP_NMech_dict[i] for i in self.od_pts]



