from constants.c3_imports import *
from constants.c2_database_values import *

# big = 60,60,60, small = 20,20,20
NN_SIZE = {'XY': {'with naoh': 'small', 'no naoh': 'small'},  # 'small' not available
           'AA': {'with naoh': 'small', 'no naoh': 'small'},
           'AY': {'with naoh': 'small'},
           'ALOAD': {'with naoh': 'small'},
           'HS': {'with naoh': 'small', 'no naoh': 'small'}}

VLE_TYPE_NO_NaOH = 'AA'
VLE_TYPE_WITH_NaOH = 'ALOAD'

NN_DIR = r'C:\Users\caspe\PycharmProjects\MA_CJVW_Optimization\inputs\d6_trained_nn'
TRANSFORMERS_DIR = r'C:\Users\caspe\PycharmProjects\MA_CJVW_Optimization\inputs\d7_trained_nn_transformers'

# Network: [T, P, CO2_frac, Molality] -> [Y_H2O, X_CO2, Vapor Fraction]
VLE_XY_NaOH_BIG = r'251012_VLE_with_NaOH_refined_6_1'
VLE_XY_NO_NaOH_BIG = r'251014_VLE_no_NaOH_refined_2_1'

# Network: [T, P, CO2_frac, Molality] -> [A_CO2, A_H2O]  # not precise enough for big H2O inputs
VLE_A_NaOH_BIG = r'251012_VLE_with_NaOH_refined_6_2'
VLE_A_NO_NaOH_BIG = r'251014_VLE_no_NaOH_refined_2_2'
VLE_A_NaOH_SMALL = r'251015_VLE_with_NaOH_refined_1_6'
VLE_A_NO_NaOH_SMALL = r'251014_VLE_no_NaOH_refined_2_3'

# Network [T, P, CO2_frac, Molality] -> [A_CO2, Y_H2O]
VLE_AY_NaOH_BIG = r'251015_VLE_with_NaOH_refined_1_1'
VLE_AY_NaOH_SMALL = r'251015_VLE_with_NaOH_refined_1_7'

# Network: [T, P, CO2_frac, Molality] -> [A_CO2, H2O_LOAD]
VLE_LOAD_NaOH_BIG = r'251015_VLE_with_NaOH_refined_1_1'
VLE_LOAD_NaOH_SMALL = r'251015_VLE_with_NaOH_refined_1_3'

# Network [T, P, CO2_frac, Molality] -> [entropy, dH]
HS_NaOH_BIG = r'251012_VLE_with_NaOH_refined_7_2'
HS_NO_NaOH_BIG = r'251014_VLE_no_NaOH_higherT_2'
HS_NaOH_SMALL = r'251015_VLE_with_NaOH_refined_1_5'
HS_NO_NaOH_SMALL = r'251014_VLE_no_NaOH_higherT_3'


VLE_XY_NaOH = {
    'big': VLE_XY_NaOH_BIG,
    'small': None
}

VLE_XY_NO_NaOH = {
    'big': VLE_XY_NO_NaOH_BIG,
    'small': None
}

VLE_A_NaOH = {
    'big': VLE_A_NaOH_BIG,
    'small': VLE_A_NaOH_SMALL
}

VLE_A_NO_NaOH = {
    'big': VLE_A_NO_NaOH_BIG,
    'small': VLE_A_NO_NaOH_SMALL
}

VLE_AY_NaOH = {
    'big': VLE_AY_NaOH_BIG,
    'small': VLE_AY_NaOH_SMALL
}

VLE_LOAD_NaOH = {
    'big': VLE_LOAD_NaOH_BIG,
    'small': VLE_LOAD_NaOH_SMALL
}

HS_NaOH = {
    'big': HS_NaOH_BIG,
    'small': HS_NaOH_SMALL
}

HS_NO_NaOH = {
    'big': HS_NO_NaOH_BIG,
    'small': HS_NO_NaOH_SMALL
}

VLE_XY_FILES = {
    'with naoh': VLE_XY_NaOH[NN_SIZE['XY']['with naoh']],
    'no naoh':   VLE_XY_NO_NaOH[NN_SIZE['XY']['no naoh']],
}

VLE_A_BASED_FILES = {
    'with naoh': VLE_A_NaOH[NN_SIZE['AA']['with naoh']],
    'no naoh':   VLE_A_NO_NaOH[NN_SIZE['AA']['no naoh']],
}

VLE_AY_FILES = {
    'with naoh': VLE_AY_NaOH[NN_SIZE['AY']['with naoh']],
}

VLE_LOAD_FILES = {
    'with naoh': VLE_LOAD_NaOH[NN_SIZE['ALOAD']['with naoh']],
}

HS_FILES = {
    'with naoh': HS_NaOH[NN_SIZE['HS']['with naoh']],
    'no naoh':   HS_NO_NaOH[NN_SIZE['HS']['no naoh']],
}


