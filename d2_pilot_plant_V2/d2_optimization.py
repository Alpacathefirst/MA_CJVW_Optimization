from d2_pilot_plant_V2.d2_process import *
import time


def get_solution_vars():
    stream_vars = [434,  # lr1_co2
                   25138,  # lr1_h2o
                   442,  # lr1_naoh
                   21.18,  # lr1_magnesite
                   0.55,  # lr1_forsterite
                   1.92,  # lr1_fayalite
                   10.59,  # lr1_amorphous_silica
                   1051,  # vr1_co2
                   125,  # vr1_h2o
                   311,  # c2_co2
                   62]  # c2_h2o
    unit_vars = [64,  # t_c101
                 62,  # t_c101_isen
                 167,  # t_va101
                 26.72,  # t_m102
                 26.97,  # t_p102
                 134,  # t_he101_cold
                 376,  # t_c102
                 371,  # t_c102_isen
                 340,  # t_c103
                 336,  # t_c103_isen
                 413,  # t_c104
                 320]  # t_c104_isen   # 330 would be way closer, 392 is reaktoro solution

    design_vars = [2968,  # h2o_in
                   49.188,  # NaOH in
                   2537.998,  # CO2 in
                   0.9]  # Liquid split

    for idx, value in enumerate(unit_vars):
        unit_vars[idx] = value + 273.15
    solution_vars = stream_vars + unit_vars + design_vars
    return solution_vars


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
        # scale bounds around a nominal solution point
        s = get_solution_vars()
        lb, ub = 0.8, 1.2

        names = [
            # Tear streams (0–10)
            "CO2_LR1", "H2O_LR1", "NaOH_LR1", "Magnesite_LR1", "Forsterite_LR1", "Fayalite_LR1", "Amorphous_Silica_LR1",
            "CO2_VR1", "H2O_VR1", "CO2_C2", "H2O_C2",
            # Unit variables (11–22)
            "T_C101", "T_C101_ISEN", "T_VA101", "T_M102", "T_P102", "T_HE101_COLD",
            "T_C102", "T_C102_ISEN", "T_C103", "T_C103_ISEN", "T_C104", "T_C104_ISEN",
            # Design specs (23–26)
            "H2O in", "NaOH in", "CO2 in", "Liquid Split"
        ]

        variables = [maingopy.OptimizationVariable(maingopy.Bounds(s[i] * lb, s[i] * ub), maingopy.VT_CONTINUOUS,
                                                   names[i]) for i in range(len(names))]
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
        co2_in[IDX['CO2']] = vars[25]

        sold_liquid = [0] * len(NAMES)
        sold_liquid[IDX['T']] = 30 + 273.15
        sold_liquid[IDX['P']] = 1
        sold_liquid[IDX['H2O']] = vars[23]
        sold_liquid[IDX['NaOH']] = vars[24]
        sold_liquid[IDX['Forsterite']] = 1103.111
        sold_liquid[IDX['Fayalite']] = 190.407

        proccess_inputs = [np.array(co2_in), np.array(sold_liquid)]

        parameters = [
            170 + 273.15,  # t_r101
            100,  # p_r101
            60 + 273.15,  # t_v101
            95,  # p_v101
            25 + 273.15,  # t_filter
            1,  # p_filter
            60 + 273.15,  # t_co2_tank
            95,  # p_co2_tank
            50,  # p V102
            25,  # p V103
            1,  # p V104
            70 + 273.15  # T_HE1_hot_out
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
        solution_vars = get_solution_vars()
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
        print(f"{'=' * 60}")
        print(f"{name.upper()}")
        print(f"{'-' * 60}")
        for label, value in zip(NAMES, stream):
            v = float(value)
            if label == "T":
                print(f"{label:<20} {to_celsius(v):>12.2f}")
            else:
                print(f"{label:<20} {v:>12.6g}")
    for unit in ['P-102', 'C-101', 'C-102', 'C-103', 'C-104', 'H-102', 'H-101', 'R-101']:
        print(f'{unit}: power: {myModel.unit_power_duties[unit]/1000}kJ Q: {myModel.unit_heat_duties[unit]/1000}kJ')


if __name__ == '__main__':
    start_time = time.time()
    run(run_opt=True)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time} seconds")
