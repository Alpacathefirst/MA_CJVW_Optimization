from unit_handler import *


class EvaluateProcess:
    def __init__(self, model):
        self.model = model
        self.unit_handler = UnitHandler(model)

    def equations(self, process_inputs, optimization_variables, p):
        t_m101 = optimization_variables[0]
        t_c101 = optimization_variables[1]
        t_va101 = optimization_variables[2]
        t_m102 = optimization_variables[3]
        t_p102 = optimization_variables[4]
        t_he101_cold = optimization_variables[5]

        lr1_pre_tear_stream = [0] * len(NAMES)
        lr1_pre_tear_stream[0:5] = optimization_variables[6:11]
        vr4_pre_tear_stream = [0] * len(NAMES)
        vr4_pre_tear_stream[0:4] = optimization_variables[11:15]

        t_r101, p_r101, t_v101, p_v101, t_filter, p_filter, t_co2_tank, p_co2_tank = \
            p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]

        # make sure input streams are in equilibrium
        lr1_tear_stream = self.unit_handler.stream(inputs=lr1_pre_tear_stream,
                                                   input_type='with naoh')
        vr4_tear_stream = self.unit_handler.stream(inputs=vr4_pre_tear_stream,
                                                   input_type='no naoh')
        v1 = self.unit_handler.stream(inputs=process_inputs[0],
                                      input_type='no naoh')
        solid_liquid = self.unit_handler.stream(inputs=process_inputs[1],
                                                input_type='with naoh')

        # define all units and how they are connected
        v2 = self.unit_handler.mixer(name='M101',
                                     inputs=[v1, vr4_tear_stream],
                                     input_type='no naoh',
                                     t_out=t_m101,
                                     adiabatic=False)
        v3, gpurge1 = self.unit_handler.splitter(name='S101',
                                                 inputs=[v2],
                                                 input_type='no naoh',
                                                 split_factor=0.1,
                                                 adiabatic=False)
        v4 = self.unit_handler.pump(name='C101',
                                    inputs=[v3],
                                    input_type='no naoh',
                                    pump_eff=0.3,
                                    t_out=t_c101,
                                    p_out=p_r101,
                                    adiabatic=True)

        sl1 = self.unit_handler.mixer(name='M102',
                                      inputs=[solid_liquid, lr1_tear_stream],
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
        pr = self.unit_handler.reactor(name='R101',
                                       inputs=[sl4, v4],
                                       input_type='with naoh',
                                       frac_conversion=0.95,
                                       t_out=t_r101)
        vr1, p1 = self.unit_handler.flash(name='VR',
                                          inputs=[pr],
                                          input_type='with naoh',
                                          t_out=t_r101,
                                          adiabatic=False)
        vr2 = self.unit_handler.change_pt(name='VA101',
                                          inputs=[vr1],
                                          input_type='no naoh',
                                          p_out=p_co2_tank,
                                          t_out=t_va101,
                                          adiabatic=True)
        vr3 = self.unit_handler.change_pt(name='h101',
                                          inputs=[vr2],
                                          input_type='no naoh',
                                          t_out=t_co2_tank)
        vr4, lpurge = self.unit_handler.flash(name='V101',
                                              inputs=[vr3],
                                              input_type='no naoh',
                                              t_out=t_co2_tank)

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
                                                solid_split=1,
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
            for specie in VLE_SPECIES:
                molar_balance = (lr1_tear_stream[IDX[specie]] - lr1[IDX[specie]]) \
                                / maingopy.pos(lr1_tear_stream[IDX[specie]])
                molar_balances_squared.append(molar_balance ** 2)
            for specie in ['CO2', 'H2O']:
                molar_balance = (vr4_tear_stream[IDX[specie]] - vr4[IDX[specie]]) \
                                / maingopy.pos(vr4_tear_stream[IDX[specie]])
                molar_balances_squared.append(molar_balance ** 2)
            sum_molar_balances_squared = sum(np.array(molar_balances_squared))
            objective = sum_molar_balances_squared
            return objective

        # when just evaluating, return all stream values
        else:
            stream_dict = {
                'V-1': v1,
                'V-2': v2,
                'GPURGE2': gpurge1,
                'V-3': v3,
                'V-4': v4,
                'V-R1': vr1,
                'V-R2': vr2,
                'V-R3': vr3,
                'V-R4': vr4,
                'SOLID, LIQUID': solid_liquid,
                'S-L-1': sl1,
                'S-L-2': sl2,
                'S-L-3': sl3,
                'S-L-4': sl4,
                'P-R': pr,
                'P-1': p1,
                'P-2': p2,
                'P-3': p3,
                'P-4': p4,
                'GPURGE': gpurge,
                'LR-1': lr1,
                'PRODUCT': product
            }
            return stream_dict
