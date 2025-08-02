from unit_handler import *


class EvaluateProcess:
    def __init__(self, model):
        self.unit_handler = UnitHandler(model)

    def equations(self, process_inputs, optimization_variables, p):
        tear_stream = optimization_variables[1:]
        t_out_mixer = optimization_variables[0]
        co2_in = process_inputs[0]
        sla_in = process_inputs[1]
        t_reactor, p_reactor, t_flash, p_flash = p[0], p[1], p[2], p[3]
        # calculate inputs once to get enthalpies
        co2_in = self.unit_handler.flash_handler.evaluate_pt_flash(co2_in)
        sla_in = self.unit_handler.flash_handler.evaluate_pt_flash(sla_in)
        output_mixer, eq_mixer = self.unit_handler.evaluate_mixer([sla_in], t_out_mixer)
        output_pump = self.unit_handler.evaluate_pump([output_mixer], p_reactor)
        output_heater, q_heater = self.unit_handler.evaluate_heater([output_pump], t_reactor)
        output_reactor, q_heater = self.unit_handler.evaluate_reactor([output_heater, co2_in], t_reactor)
        g_out_flash, l_out_flash = self.unit_handler.evaluate_flash([output_reactor], t_flash, p_flash)
        l_out_filter, s_out_filter = self.unit_handler.evaluate_filter([l_out_flash])
        molar_balance = tear_stream - l_out_filter
        eq_constraints = [eq_mixer]
        objective = sum(molar_balance)**2
        return eq_constraints, objective

