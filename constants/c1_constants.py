from constants.c3_imports import *
from constants.c2_database_values import *

NN_DIR = r'C:\Users\caspe\PycharmProjects\MA_CJVW_Optimization\inputs\d6_trained_nn'
TRANSFORMERS_DIR = r'C:\Users\caspe\PycharmProjects\MA_CJVW_Optimization\inputs\d7_trained_nn_transformers'
VLE_FILES = {'with naoh': r'DATASET_LOW_P_250911_refined_3_1', 'no naoh': r'DATASET_VAPOR_250912_refined_3_2'}
HS_FILES = {'with naoh': r'DATASET_S_H_250911_refined_1_1', 'no naoh': r'DATASET_VAPOR_250912_refined_3_1'}
ANN_FILES = {'vle': VLE_FILES, 'hs': HS_FILES}

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
    "T", "P", "CO2", "H2O", "NaOH", "enthalpy_vle", "entropy_vle",
    "Magnesite", "Forsterite", "Fayalite", "Amorphous_Silica", "enthalpy_s"
]

IDX = {name: i for i, name in enumerate(NAMES)}

VLE_SPECIES = ["CO2", "H2O", "NaOH"]
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
