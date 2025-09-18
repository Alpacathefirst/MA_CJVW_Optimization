from d2_pilot_plant.d2_process import *
import time


# To define a model, we need to spcecialize the MAiNGOmodel class
class Model(maingopy.MAiNGOmodel):
    def __init__(self):
        maingopy.MAiNGOmodel.__init__(self)
        self.get_equations = True
        self.equalities = []
        self.inequalities = []
        self.unit_heat_duties = {}
        self.unit_power_duties = {}
        # Initialize feedforward neural network and load data from example csv file
        self.process = EvaluateProcess(model=self)

    # We need to implement the get_variables functions for specifying the optimization variables
    def get_variables(self):
        # define bounds of the original variables, so that it rescales the results of the optimization
        # the optimization is done with the normalized version of these values

        tear_stream_vars = [
            # L-R1 tear stream
            maingopy.OptimizationVariable(maingopy.Bounds(7, 10), maingopy.VT_CONTINUOUS, "CO2_LR1"),
            maingopy.OptimizationVariable(maingopy.Bounds(300, 400), maingopy.VT_CONTINUOUS, "H2O_LR1"),
            maingopy.OptimizationVariable(maingopy.Bounds(5, 12), maingopy.VT_CONTINUOUS, "NaOH_LR1"),
            maingopy.OptimizationVariable(maingopy.Bounds(1e-9, 1), maingopy.VT_CONTINUOUS, "Magnesite_LR1"),
            maingopy.OptimizationVariable(maingopy.Bounds(1e-9, 1), maingopy.VT_CONTINUOUS, "Forsterite_LR1"),
            maingopy.OptimizationVariable(maingopy.Bounds(1e-9, 1), maingopy.VT_CONTINUOUS, "Fayalite_LR1"),
            maingopy.OptimizationVariable(maingopy.Bounds(1e-9, 1), maingopy.VT_CONTINUOUS, "Amorphous_Silica_LR1"),
            # V-R4 tear stream
            maingopy.OptimizationVariable(maingopy.Bounds(130, 170), maingopy.VT_CONTINUOUS, "CO2_VR1"),
            maingopy.OptimizationVariable(maingopy.Bounds(10, 20), maingopy.VT_CONTINUOUS, "H2O_VR1"),
            # V-C2 tear_stream
            maingopy.OptimizationVariable(maingopy.Bounds(1, 10), maingopy.VT_CONTINUOUS, "CO2_C2"),
            maingopy.OptimizationVariable(maingopy.Bounds(1e-3, 4), maingopy.VT_CONTINUOUS, "H2O_C2")
        ]

        # [335.979, 335.15, 440.15, 300.84999999999997, 300.45, 403.15, 649.15, 644.15, 613.15, 609.15, 686.15, 656.15]

        unit_variables = [
            maingopy.OptimizationVariable(maingopy.Bounds(300, 400), maingopy.VT_CONTINUOUS, "T_C101"),
            maingopy.OptimizationVariable(maingopy.Bounds(300, 400), maingopy.VT_CONTINUOUS, "T_C101_ISEN"),
            maingopy.OptimizationVariable(maingopy.Bounds(400, 500), maingopy.VT_CONTINUOUS, "T_VA101"),
            maingopy.OptimizationVariable(maingopy.Bounds(283, 320), maingopy.VT_CONTINUOUS, "T_M102"),
            maingopy.OptimizationVariable(maingopy.Bounds(283, 320), maingopy.VT_CONTINUOUS, "T_P102"),
            maingopy.OptimizationVariable(maingopy.Bounds(350, 500), maingopy.VT_CONTINUOUS, "T_HE101_COLD"),
            maingopy.OptimizationVariable(maingopy.Bounds(500, 700), maingopy.VT_CONTINUOUS, "T_C102"),
            maingopy.OptimizationVariable(maingopy.Bounds(500, 700), maingopy.VT_CONTINUOUS, "T_C102_ISEN"),
            maingopy.OptimizationVariable(maingopy.Bounds(500, 700), maingopy.VT_CONTINUOUS, "T_C103"),
            maingopy.OptimizationVariable(maingopy.Bounds(500, 700), maingopy.VT_CONTINUOUS, "T_C103_ISEN"),
            maingopy.OptimizationVariable(maingopy.Bounds(500, 700), maingopy.VT_CONTINUOUS, "T_C104"),
            maingopy.OptimizationVariable(maingopy.Bounds(500, 700), maingopy.VT_CONTINUOUS, "T_C104_ISEN"),
        ]

        variables = tear_stream_vars + unit_variables
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
        co2_in[IDX['P']] = 95
        co2_in[IDX['CO2']] = 50

        sold_liquid = [0] * len(NAMES)
        sold_liquid[IDX['T']] = 30 + 273.15
        sold_liquid[IDX['P']] = 1
        sold_liquid[IDX['H2O']] = 60
        sold_liquid[IDX['NaOH']] = 1
        sold_liquid[IDX['Forsterite']] = 15
        sold_liquid[IDX['Fayalite']] = 10

        proccess_inputs = [np.array(co2_in), np.array(sold_liquid)]

        parameters = [
            170 + 273.15,  # t_r101
            100,  # p_r101
            60 + 273.15,  # t_v101
            95,  # p_v101
            25 + 273.15,  # t_filter
            1,  # p_filter
            60+273.15,  # t_co2_tank
            95,  # p_co2_tank
            50,  # p V102
            25,  # p V103
            1,  # p V104
            70+273.15  # T_HE1_hot_out
        ]

        # if not in evaluation mode, the process.equations will return all the equations that define the process
        if self.get_equations:
            objective = self.process.equations(proccess_inputs, vars, parameters)
            # the result
            result = maingopy.EvaluationContainer()
            # constraints
            # add equalities with result.eq = [equation]
            result.eq = self.equalities
            # add inequalities with result.ineq = [equation]
            # result.ineq = self.inequalities
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


