import sys

sys.path.append(r"C:\Users\caspe\maingo\maingo\build\Release")

import numpy as np
import maingopy
# from get_min_max import *
from process import EvaluateProcess


# To define a model, we need to spcecialize the MAiNGOmodel class
class Model(maingopy.MAiNGOmodel):
    def __init__(self, pt_file, ph_file):
        self.pt_file = pt_file
        self.ph_file = ph_file
        maingopy.MAiNGOmodel.__init__(self)
        self.pt_flash = maingopy.melonpy.FeedForwardNet()
        self.ph_flash = maingopy.melonpy.FeedForwardNet()
        self.path = "inputs/d6_trained_nn"
        self.pt_flash.load_model(self.path, f'{file_pt}.xml', maingopy.melonpy.XML)
        self.ph_flash.load_model(self.path, f'{file_ph}.xml', maingopy.melonpy.XML)
        # Initialize feedforward neural network and load data from example csv file
        self.process = EvaluateProcess(self)

    # We need to implement the get_variables functions for specifying the optimization variables
    def get_variables(self):
        # define bounds of the original variables, so that it rescales the results of the optimization
        # the optimization is done with the normalized version of these values
        unit_variables = [
                     maingopy.OptimizationVariable(maingopy.Bounds(290, 400), maingopy.VT_CONTINUOUS, "T_Mixer")
                     ]
        # tear_stream_vars = [
        #     maingopy.OptimizationVariable(maingopy.Bounds(295, 400), maingopy.VT_CONTINUOUS, "T"),
        #     maingopy.OptimizationVariable(maingopy.Bounds(1e5, 5e6), maingopy.VT_CONTINUOUS, "P"),
        #     maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 100), maingopy.VT_CONTINUOUS, "CO2_vap"),
        #     maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 100), maingopy.VT_CONTINUOUS, "N2_vap"),
        #     maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 100), maingopy.VT_CONTINUOUS, "H2O_vap"),
        #     maingopy.OptimizationVariable(maingopy.Bounds(-1e6, 1e6), maingopy.VT_CONTINUOUS, "enthalpy_vap"),
        #     maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 100), maingopy.VT_CONTINUOUS, "CO2_aq"),
        #     maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 100), maingopy.VT_CONTINUOUS, "N2_aq"),
        #     maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 100), maingopy.VT_CONTINUOUS, "H2O_aq"),
        #     maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 100), maingopy.VT_CONTINUOUS, "NaOH_aq"),
        #     maingopy.OptimizationVariable(maingopy.Bounds(-1e6, 1e6), maingopy.VT_CONTINUOUS, "enthalpy_aq"),
        #     maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 100), maingopy.VT_CONTINUOUS, "Magnesite"),
        #     maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 100), maingopy.VT_CONTINUOUS, "Forsterite"),
        #     maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 100), maingopy.VT_CONTINUOUS, "Fayalite"),
        #     maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 100), maingopy.VT_CONTINUOUS, "Amorphous_Silica"),
        #     maingopy.OptimizationVariable(maingopy.Bounds(-1e6, 1e6), maingopy.VT_CONTINUOUS, "enthalpy_s"),
        # ]

        variables = unit_variables
        return variables

    # We need to implement the evaluate function that computes the values of the objective and constraints from the
    # variables. Note that the variables in the 'vars' argument of this function do correspond to the optimization
    # variables defined in the get_variables function. However, they are different objects for technical reasons.
    # The only mapping we have between them is the position in the list.
    # The results of the evaluation (i.e., objective and constraint values) need to be return in an EvaluationContainer
    def evaluate(self, vars):
        # [0, 1, 2      , 3     , 4      , 5           , 6     , 7    , 8     , 9      , 10         , 11       , 12        , 13      , 14              , 15        ]
        # [T, P, CO2_vap, N2_vap, H2O_vap, enthalpy_vap, CO2_aq, N2_aq, H2O_aq, NaOH_aq, enthalpy_aq, Magnesite, Forsterite, Fayalite, Amorphous_Silica, enthalpy_s]
        co2_in = np.array([60, 100, 60, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        sla_in = np.array([60, 100, 0, 0, 0, 0, 0, 0, 100, 1, 0, 0, 10, 5, 0, 0])
        proccess_inputs = [co2_in, sla_in]
        # t_reactor, p_reactor, t_flash, p_flash
        parameters = [170+273.15, 100, 298.15, 1]
        eq_constraints, objective = self.process.equations(proccess_inputs, vars, parameters)

        # the result
        result = maingopy.EvaluationContainer()
        # constraints
        # add equalities with result.eq = [equation]
        # result.eq = eq_constraints
        # add inequalities with result.ineq = [equation]
        result.objective = objective**2
        return result


# To work with the problem, we first create an instance of the model.
file_pt = '3107_combined(v, l, vle)_PT_1'
file_ph = '3107_combined(v, l, vle)_PT_1'
myModel = Model(file_pt, file_ph)
# We then create an instance of MAiNGO, the solver, and hand it the model.
myMAiNGO = maingopy.MAiNGO(myModel)

myMAiNGO.set_option("epsilonA", 1e-9)
myMAiNGO.set_option('epsilonR', 1e-4)

# We can have MAiNGO read a settings file:
# fileName = ""
# myMAiNGO.read_settings(fileName) # If fileName is empty, MAiNGO will attempt to open MAiNGOSettings.txt
myMAiNGO.set_log_file_name(".logs/my_log_file.log")
myMAiNGO.set_option("writeCsv", True)
myMAiNGO.set_iterations_csv_file_name(".logs/iterations.csv")
myMAiNGO.set_solution_and_statistics_csv_file_name(".logs/solution_and_statistics.csv")

# myMAiNGO.write_model_to_file_in_other_language(writingLanguage=maingopy.LANG_GAMS,
#                                                fileName="./logs/my_problem_file_MAiNGO.gms", solverName="SCIP",
#                                                writeRelaxationOnly=False)

# Finally, we call the solve routine to solve the problem.
maingoStatus = myMAiNGO.solve()
print(maingoStatus)

# Get numeric solution values
solution_vars = myMAiNGO.get_solution_point()
print("Global optimum of the surrogate model: f([{}]) = {}".format(
    solution_vars[0], myMAiNGO.get_objective_value()
))
print("Global optimum of the surrogate model: f([{}]) = {}".format(myMAiNGO.get_solution_point()[0],
                                                                       myMAiNGO.get_objective_value()))


# # === Evaluate at optimal solution to get A_CO2 ===
# outputs = myModel.flash_handler.evaluate_pt_flash(
#     np.array([solution_vars[0],  # T
#               1,                  # P (fixed here)
#               0.2425, 0, 1 - 0.2425, 0, 0, 0, 0, 0, 0, 0])  # same inlet spec as in evaluate()
# )
# n_co2_vap = outputs[2]
# A_CO2 = n_co2_vap / 0.2425
# A_CO2_aq = 1 - A_CO2
#
# print(f"A_CO2 at optimum = {A_CO2_aq}")
