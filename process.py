from unit_handler import *


class EvaluateProcess:
    def __init__(self, model):
        self.model = model
        self.unit_handler = UnitHandler(model)

    def equations(self, process_inputs, optimization_variables, p):
        t_out_mixer = optimization_variables[0]
        tear_stream_simple = optimization_variables[2:]
        co2_in = process_inputs[0]
        sla_in = process_inputs[1]
        t_reactor, p_reactor, t_flash, p_flash, t_tear, p_tear = p[0], p[1], p[2], p[3], p[4], p[5]
        # calculate inputs once to get enthalpies
        tear_stream = self.unit_handler.complicate_tearstream(t_tear, p_tear, tear_stream_simple)
        tear_stream = self.unit_handler.flash_handler.evaluate_pt_flash(tear_stream)
        co2_in = self.unit_handler.flash_handler.get_enthalpy(co2_in)
        sla_in = self.unit_handler.flash_handler.get_enthalpy(sla_in)
        output_mixer, eq_mixer = self.unit_handler.evaluate_mixer([sla_in, tear_stream], t_out_mixer)
        output_pump = self.unit_handler.evaluate_pump([output_mixer], p_reactor)
        output_heater, q_heater = self.unit_handler.evaluate_heater([output_pump], t_reactor)
        output_reactor, q_heater = self.unit_handler.evaluate_reactor([output_heater, co2_in], t_reactor)
        g_out_flash, l_out_flash = self.unit_handler.evaluate_flash([output_reactor], t_flash, p_flash)
        l_out_filter, s_out_filter = self.unit_handler.evaluate_filter([l_out_flash], liquid_split=0.90, solid_split=1)
        output_tearstream = self.unit_handler.evaluate_change_pt(t_tear, p_tear, [l_out_filter])
        output_tearstream_simple = self.unit_handler.simplify_tearstream(output_tearstream)
        # if not evaluating, all these equations are returned plus equality constraints and objective
        if self.model.get_equations:
            eq_constraints = [eq_mixer]
            molar_balances_squared = []
            for index, specie in enumerate(output_tearstream_simple):
                molar_balance = (output_tearstream_simple[index] - tear_stream_simple[index]) / maingopy.pos(
                    output_tearstream_simple[index])
                molar_balances_squared.append(molar_balance ** 2)
            sum_molar_balances_squared = sum(np.array(molar_balances_squared))
            eq_constraints = eq_constraints
            # objective = ((g_out_flash[2] - 5)/5)**2 + sum_molar_balances_squared
            objective = sum_molar_balances_squared
            return eq_constraints, objective
        # when just evaluating, return all stream values
        else:
            output_dict = {
                'CO2 input': co2_in,
                'Solid, liquid, additives in': sla_in,
                'tear stream': tear_stream,
                'Output mixer': output_mixer,
                'Output pump': output_pump,
                'Output heater': output_heater,
                'Output reactor': output_reactor,
                'Gas out flash': g_out_flash,
                'Liquid out flash': l_out_flash,
                'Liquid out filter': l_out_filter,
                'Solid out filter': s_out_filter,
                'Output tearstream': output_tearstream,
                'Error tearstream': np.where(tear_stream != 0, (output_tearstream - tear_stream) / tear_stream, 0),
            }
            return output_dict, eq_mixer
