from unit_handler import *


class EvaluateProcess:
    def __init__(self, model):
        self.model = model
        self.unit_handler = UnitHandler(model)

    def equations(self, process_inputs, optimization_variables, p):
        t_sl1 = optimization_variables[0]
        t_sl2 = optimization_variables[1]
        t_sl3 = optimization_variables[2]
        t_p4 = optimization_variables[3]
        tear_stream_simple = optimization_variables[4:]
        v1 = process_inputs[0]
        solid_liquid = process_inputs[1]
        t_r101, p_r101, t_v101, p_v101, t_filter, p_filter = p[0], p[1], p[2], p[3], p[4], p[5]
        # complicate the tear_stream
        tear_stream, ineq_tearstream = self.unit_handler.complicate_tearstream(inputs=tear_stream_simple, t=t_filter,
                                                                               p=p_filter)

        # calculate inputs once to get enthalpies
        v1, ineq_v1 = self.unit_handler.sh_handler.evaluate(inputs=v1)
        v2, ineq_m101 = self.unit_handler.evaluate_mixer(inputs=v1)

        solid_liquid, ineq_sl = self.unit_handler.sh_handler.evaluate(inputs=solid_liquid)
        sl1, q_mixer, ineq_m102 = self.unit_handler.evaluate_mixer(inputs=[solid_liquid, tear_stream], t_out=t_sl1)
        sl2, q_p102, ineq_p102 = self.unit_handler.evaluate_pump(inputs=[sl1], t_out=t_sl2, p_out=p_r101)
        sl3, q_he101_cold, ineq_he101_cold = self.unit_handler.evaluate_change_pt(inputs=[sl2], t_out=t_sl3,
                                                                                  p_out=sl2[IDX['P']], adiabatic=False)
        sl4, q_h101, ineq_h101 = self.unit_handler.evaluate_change_pt(inputs=[sl3], t_out=t_r101, p_out=sl3[IDX['P']],
                                                                      adiabatic=False)
        p1, q_r101, slr_eq, mol_eq, ineq_r101 = self.unit_handler.evaluate_reactor(inputs=[sl4, v1], t_out=t_r101)
        p2, q_he101_hot, ineq_he101_hot = self.unit_handler.evaluate_change_pt(inputs=[p1], t_out=sl2[IDX['T']] + 10,
                                                                               p_out=p1[IDX['P']], adiabatic=False)
        p3, q_va101, ineq_va101 = self.unit_handler.evaluate_change_pt(inputs=[p1], t_out=t_v101, p_out=p_v101,
                                                                       adiabatic=False)
        gpurge, p4, q_v101, ineq_v101 = self.unit_handler.evaluate_flash(inputs=[p3], t_out=t_filter, p_out=p_v101)
        lr1, product, q_f101, ineq_f101 = self.unit_handler.evaluate_filter(inputs=[p4], liquid_split=0.9,
                                                                            solid_split=1)
        output_tearstream_simple = self.unit_handler.simplify_tearstream(inputs=lr1)

        # adiabatic units:
        q_he101 = (q_he101_hot + q_he101_cold) / maingopy.neg(q_he101_hot)

        # if not evaluating, all these equations are returned plus equality constraints and objective
        if self.model.get_equations:
            eq_constraints = [q_mixer, q_he101, q_p102]
            ineq_constraints = ineq_tearstream + ineq_v1 + ineq_sl + ineq_m102 + ineq_p102 + ineq_he101_cold + \
                               ineq_h101 + ineq_r101 + ineq_he101_hot + ineq_va101 + ineq_v101 + ineq_f101

            molar_balances_squared = []
            for index, specie in enumerate(output_tearstream_simple):
                molar_balance = (output_tearstream_simple[index] - tear_stream_simple[index]) / maingopy.pos(
                    output_tearstream_simple[index])
                molar_balances_squared.append(molar_balance ** 2)
            sum_molar_balances_squared = sum(np.array(molar_balances_squared))
            eq_constraints = eq_constraints
            objective = sum_molar_balances_squared
            return eq_constraints, ineq_constraints, objective
        # when just evaluating, return all stream values
        else:
            output_dict = {
                'V-1': v1,
                'SOLID, LIQUID': solid_liquid,
                'LR-1': lr1,
                'S-L-1': sl1,
                'S-L-2': sl2,
                'S-L-3': sl3,
                'S-L-4': sl4,
                'P-1': p1,
                'P-2': p2,
                'P-3': p3,
                'P-4': p4,
            }
            return output_dict, q_mixer, q_he101
