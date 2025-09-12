from simple_demo_plant.process import *


# To define a model, we need to spcecialize the MAiNGOmodel class
class Model(maingopy.MAiNGOmodel):
    def __init__(self):
        maingopy.MAiNGOmodel.__init__(self)
        self.get_equations = True
        # Initialize feedforward neural network and load data from example csv file
        self.process = EvaluateProcess(model=self)

    # We need to implement the get_variables functions for specifying the optimization variables
    def get_variables(self):
        # define bounds of the original variables, so that it rescales the results of the optimization
        # the optimization is done with the normalized version of these values
        unit_variables = [
            maingopy.OptimizationVariable(maingopy.Bounds(300, 370), maingopy.VT_CONTINUOUS, "T_SL1"),
            maingopy.OptimizationVariable(maingopy.Bounds(300, 500), maingopy.VT_CONTINUOUS, "T_SL2"),
            maingopy.OptimizationVariable(maingopy.Bounds(300, 500), maingopy.VT_CONTINUOUS, "T_SL3"),
            maingopy.OptimizationVariable(maingopy.Bounds(330, 370), maingopy.VT_CONTINUOUS, "T_P4"),

        ]

        tear_stream_vars = [
            maingopy.OptimizationVariable(maingopy.Bounds(1e-2, 100), maingopy.VT_CONTINUOUS, "CO2"),
            maingopy.OptimizationVariable(maingopy.Bounds(100, 1000), maingopy.VT_CONTINUOUS, "H2O"),
            maingopy.OptimizationVariable(maingopy.Bounds(1e-2, 100), maingopy.VT_CONTINUOUS, "NaOH"),
        ]

        variables = unit_variables + tear_stream_vars
        return variables

    # We need to implement the evaluate function that computes the values of the objective and constraints from the
    # variables. Note that the variables in the 'vars' argument of this function do correspond to the optimization
    # variables defined in the get_variables function. However, they are different objects for technical reasons.
    # The only mapping we have between them is the position in the list.
    # The results of the evaluation (i.e., objective and constraint values) need to be return in an EvaluationContainer
    def evaluate(self, vars):
        # Define Constant inputs
        co2_in = [0] * len(NAMES)
        co2_in[IDX['T']] = 60 + 273.15
        co2_in[IDX['P']] = 100
        co2_in[IDX['CO2_vap']] = 31

        sold_liquid = [0] * len(NAMES)
        sold_liquid[IDX['T']] = 30 + 273.15
        sold_liquid[IDX['P']] = 1
        sold_liquid[IDX['H2O_aq']] = 60
        sold_liquid[IDX['NaOH_aq']] = 1
        sold_liquid[IDX['Forsterite']] = 15
        sold_liquid[IDX['Fayalite']] = 10

        proccess_inputs = [np.array(co2_in), np.array(sold_liquid)]

        parameters = [
            170 + 273.15,  # t_reactor
            100,  # p_reactor
            70 + 273.15,  # t_flash
            1,  # p_flash
            69.218 + 273.15,  # t_filter
            1  # p_tearstream
        ]

        # if not in evaluation mode, the process.equations will return all the equations that define the process
        if self.get_equations:
            eq_constraints, ineq_constraints, objective = self.process.equations(proccess_inputs, vars, parameters)

            # the result
            result = maingopy.EvaluationContainer()
            # constraints
            # add equalities with result.eq = [equation]
            result.eq = eq_constraints
            # add inequalities with result.ineq = [equation]
            result.ineq = eq_constraints
            result.objective = objective
            return result

        # just evaluate the model, no optimization
        else:
            outputs = self.process.equations(proccess_inputs, self.optimal_vars, parameters)
            return outputs


# To work with the problem, we first create an instance of the model.
myModel = Model()
# We then create an instance of MAiNGO, the solver, and hand it the model.
myMAiNGO = maingopy.MAiNGO(myModel)

myMAiNGO.set_option("epsilonA", 1e-2)
myMAiNGO.set_option('epsilonR', 1e-2)
myMAiNGO.set_option('deltaEq', 1e-2)  # when equality constraint is met

# We can have MAiNGO read a settings file:
# fileName = ""
# myMAiNGO.read_settings(fileName) # If fileName is empty, MAiNGO will attempt to open MAiNGOSettings.txt
myMAiNGO.set_log_file_name(".logs/my_log_file.log")
myMAiNGO.set_option("writeCsv", True)
myMAiNGO.set_iterations_csv_file_name(".logs/iterations.csv")
myMAiNGO.set_solution_and_statistics_csv_file_name(".logs/solution_and_statistics.csv")

# Finally, we call the solve routine to solve the problem.
maingoStatus = myMAiNGO.solve()
print(maingoStatus)

# Get numeric solution values
solution_vars = myMAiNGO.get_solution_point()
print("Global optimum of the surrogate model: f([{}, {}]) = {}".format(
    solution_vars[0], solution_vars[1], myMAiNGO.get_objective_value(),
))

# evaluate model

# ========================
# Post-Optimization Evaluation
# ========================
myModel.get_equations = False
myModel.optimal_vars = solution_vars
process_outputs, eq_m102, eq_he101 = myModel.evaluate(solution_vars)


def to_celsius(t):
    return t - 273.15


# nicely display the output
for name, stream in process_outputs.items():
    print(f"{'='*60}")
    print(f"{name.upper()}")
    print(f"{'-'*60}")
    for label, value in zip(NAMES, stream):
        v = float(value)
        if label == "T":
            print(f"{label:<20} {to_celsius(v):>12.2f}")
        else:
            print(f"{label:<20} {v:>12.6g}")

print('Enthalpy balance', eq_m102)
