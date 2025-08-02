from constants.imports import *
from constants.database_values import *
import numpy as np

solid_species = ['Magnesite', 'Forsterite', 'Fayalite', 'SiO2(a)']

a = []
b = []
c = []
d = []

for specie in solid_species:
    a.append([data_dict[specie]['StandardThermoModel']['HollandPowell']['a']])
    b.append([data_dict[specie]['StandardThermoModel']['HollandPowell']['b']])
    c.append([data_dict[specie]['StandardThermoModel']['HollandPowell']['c']])
    d.append([data_dict[specie]['StandardThermoModel']['HollandPowell']['d']])

A = np.array(a)
B = np.array(b)
C = np.array(c)
D = np.array(d)
