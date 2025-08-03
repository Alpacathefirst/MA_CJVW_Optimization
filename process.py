from unit_handler import *


class EvaluateProcess:
    def __init__(self, model):
        self.model = model
        self.unit_handler = UnitHandler(model)

    def equations(self, process_inputs, optimization_variables, p, get_equations):
        tear_stream_simple = optimization_variables[1:]
        t_out_mixer = optimization_variables[0]
        co2_in = process_inputs[0]
        sla_in = process_inputs[1]
        t_reactor, p_reactor, t_flash, p_flash = p[0], p[1], p[2], p[3]
        # calculate inputs once to get enthalpies
        tear_stream = self.unit_handler.complicate_tearstream(t_flash, p_flash, tear_stream_simple)
        tear_stream = self.unit_handler.flash_handler.evaluate_pt_flash(tear_stream)
        co2_in = self.unit_handler.flash_handler.evaluate_pt_flash(co2_in)
        sla_in = self.unit_handler.flash_handler.evaluate_pt_flash(sla_in)
        output_mixer, eq_mixer = self.unit_handler.evaluate_mixer([sla_in, tear_stream], t_out_mixer)
        output_pump = self.unit_handler.evaluate_pump([output_mixer], p_reactor)
        output_heater, q_heater = self.unit_handler.evaluate_heater([output_pump], t_reactor)
        output_reactor, q_heater = self.unit_handler.evaluate_reactor([output_heater, co2_in], t_reactor)
        g_out_flash, l_out_flash = self.unit_handler.evaluate_flash([output_reactor], t_flash, p_flash)
        l_out_filter, s_out_filter = self.unit_handler.evaluate_filter([l_out_flash])
        output_tearstream = self.unit_handler.evaluate_change_pt(t=70+273, p=1, inputs=[l_out_filter])
        output_tearstream_simple = self.unit_handler.simplify_tearstream(output_tearstream)
        # if not evaluating, all these equations are returned plus equality constraints and objective
        if self.model.get_equations:
            eq_constraints = [eq_mixer]
            molar_balance = []
            for index, specie in enumerate(output_tearstream_simple):
                molar_balance.append((output_tearstream_simple[index] - tear_stream_simple[index]) / maingopy.pos(output_tearstream_simple[index]))
            # molar_balance = (output_tearstream_simple - tear_stream_simple) / maingopy.pos(output_tearstream_simple)
            objective = sum(np.array(molar_balance))**2
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
                'Output tearstream (full)': output_tearstream,
                'Output tearstream (simple)': output_tearstream_simple,
            }
            return output_dict, eq_mixer
