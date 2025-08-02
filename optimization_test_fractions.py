import sys
sys.path.append(r"C:\Users\caspe\maingo\maingo\build\Release")

import numpy as np
import maingopy
from get_min_max import *


# To define a model, we need to spcecialize the MAiNGOmodel class
class Model(maingopy.MAiNGOmodel):
    def __init__(self, file):
        maingopy.MAiNGOmodel.__init__(self)
        # Initialize feedforward neural network and load data from example csv file
        self.ffANN = maingopy.melonpy.FeedForwardNet()
        # folder where the model xml is stored
        self.path = "inputs/d6_trained_nn"
        # xml filename
        self.fileName = file
        self.min_values, self.max_values = get_min_max(file)
        print(self.min_values, self.max_values)
        # open them (define that it is an XML instead of a CSV)
        self.ffANN.load_model(self.path, f'{self.fileName}.xml', maingopy.melonpy.XML)

    # We need to implement the get_variables functions for specifying the optimization variables
    def get_variables(self):
        # define bounds of the original variables, so that it rescales the results of the optimization
        # the optimization is done with the normalized version of these values
        # variables = [maingopy.OptimizationVariable(maingopy.Bounds(300, 473), maingopy.VT_CONTINUOUS, "T"),
        #              maingopy.OptimizationVariable(maingopy.Bounds(30, 200), maingopy.VT_CONTINUOUS, "p")]
        variables = [maingopy.OptimizationVariable(maingopy.Bounds(333, 473), maingopy.VT_CONTINUOUS, "T")]
        return variables

    # We need to implement the evaluate function that computes the values of the objective and constraints from the
    # variables. Note that the variables in the 'vars' argument of this function do correspond to the optimization
    # variables defined in the get_variables function. However, they are different objects for technical reasons.
    # The only mapping we have between them is the position in the list.
    # The results of the evaluation (i.e., objective and constraint values) need to be return in an EvaluationContainer
    def evaluate(self, vars):
        t = vars[0]
        p = 127.75

        n_co2 = 0.2425
        n_h2o = 1 - n_co2
        n_n2 = 0
        n_naoh = 0

        t_scaled = self.scale_input(t, 'T')
        p_scaled = self.scale_input(p, 'P')
        n_co2_scaled = self.scale_input(n_co2, 'CO2(g)_in')
        n_h2o_scaled = self.scale_input(n_h2o, 'H2O(aq)_in')
        n_n2_scaled = self.scale_input(n_n2, 'N2(g)_in')
        n_naoh_scaled = self.scale_input(n_naoh, 'NaOH(aq)_in')

        # Inputs to the Flash ANN
        ann_inputs = [t_scaled, p_scaled, n_co2_scaled, n_n2_scaled, n_h2o_scaled, n_naoh_scaled]
        ann_outputs = self.evaluate_pt_flash(ann_inputs)

        y_h2o_scaled = ann_outputs[0]
        x_co2_scaled = ann_outputs[1]
        x_n2_scaled = ann_outputs[2]
        v_frac_scaled = ann_outputs[3]
        enthalpy_scaled = ann_outputs[4]

        y_h2o = self.inverse_scale_input(y_h2o_scaled, 'Y_H2O')
        x_ = self.inverse_scale_input(x_co2_scaled, 'X_CO2')
        a_n2 = self.inverse_scale_input(x_n2_scaled, 'X_N2')

        enthalpy = self.inverse_scale_input(enthalpy_scaled, 'enthalpy')

        # the result
        result = maingopy.EvaluationContainer()
        # constraints
        # add equalities with result.eq = [equation]
        # add inequalities with result.ineq = [equation]
        # scaling between [-1, 1]
        # x_scaled = 2 * (x - x_min) / (x_max - x_min) - 1
        # x = 0.5 * (x_scaled + 1) * (x_max - x_min) + x_min
        result.objective = a_co2
        return result

    def scale_input(self, unscaled, name):
        return 2 * (unscaled - self.min_values[name]) / (self.max_values[name] - self.min_values[name]) - 1

    def inverse_scale_input(self, scaled, name):
        return 0.5 * (scaled + 1) * (self.max_values[name] - self.min_values[name]) + self.min_values[name]

    def evaluate_pt_flash(self, ann_inputs):
        # Evaluate the network (in reduced-space)
        ann_outputs = self.ffANN.calculate_prediction_reduced_space(ann_inputs)
        # ann_outputs: ['A_CO2', 'A_H2O', 'A_N2', 'enthalpy']
        return ann_outputs


# To work with the problem, we first create an instance of the model.
file = 'FINAL_LP_HH_VLP(v, l, vle)_PT_1'
myModel = Model(file)
# We then create an instance of MAiNGO, the solver, and hand it the model.
myMAiNGO = maingopy.MAiNGO(myModel)

# We can have MAiNGO read a settings file:
#fileName = ""
#myMAiNGO.read_settings(fileName) # If fileName is empty, MAiNGO will attempt to open MAiNGOSettings.txt
myMAiNGO.set_log_file_name(".logs/my_log_file.log")
myMAiNGO.set_option("writeCsv", True)
myMAiNGO.set_iterations_csv_file_name(".logs/iterations.csv")
myMAiNGO.set_solution_and_statistics_csv_file_name(".logs/solution_and_statistics.csv")

myMAiNGO.write_model_to_file_in_other_language(writingLanguage=maingopy.LANG_GAMS, fileName="./logs/my_problem_file_MAiNGO.gms", solverName="SCIP", writeRelaxationOnly=False)


# Finally, we call the solve routine to solve the problem.
maingoStatus = myMAiNGO.solve()
print(maingoStatus)

print("Global optimum of the surrogate model: f([{}, {}]) = {}".format(myMAiNGO.get_solution_point()[0], myMAiNGO.get_solution_point()[1], myMAiNGO.get_objective_value()))
