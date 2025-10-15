from d2_pilot_plant_V2.d2_process import *
import time
import os
from pathlib import Path
import pandas as pd


def get_solution_vars():
    stream_vars = [421,  # lr1_co2
                   23663,  # lr1_h2o
                   430.15,  # lr1_naoh
                   21.18,  # lr1_magnesite
                   0.55,  # lr1_forsterite
                   1.92,  # lr1_fayalite
                   10.59,  # lr1_amorphous_silica
                   1058,  # vr1_co2
                   126,  # vr1_h2o
                   295,  # c2_co2
                   59]  # c2_h2o
    unit_temps = [64,  # t_c101
                  62,  # t_c101_isen
                  167,  # t_va101
                  39,  # t_m102
                  44,  # t_p102
                  151,  # t_he101_cold
                  424,  # t_c102
                  390,  # t_c102_isen
                  360,  # t_c103
                  330,  # t_c103_isen
                  436,  # t_c104
                  400]  # t_c104_isen   # 330 would be way closer, 392 is reaktoro solution

    design_vars = [3102,  # h2o_in
                   53.165,  # NaOH in
                   2337,  # CO2 in
                   0.89]  # Liquid split

    unit_pressures = [50,  # p v102
                      25]  # p v103

    for idx, value in enumerate(unit_temps):
        unit_temps[idx] = value + 273.15
    solution_vars = stream_vars + unit_temps + design_vars + unit_pressures
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
        self.parameters = None

    # We need to implement the get_variables functions for specifying the optimization variables
    def get_variables(self):
        # scale bounds around a nominal solution point
        s = get_solution_vars()
        lb, ub = 0.5, 1.5

        names = [
            # Tear streams (0–10)
            "CO2_LR1", "H2O_LR1", "NaOH_LR1", "Magnesite_LR1", "Forsterite_LR1", "Fayalite_LR1", "Amorphous_Silica_LR1",
            "CO2_VR1", "H2O_VR1", "CO2_C2", "H2O_C2",
            # Unit variables (11–22)
            "T_C101", "T_C101_ISEN", "T_VA101", "T_M102", "T_P102", "T_HE101_COLD",
            "T_C102", "T_C102_ISEN", "T_C103", "T_C103_ISEN", "T_C104", "T_C104_ISEN",
            # Design specs (23–26)
            "H2O in", "NaOH in", "CO2 in",
        ]

        variables = [maingopy.OptimizationVariable(maingopy.Bounds(s[i] * lb, s[i] * ub), maingopy.VT_CONTINUOUS,
                                                   names[i]) for i in range(len(names))]

        # # widen bounds for unit variables (11–22): all T_* entries
        # for idx in range(11, 23):  # 11..22 inclusive
        #     variables[idx] = maingopy.OptimizationVariable(
        #         maingopy.Bounds(293, 730),
        #         maingopy.VT_CONTINUOUS,
        #         names[idx]
        #     )

        variables.append(maingopy.OptimizationVariable(maingopy.Bounds(0.8, 0.95), maingopy.VT_CONTINUOUS, "Liquid Split"))
        variables.append(maingopy.OptimizationVariable(maingopy.Bounds(45, 55), maingopy.VT_CONTINUOUS, "P_V102"))
        variables.append(maingopy.OptimizationVariable(maingopy.Bounds(24, 26), maingopy.VT_CONTINUOUS, "P_V103"))

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
        sold_liquid[IDX['Forsterite']] = 1103.11
        sold_liquid[IDX['Fayalite']] = 190.407

        proccess_inputs = [np.array(co2_in), np.array(sold_liquid)]

        # if not in evaluation mode, the process.equations will return all the equations that define the process
        if self.get_equations:
            self.process.equations(proccess_inputs, vars, self.parameters)
            # the result
            result = maingopy.EvaluationContainer()
            # constraints
            # add equalities with result.eq = [equation]
            result.eq = self.equalities
            # add inequalities with result.ineq = [equation]
            result.ineq = self.inequalities
            # result.objective = self.cost_objective()
            return result

        # just evaluate the model, no optimization
        else:
            outputs = self.process.equations(proccess_inputs, self.optimal_vars, self.parameters)
            return outputs

    def get_power(self, m_product):
        p_data = {}
        total_power = 0
        # compressor costs
        comps = ['C-101', 'C-102', 'C-103', 'C-104']
        pumps = ['P-102']
        q_cool = ['H-101', 'R-101']
        q_heat = ['H-102']
        for name in comps + pumps + q_cool + q_heat:
            p = self.unit_power_duties[name] / 1000 / 3600
            q = self.unit_heat_duties[name] / 1000 / 3600

            if name in comps:
                power = p * COMPRESSOR_FACTOR
            elif name in pumps:
                power = p * PUMP_FACTOR
            elif name in q_cool:
                power = -1 * q * COOL_FACTOR
            elif name in q_heat:
                power = q * HEAT_FACTOR
            else:
                raise Exception('')
            p_data[f'P_{name}[kWh/tonne]'] = power / m_product * 1000
            total_power += power  # in kW
        p_data['P_Total[kWh/tonne]'] = total_power / m_product * 1000
        return total_power, p_data

    def objective_function(self, stream_values):
        co2_input = stream_values['V-1'][IDX['CO2']] * MOLAR_MASS['CO2']
        h2o_input = stream_values['SLURRY'][IDX['H2O']] * MOLAR_MASS['H2O']
        naoh_input = stream_values['SLURRY'][IDX['H2O']] * MOLAR_MASS['NaOH']

        forsterite_in = stream_values['SLURRY'][IDX['Forsterite']] * MOLAR_MASS['Forsterite']
        fayalite_in = stream_values['SLURRY'][IDX['Fayalite']] * MOLAR_MASS['Fayalite']

        forsterite_out = stream_values['PRODUCT'][IDX['Forsterite']] * MOLAR_MASS['Forsterite']
        fayalite_out = stream_values['PRODUCT'][IDX['Fayalite']] * MOLAR_MASS['Fayalite']
        magnesite_out = stream_values['PRODUCT'][IDX['Magnesite']] * MOLAR_MASS['Magnesite']
        silica_out = stream_values['PRODUCT'][IDX['Amorphous_Silica']] * MOLAR_MASS['Amorphous_Silica']

        m_co2 = co2_input
        m_h2o = h2o_input
        m_naoh = naoh_input
        m_olivine = forsterite_in + fayalite_in
        m_product = forsterite_out + fayalite_out + magnesite_out + silica_out

        power, power_data = self.get_power(m_product)

        c_elec = power * PRICES['Electricity']  # power in kW, price in euro / kWh --> cost in euro / hr
        c_co2 = m_co2 * PRICES['CO2'] / 1000  # m_co2 in kg / hr, price in euro / tonne --> cost in euro / hr
        c_h2o = m_h2o * PRICES['H2O'] / 1000  # m_h2o in kg / hr, price in euro / tonne --> cost in euro / hr
        c_naoh = m_naoh * PRICES['NaOH'] / 1000  # m_naoh in kg / hr, price in euro / tonne --> cost in euro / hr
        c_olivine = m_olivine * PRICES[
            'Olivine'] / 1000  # m_olivine in kg / hr, price in euro / tonne --> cost in euro / hr
        c_total = c_elec + c_co2 + c_h2o + c_naoh + c_olivine
        scaled_cost = c_total / m_product * 1000  # (euro / hr) / (kg / hr) * 1000 kg/tonne = euro/tonne

        cost_data = {
            'c_CO2 [euro/tonne]': c_co2 / m_product * 1000,
            'c_H2O [euro/tonne]': c_h2o / m_product * 1000,
            'c_NaOH [euro/tonne]': c_naoh / m_product * 1000,
            'c_Olivine [euro/tonne]': c_olivine / m_product * 1000,
            'c_Electricity [euro/tonne]': c_elec / m_product * 1000,
            'c_Total [euro/tonne]': scaled_cost,
        }

        return scaled_cost, power_data, cost_data


