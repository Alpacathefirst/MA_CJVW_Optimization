from d1_demo_plant.d1_process import *
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
            maingopy.OptimizationVariable(maingopy.Bounds(400, 500), maingopy.VT_CONTINUOUS, "CO2_LR1"),  # 0
            maingopy.OptimizationVariable(maingopy.Bounds(2.2e4, 2.6e4), maingopy.VT_CONTINUOUS, "H2O_LR1"),  # 1
            maingopy.OptimizationVariable(maingopy.Bounds(420, 450), maingopy.VT_CONTINUOUS, "NaOH_LR1"),  # 2
            maingopy.OptimizationVariable(maingopy.Bounds(18, 25), maingopy.VT_CONTINUOUS, "Magnesite_LR1"),  # 3
            maingopy.OptimizationVariable(maingopy.Bounds(0.4, 0.6), maingopy.VT_CONTINUOUS, "Forsterite_LR1"),  # 4
            maingopy.OptimizationVariable(maingopy.Bounds(1.5, 2.5), maingopy.VT_CONTINUOUS, "Fayalite_LR1"),  # 5
            maingopy.OptimizationVariable(maingopy.Bounds(9, 13), maingopy.VT_CONTINUOUS, "Amorphous_Silica_LR1"),  # 6
            # V-R4 tear stream
            maingopy.OptimizationVariable(maingopy.Bounds(700, 900), maingopy.VT_CONTINUOUS, "CO2_VR4"),  # 7
            maingopy.OptimizationVariable(maingopy.Bounds(3, 6), maingopy.VT_CONTINUOUS, "H2O_VR4")  # 8
        ]

        unit_variables = [
            maingopy.OptimizationVariable(maingopy.Bounds(300, 400), maingopy.VT_CONTINUOUS, "T_C101"),  # 9
            maingopy.OptimizationVariable(maingopy.Bounds(300, 400), maingopy.VT_CONTINUOUS, "T_C101_ISENTROPIC"),  # 10
            maingopy.OptimizationVariable(maingopy.Bounds(400, 500), maingopy.VT_CONTINUOUS, "T_VA101"),  # 11
            maingopy.OptimizationVariable(maingopy.Bounds(290, 350), maingopy.VT_CONTINUOUS, "T_M102"),  # 12
            maingopy.OptimizationVariable(maingopy.Bounds(290, 350), maingopy.VT_CONTINUOUS, "T_P102"),  # 13
            maingopy.OptimizationVariable(maingopy.Bounds(300, 500), maingopy.VT_CONTINUOUS, "T_HE101_COLD")  # 14
        ]

        design_specs_variables = [
            maingopy.OptimizationVariable(maingopy.Bounds(2800, 3500), maingopy.VT_CONTINUOUS, "H2O in"),  # 15
            maingopy.OptimizationVariable(maingopy.Bounds(40, 60), maingopy.VT_CONTINUOUS, "NaOH in"),  # 16
            maingopy.OptimizationVariable(maingopy.Bounds(2500, 2900), maingopy.VT_CONTINUOUS, "CO2 in")  # 17
        ]
        variables = tear_stream_vars + unit_variables + design_specs_variables

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
        co2_in[IDX['CO2']] = vars[17]

        sold_liquid = [0] * len(NAMES)
        sold_liquid[IDX['T']] = 30 + 273.15
        sold_liquid[IDX['P']] = 1
        sold_liquid[IDX['H2O']] = vars[15]
        sold_liquid[IDX['NaOH']] = vars[16]
        sold_liquid[IDX['Forsterite']] = 1103.111
        sold_liquid[IDX['Fayalite']] = 190.407

        proccess_inputs = [np.array(co2_in), np.array(sold_liquid)]

        parameters = [
            170 + 273.15,  # t_r101
            100,  # p_r101
            68 + 273.15,  # t_v102
            1,  # p_v102
            40 + 273.15,  # t_filter
            1,  # p_tearstream
            60 + 273.15,  # t_co2_tank
            95  # p_co2_tank
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

myMAiNGO.set_option("epsilonA", 1e-4)
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
        stream_vars = [434.9259,  # lr1_co2
                       24880.82,  # lr1_h2o
                       442.6921,  # lr1_naoh
                       21.18,  # lr1_magnesite
                       0.55,  # lr1_forsterite
                       1.92,  # lr1_fayalite
                       10.59,  # lr1_amorphous_silica
                       825.59,  # vr4_co2
                       4.359869]  # vr4_h2o
        unit_vars = [64.26561,  # t_c101
                     62,  # t_c101_isen
                     167,  # t_va101
                     39.54,  # t_m102
                     39.54,  # t_p102
                     146]  # t_he_cold_out

        design_vars = [2968.905,  # h2o_in
                       49.188,  # NaOH in
                       2627.933]  # CO2 in

        for idx, value in enumerate(unit_vars):
            unit_vars[idx] = value + 273.15
        solution_vars = stream_vars + unit_vars + design_vars

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
