from constants.c3_imports import *
from constants.c2_database_values import *

NN_DIR = r'C:\Users\caspe\PycharmProjects\MA_CJVW_Optimization\inputs\d6_trained_nn'
TRANSFORMERS_DIR = r'C:\Users\caspe\PycharmProjects\MA_CJVW_Optimization\inputs\d7_trained_nn_transformers'
# VLE_FILES = {'with naoh': r'DATASET_LOW_P_250911_refined_3_1', 'no naoh': r'DATASET_VAPOR_250912_refined_3_2'}
VLE_FILES = {'with naoh': r'DATASET_250911_refined_1_1', 'no naoh': r'DATASET_VAPOR_250912_refined_3_2'}
HS_FILES = {'with naoh': r'DATASET_S_H_250911_refined_1_1', 'no naoh': r'DATASET_VAPOR_250912_refined_3_1'}
ANN_FILES = {'vle': VLE_FILES, 'hs': HS_FILES}

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

# Thermochemical data at 298.15 K (J/mol, J/mol/K)
THERMOCHEMICAL_DATA = {
    "CO2": {"Tref": 298.15, "S298": 213.7, "Hf298": -393_510.0, "Gf298": -394_350.0},
    "H2O": {"Tref": 298.15, "S298": 188.8, "Hf298": -241_810.0, "Gf298": -228_560.0},
}
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