class ModelHandler:
    def __init__(self):
        self.myModel = None
        self.myMAiNGO = None
        self.initialise_model()

    def initialise_model(self):
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

        parameters = [
            170 + 273.15,  # t_r101
            100,  # p_r101
            60 + 273.15,  # t_v101
            95,  # p_v101
            40 + 273.15,  # t_filter
            1,  # p_filter
            60 + 273.15,  # t_co2_tank
            95,  # p_co2_tank
            50,  # p V102
            25,  # p V103
            1,  # p V104
            70 + 273.15  # T_HE1_hot_out
        ]
        myModel.parameters = parameters
        self.myModel = myModel
        self.myMAiNGO = myMAiNGO

    def run_optimization(self):
        # Finally, we call the solve routine to solve the problem.
        maingoStatus = self.myMAiNGO.solve()
        print(maingoStatus)

        # Get numeric solution values
        solution_vars = self.myMAiNGO.get_solution_point()
        return solution_vars

    def run(self, run_opt):
        if run_opt:
            solution_vars = self.run_optimization()
        else:
            # this will just return the predefined solution vars
            solution_vars = get_solution_vars()
        return solution_vars

    def evaluate_model(self, solution_vars):
        # evaluate model
        self.myModel.get_equations = False
        self.myModel.optimal_vars = solution_vars
        tear_stream_errors, stream_outputs = self.myModel.evaluate(solution_vars)
        return tear_stream_errors, stream_outputs

    def print_solution(self, tear_stream_errors, stream_values):

        def to_celsius(t):
            return t - 273.15

        for specie, error in tear_stream_errors.items():
            print(specie, error)

        # nicely display the output
        for name, stream in stream_values.items():
            print(f"{'=' * 60}")
            print(f"{name.upper()}")
            print(f"{'-' * 60}")
            for label, value in zip(NAMES, stream):
                v = float(value)
                if label == "T":
                    print(f"{label:<20} {to_celsius(v):>12.2f}")
                else:
                    print(f"{label:<20} {v:>12.6g}")

        scaled_cost, power_data, cost_data = self.myModel.objective_function(stream_values)

        for unit, power in power_data.items():
            print(f'{unit}: power: {power}[kWh/tonne]')

    def run_sensitivity_analysis(self, name):
        file_path = Path(rf"C:\Users\caspe\PycharmProjects\MA_CJVW_Optimization\outputs\sensitivity_outputs\{name}.csv")
        if os.path.exists(file_path):
            raise Exception('Choose different name for sensitivity analysis')

        def function(p_v102, p_v103):
            self.initialise_model()
            parameters = [
                170 + 273.15,  # t_r101
                100,  # p_r101
                60 + 273.15,  # t_v101
                95,  # p_v101
                40 + 273.15,  # t_filter
                1,  # p_filter
                60 + 273.15,  # t_co2_tank
                95,  # p_co2_tank
                p_v102,  # p V102
                p_v103,  # p V103
                1,  # p V104
                70 + 273.15  # T_HE1_hot_out
            ]
            self.myModel.parameters = parameters
            solution_vars = self.run(run_opt=True)
            _, stream_values = self.evaluate_model(solution_vars)
            scaled_cost, power_data, cost_data = self.myModel.objective_function(stream_values)
            return power_data, cost_data

        sensitivity_rows = []
        for p_v103_v104_ratio in [5, 10, 15, 20, 25]:
            for p_v102_v103_ratio in [2, 3, 4, 5, 6]:
                p_v103 = p_v103_v104_ratio
                p_v102 = p_v103 * p_v102_v103_ratio
                if p_v102 < 100:
                    p_data, c_data = function(p_v102=p_v102, p_v103=p_v103)
                    row = {
                        'p_V-102 [bar]': p_v102,
                        'p_V-103 [bar]': p_v103,
                        **p_data,  # e.g. P_*[kW], P_Total[kW]
                        **c_data  # e.g. c_* [€], c_Total_scaled [€]
                    }
                    sensitivity_rows.append(row)
        sensitivity_data = pd.DataFrame(sensitivity_rows)
        sensitivity_data.to_csv(file_path, index=False)

    def run_optimization_of_cost_function(self):
        return


if __name__ == '__main__':
    start_time = time.time()
    model_handler = ModelHandler()

    # run this for a simple model validation with predefined solution variables
    stream_errors, stream_outputs = model_handler.evaluate_model(model_handler.run(run_opt=True))
    model_handler.print_solution(stream_errors, stream_outputs)

    # run this for sensitivity analysis of cost function vs p_v102, p_v103
    # model_handler.run_sensitivity_analysis(name='test')

    # run this for optimization of p_v102 and p_v103 to get minimal of cost function
    # model_handler.run_optimization_of_cost_function()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time} seconds")