ANN_FILES = {'XY': VLE_XY_FILES, 'AA': VLE_A_BASED_FILES, 'AY': VLE_AY_FILES, 'ALOAD': VLE_LOAD_FILES, 'HS': HS_FILES}

gas_species = ['CO2(g)', 'H2O(g)']


g_hf, g_a, g_b, g_c, g_d, g_sr, g_vr = [], [], [], [], [], [], []

for sp in gas_species:
    rec = data_dict.get(sp, {}).get('StandardThermoModel', {}).get('HollandPowell', None)
    if rec is None:
        # fallback if keys are stored without (g), e.g. "CO2" / "H2O"
        sp_base = sp.replace('(g)', '').strip()
        rec = data_dict[sp_base]['StandardThermoModel']['HollandPowell']

    g_hf.append([rec['Hf']])  # J/mol
    g_a.append([rec['a']])  # Maier–Kelley A
    g_b.append([rec['b']])  # Maier–Kelley B
    g_c.append([rec['c']])  # Maier–Kelley C
    g_d.append([rec['d']])  # Maier–Kelley D
    g_sr.append([rec['Sr']])  # J/(mol·K) at 298.15 K, 1 bar
    g_vr.append([rec['Vr']])  # m^3/mol at 298.15 K, 1 bar

Hf_GASES = np.array(g_hf)
A_GASES = np.array(g_a)
B_GASES = np.array(g_b)
C_GASES = np.array(g_c)
D_GASES = np.array(g_d)
SR_GASES = np.array(g_sr)
V_REF_GASES = np.array(g_vr)

solid_species = ['Magnesite', 'Forsterite', 'Fayalite', 'SiO2(a)']

s_hf = []
s_a = []
s_b = []
s_c = []
s_d = []

for specie in solid_species:
    s_hf.append([data_dict[specie]['StandardThermoModel']['HollandPowell']['Hf']])
    s_a.append([data_dict[specie]['StandardThermoModel']['HollandPowell']['a']])
    s_b.append([data_dict[specie]['StandardThermoModel']['HollandPowell']['b']])
    s_c.append([data_dict[specie]['StandardThermoModel']['HollandPowell']['c']])
    s_d.append([data_dict[specie]['StandardThermoModel']['HollandPowell']['d']])

Hf_SOLID = np.array(s_hf)
A_SOLID = np.array(s_a)
B_SOLID = np.array(s_b)
C_SOLID = np.array(s_c)
D_SOLID = np.array(s_d)

# Leave T and P at index 0 and 1, otherwise it will break the code
NAMES = [
    "T", "P", "CO2", "H2O", "NaOH", "enthalpy_vle", "entropy_vle",
    "Magnesite", "Forsterite", "Fayalite", "Amorphous_Silica", "enthalpy_s"
]

IDX = {name: i for i, name in enumerate(NAMES)}

VLE_SPECIES = ["CO2", "H2O", "NaOH"]
SOL_SPECIES = ["Magnesite", "Forsterite", "Fayalite", "Amorphous_Silica"]

EPSILON = 1e-16
NON_ZERO_EPSILON = 1e-10
# Thermochemical data at 298.15 K (J/mol, J/mol/K)
THERMOCHEMICAL_DATA = {
    "CO2": {"Tref": 298.15, "S298": 213.7, "Hf298": -393_510.0, "Gf298": -394_350.0},
    "H2O": {"Tref": 298.15, "S298": 188.8, "Hf298": -241_810.0, "Gf298": -228_560.0},
}
REF_STATE_AQ = {
    "CO2": {"Hf298": -413_798.0},
    "H2O": {"Hf298": -287_721.13},  # liquid ref state
    "NaOH": {"Hf298": -469_863.0}
}
REF_STATE_HS = {
    "CO2": {"Hf298": -393_510.0},
    "H2O": {"Hf298": -287_721.13},  # liquid ref state
    "NaOH": {"Hf298": -469_863.0}}

# molar masses in kg/mol
MOLAR_MASS = {
    "CO2": 0.0440095,
    "N2": 0.0280134,
    "H2O": 0.01801528,
    "NaOH": 0.039997,
    "Magnesite": 0.084313,  # MgCO3
    "Forsterite": 0.140693,  # Mg2SiO4
    "Fayalite": 0.203774,  # Fe2SiO4
    "Amorphous_Silica": 0.0600843  # SiO2
}

# density in kg/m3
DENSITY = {
    "H2O": 1000,
    "Forsterite": 3217,
    "Fayalite": 4392
}

# Ideal Gas constant
R = 8.314  # J / mol / K

# for the optimization of a cost function
PRICES = {"Electricity": 0.21,  # Euro per kWh
          "CO2": 150,  # Euro / tonne
          "H2O": 2.06,  # Euro / cum  ( I assume euro per tonne)
          "NaOH": 275,  # Euro / tonne
          "Olivine": 50}  # Euro / tonne

# for the power consumption of different units
COMPRESSOR_FACTOR = 8
PUMP_FACTOR = 1
COOL_FACTOR = 1 / 60
HEAT_FACTOR = 1
