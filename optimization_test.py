from process import *


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
            maingopy.OptimizationVariable(maingopy.Bounds(300, 400), maingopy.VT_CONTINUOUS, "T_Mixer"),
        ]
        tear_stream_vars = [
            maingopy.OptimizationVariable(maingopy.Bounds(100, 500), maingopy.VT_CONTINUOUS, "CO2"),
            maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 2), maingopy.VT_CONTINUOUS, "N2"),
            maingopy.OptimizationVariable(maingopy.Bounds(10000, 20000), maingopy.VT_CONTINUOUS, "H2O"),
            maingopy.OptimizationVariable(maingopy.Bounds(100, 500), maingopy.VT_CONTINUOUS, "NaOH"),
            # maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 1e5), maingopy.VT_CONTINUOUS, "CO2_vap"),
            # maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 1e5), maingopy.VT_CONTINUOUS, "N2_vap"),
            # maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 1e5), maingopy.VT_CONTINUOUS, "H2O_vap"),
            # maingopy.OptimizationVariable(maingopy.Bounds(-1e9, 1e9), maingopy.VT_CONTINUOUS, "enthalpy_vap"),
            # maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 1e5), maingopy.VT_CONTINUOUS, "CO2_aq"),
            # maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 1e5), maingopy.VT_CONTINUOUS, "N2_aq"),
            # maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 1e5), maingopy.VT_CONTINUOUS, "H2O_aq"),
            # maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 1e5), maingopy.VT_CONTINUOUS, "NaOH_aq"),
            # maingopy.OptimizationVariable(maingopy.Bounds(-1e9, 1e9), maingopy.VT_CONTINUOUS, "enthalpy_aq"),
            # maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 1e5), maingopy.VT_CONTINUOUS, "Magnesite"),
            # maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 1e5), maingopy.VT_CONTINUOUS, "Forsterite"),
            # maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 1e5), maingopy.VT_CONTINUOUS, "Fayalite"),
            # maingopy.OptimizationVariable(maingopy.Bounds(1e-16, 1e5), maingopy.VT_CONTINUOUS, "Amorphous_Silica"),
            # maingopy.OptimizationVariable(maingopy.Bounds(-1e9, 1e9), maingopy.VT_CONTINUOUS, "enthalpy_s"),
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
        co2_in = np.array([
            60 + 273.15,  # T
            100,  # P
            50,  # CO2_vap
            0.01,  # N2_vap
            0,  # H2O_vap
            0,  # enthalpy_vap
            0,  # CO2_aq
            0,  # N2_aq
            0,  # H2O_aq
            0,  # NaOH_aq
            0,  # enthalpy_aq
            0,  # Magnesite
            0,  # Forsterite
            0,  # Fayalite
            0,  # Amorphous_Silica
            0  # enthalpy_s
        ])

        sla_in = np.array([
            30 + 273.15,  # T
            1,  # P
            0,  # CO2_vap
            0,  # N2_vap
            0,  # H2O_vap
            0,  # enthalpy_vap
            0,  # CO2_aq
            0,  # N2_aq
            100,  # H2O_aq
            1,  # NaOH_aq
            0,  # enthalpy_aq
            0,  # Magnesite
            10,  # Forsterite
            5,  # Fayalite
            0,  # Amorphous_Silica
            0  # enthalpy_s
        ])
        proccess_inputs = [co2_in, sla_in]
        # t_reactor, p_reactor, t_flash, p_flash
        parameters = [
            170 + 273.15,  # t_reactor
            100,  # p_reactor
            170 + 273.15,  # t_flash
            20  # p_flash
        ]

        # if not in evaluation mode, the process.equations will return all the equations that define the process
        if self.get_equations:
            eq_constraints, objective = self.process.equations(proccess_inputs, vars, parameters, self.get_equations)

            # the result
            result = maingopy.EvaluationContainer()
            # constraints
            # add equalities with result.eq = [equation]
            result.eq = eq_constraints
            # add inequalities with result.ineq = [equation]
            result.objective = objective
            return result

        # just evaluate the model, no optimization
        else:
            outputs = self.process.equations(proccess_inputs, self.optimal_vars, parameters, self.get_equations)
            return outputs


# To work with the problem, we first create an instance of the model.
myModel = Model()
# We then create an instance of MAiNGO, the solver, and hand it the model.
myMAiNGO = maingopy.MAiNGO(myModel)

myMAiNGO.set_option("epsilonA", 1e-3)
myMAiNGO.set_option('epsilonR', 1e-2)
myMAiNGO.set_option('deltaEq', 1e-2)  # when equality constraint is met

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
print("Global optimum of the surrogate model: f([{}, {}]) = {}".format(
    solution_vars[0],solution_vars[1], myMAiNGO.get_objective_value(),
))

# evaluate model

# ========================
# Post-Optimization Evaluation (Pure Numeric)
# ========================
myModel.get_equations = False
myModel.optimal_vars = solution_vars
process_outputs, eq_mixer = myModel.evaluate(solution_vars)

# nicely display the output
stream_labels = [
    "T [K]", "P [bar]",
    "CO2_vap", "N2_vap", "H2O_vap", "enthalpy_vap",
    "CO2_aq", "N2_aq", "H2O_aq", "NaOH_aq", "enthalpy_aq",
    "Magnesite", "Forsterite", "Fayalite", "Amorphous_Silica", "enthalpy_s"
]

for name, stream in process_outputs.items():
    print(f"{'='*60}")
    print(f"{name.upper()}")
    print(f"{'-'*60}")
    for label, value in zip(stream_labels, stream):
        val = float(value)
        print(f"{label:<20} {val:>15.6g}")

print('Enthalpy balance', eq_mixer)
