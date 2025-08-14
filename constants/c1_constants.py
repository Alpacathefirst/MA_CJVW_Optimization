from constants.c3_imports import *
from constants.c2_database_values import *

PT_FILE = '1208_VLE_refined_1_1'  # 'A_final_refined_2_1'
NN_TYPE = 2  # Type 1: A_CO2, A_H2O, Type 2: Y_H2O, X_CO2, V-Frac

solid_species = ['Magnesite', 'Forsterite', 'Fayalite', 'SiO2(a)']

hf = []
a = []
b = []
c = []
d = []

for specie in solid_species:
    hf.append([data_dict[specie]['StandardThermoModel']['HollandPowell']['Hf']])
    a.append([data_dict[specie]['StandardThermoModel']['HollandPowell']['a']])
    b.append([data_dict[specie]['StandardThermoModel']['HollandPowell']['b']])
    c.append([data_dict[specie]['StandardThermoModel']['HollandPowell']['c']])
    d.append([data_dict[specie]['StandardThermoModel']['HollandPowell']['d']])

Hf = np.array(hf)
A = np.array(a)
B = np.array(b)
C = np.array(c)
D = np.array(d)

# Leave T and P at index 0 and 1, otherwise it will break the code
NAMES = [
    "T", "P", "CO2_vap", "N2_vap", "H2O_vap",
    "CO2_aq", "N2_aq", "H2O_aq", "NaOH_aq", "enthalpy_vle", "entropy_vle",
    "Magnesite", "Forsterite", "Fayalite", "Amorphous_Silica", "enthalpy_s"
]

IDX = {name: i for i, name in enumerate(NAMES)}

VAP_SCECIES = ["CO2_vap", "N2_vap", "H2O_vap"]
AQ_SCECIES = ["CO2_aq", "N2_aq", "H2O_aq", "NaOH_aq"]
SOL_SPECIES = ["Magnesite", "Forsterite", "Fayalite", "Amorphous_Silica"]

EPSILON = 1e-16

# molar masses in kg/mol
MOLAR_MASS = {
    "CO2": 0.0440095,
    "N2": 0.0280134,
    "H2O": 0.01801528,
    "NaOH": 0.039997,
    "Magnesite": 0.084313,         # MgCO3
    "Forsterite": 0.140693,        # Mg2SiO4
    "Fayalite": 0.203774,          # Fe2SiO4
    "Amorphous_Silica": 0.0600843  # SiO2
}
