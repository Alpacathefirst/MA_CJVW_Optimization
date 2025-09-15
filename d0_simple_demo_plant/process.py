from unit_handler import *


class EvaluateProcess:
    def __init__(self, model):
        self.model = model
        self.unit_handler = UnitHandler(model)

    def equations(self, process_inputs, optimization_variables, p):
        t_m102 = optimization_variables[0]
        t_p102 = optimization_variables[1]
        t_he101_cold = optimization_variables[2]
        pre_tear_stream = optimization_variables[3:]
        # tear_stream_co2, tear_stream_h2o, tear_stream_naoh = optimization_variables[3:]
        t_r101, p_r101, t_v101, p_v101, t_filter, p_filter = p[0], p[1], p[2], p[3], p[4], p[5]
        # pre_tear_stream = [0] * len(NAMES)
        # pre_tear_stream[IDX['T']] = t_filter
        # pre_tear_stream[IDX['P']] = p_filter
        # pre_tear_stream[IDX['CO2']] = tear_stream_co2
        # pre_tear_stream[IDX['H2O']] = tear_stream_h2o
        # pre_tear_stream[IDX['NaOH']] = tear_stream_naoh
        # calculate inputs once to get enthalpies, entropies
        tear_stream = self.unit_handler.stream(inputs=pre_tear_stream,
                                               input_type='with naoh')
        v1 = self.unit_handler.stream(inputs=process_inputs[0],
                                      input_type='no naoh')
        solid_liquid = self.unit_handler.stream(inputs=process_inputs[1],
                                                input_type='with naoh')
        # define all units and how they are connected
        sl1 = self.unit_handler.mixer(name='M102',
                                      inputs=[solid_liquid, tear_stream],
                                      input_type='with naoh',
                                      t_out=t_m102,
                                      adiabatic=True)
        sl2 = self.unit_handler.pump(name='P102',
                                     inputs=[sl1],
                                     input_type='with naoh',
                                     pump_eff=1,
                                     p_out=p_r101,
                                     t_out=t_p102,
                                     adiabatic=True)
        sl3 = self.unit_handler.change_pt(name='HE101_cold',
                                          inputs=[sl2],
                                          input_type='with naoh',
                                          t_out=t_he101_cold)
        sl4 = self.unit_handler.change_pt(name='H101',
                                          inputs=[sl3],
                                          input_type='with naoh',
                                          t_out=t_r101,
                                          adiabatic=False)
        p1 = self.unit_handler.reactor(name='R101',
                                       inputs=[sl4, v1],
                                       input_type='with naoh',
                                       frac_conversion=0.95,
                                       t_out=t_r101)
        p2 = self.unit_handler.change_pt(name='HE101_hot',
                                         inputs=[p1],
                                         input_type='with naoh',
                                         t_out=sl2[IDX['T']] + 10,
                                         adiabatic=False)
        p3 = self.unit_handler.change_pt(name='VA101',
                                         inputs=[p1],
                                         input_type='with naoh',
                                         t_out=t_v101,
                                         p_out=p_v101,
                                         adiabatic=False)
        gpurge, p4 = self.unit_handler.flash(name='V101',
                                             inputs=[p3],
                                             input_type='with naoh',
                                             t_out=t_v101,
                                             adiabatic=False)
        lr1, product = self.unit_handler.filter(name='F101',
                                                inputs=[p4],
                                                input_type='with naoh',
                                                solid_split=0.98,
                                                res_moisture=0.2,
                                                t_out=t_filter,
                                                adiabatic=False)

        if self.model.get_equations:
            # equality contraint for HE101
            q_he101_hot = self.model.unit_heat_duties['HE101_hot']
            q_he101_cold = self.model.unit_heat_duties['HE101_cold']
            self.model.equalities.append((q_he101_hot + q_he101_cold) / maingopy.neg(q_he101_hot))

            # define the objective of the optimization
            molar_balances_squared = []
            for specie in VLE_SPECIES + SOL_SPECIES:
                molar_balance = (tear_stream[IDX[specie]] - lr1[IDX[specie]]) / maingopy.pos(tear_stream[IDX[specie]])
                molar_balances_squared.append(molar_balance ** 2)
            sum_molar_balances_squared = sum(np.array(molar_balances_squared))
            objective = sum_molar_balances_squared
            return objective

        # when just evaluating, return all stream values
        else:
            stream_dict = {
                'V-1': v1,
                'SOLID, LIQUID': solid_liquid,
                'S-L-1': sl1,
                'S-L-2': sl2,
                'S-L-3': sl3,
                'S-L-4': sl4,
                'P-1': p1,
                'P-2': p2,
                'P-3': p3,
                'P-4': p4,
                'GPURGE': gpurge,
                'LR-1': lr1,
                'PRODUCT': product
            }
            return stream_dict
