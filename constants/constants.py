import numpy as np

from constants.imports import *
from constants.database_values import *

PT_FILE = '3107_combined(v, l, vle)_PT_1'

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