def run_optimization():
    # Finally, we call the solve routine to solve the problem.
    maingoStatus = myMAiNGO.solve()
    print(maingoStatus)

    # Get numeric solution values
    solution_vars = myMAiNGO.get_solution_point()
    return solution_vars


def run(run_opt):
    if run_opt:
        solution_vars = run_optimization()
    else:
        stream_vars = [8.75, 381.9, 9, 0, 0, 0, 0, 147.7063, 17.49594, 4.585, 0.88597]
        unit_vars = [62.829,
                     62,
                     167,
                     27.7,
                     27.3,
                     130,
                     376,  # t_c102
                     371,  # t_c102_isen
                     340,  # t_c103
                     336,  # t_c103_isen
                     413,  # t_c104
                     320]  # t_c104_isen   # 330 would be way closer, 392 is reaktoro solution
        for idx, value in enumerate(unit_vars):
            unit_vars[idx] = value + 273.15
        print(unit_vars)
        solution_vars = stream_vars + unit_vars

    # evaluate model
    myModel.get_equations = False
    myModel.optimal_vars = solution_vars
    tear_stream_errors, stream_outputs = myModel.evaluate(solution_vars)

    def to_celsius(t):
        return t - 273.15

    for specie, error in tear_stream_errors.items():
        print(specie, error)

    # nicely display the output
    for name, stream in stream_outputs.items():
        print(f"{'='*60}")
        print(f"{name.upper()}")
        print(f"{'-'*60}")
        for label, value in zip(NAMES, stream):
            v = float(value)
            if label == "T":
                print(f"{label:<20} {to_celsius(v):>12.2f}")
            else:
                print(f"{label:<20} {v:>12.6g}")
    for unit, heatflow in myModel.unit_heat_duties.items():
        print(unit, heatflow)


if __name__ == '__main__':
    start_time = time.time()
    run(run_opt=True)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time} seconds")
