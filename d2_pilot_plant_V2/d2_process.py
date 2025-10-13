from unit_handler import *


class EvaluateProcess:
    def __init__(self, model):
        self.model = model
        self.unit_handler = UnitHandler(model)

    def equations(self, process_inputs, optimization_variables, p):
        t_r101, p_r101, t_v101, p_v101, t_filter, p_filter, t_co2_tank, p_co2_tank, p_v102, \
        p_v103, p_v104, t_he_hot_out = p[0:]

        t_c101, t_c101_isen, t_va101, t_m102, t_p102, t_he101_cold, t_c102, t_c102_isen, t_c103, t_c103_isen, \
        t_c104, t_c104_isen = optimization_variables[11:23]

        liquid_split = optimization_variables[26]
        # p_v102 = optimization_variables[27]
        # p_v103 = optimization_variables[28]

        lr1_pre_tear_stream = [0] * len(NAMES)
        lr1_co2, lr1_h2o, lr1_naoh, lr1_magnesite, lr1_forsterite, lr1_fayalite, lr1_sio2 = optimization_variables[0:7]
        lr1_pre_tear_stream[IDX['T']] = t_filter
        lr1_pre_tear_stream[IDX['P']] = p_filter
        lr1_pre_tear_stream[IDX['CO2']] = lr1_co2
        lr1_pre_tear_stream[IDX['H2O']] = lr1_h2o
        lr1_pre_tear_stream[IDX['NaOH']] = lr1_naoh
        lr1_pre_tear_stream[IDX['Magnesite']] = lr1_magnesite
        lr1_pre_tear_stream[IDX['Forsterite']] = lr1_forsterite
        lr1_pre_tear_stream[IDX['Fayalite']] = lr1_fayalite
        lr1_pre_tear_stream[IDX['Amorphous_Silica']] = lr1_sio2

        vr1_pre_tear_stream = [0] * len(NAMES)
        vr1_co2, vr1_h2o = optimization_variables[7], optimization_variables[8]
        vr1_pre_tear_stream[IDX['T']] = t_r101
        vr1_pre_tear_stream[IDX['P']] = p_r101
        vr1_pre_tear_stream[IDX['CO2']] = vr1_co2
        vr1_pre_tear_stream[IDX['H2O']] = vr1_h2o

        vc2_pre_tear_stream = [0] * len(NAMES)
        vc2_co2, vc2_h2o = optimization_variables[9], optimization_variables[10]
        vc2_pre_tear_stream[IDX['T']] = t_c102
        vc2_pre_tear_stream[IDX['P']] = p_co2_tank
        vc2_pre_tear_stream[IDX['CO2']] = vc2_co2
        vc2_pre_tear_stream[IDX['H2O']] = vc2_h2o

        # make sure input streams are in equilibrium
        lr1_tear_stream = self.unit_handler.stream(inputs=lr1_pre_tear_stream,
                                                   input_type='with naoh')
        vr1_tear_stream = self.unit_handler.stream(inputs=vr1_pre_tear_stream,
                                                   input_type='no naoh')
        vc2_tear_stream = self.unit_handler.stream(inputs=vc2_pre_tear_stream,
                                                   input_type='no naoh')
        v1 = self.unit_handler.stream(inputs=process_inputs[0],
                                      input_type='no naoh')
        solid_liquid = self.unit_handler.stream(inputs=process_inputs[1],
                                                input_type='with naoh')

        # define all units and how they are connected
        vr2 = self.unit_handler.change_pt(name='VA-101',
                                          inputs=[vr1_tear_stream],
                                          input_type='no naoh',
                                          p_out=p_co2_tank,
                                          t_out=t_va101,
                                          adiabatic=True)
        vr3 = self.unit_handler.change_pt(name='H-101',
                                          inputs=[vr2, vc2_pre_tear_stream],
                                          input_type='no naoh',
                                          t_out=t_co2_tank,
                                          adiabatic=False)
        vr4, lpurge = self.unit_handler.flash(name='V-101',
                                              inputs=[vr3],
                                              input_type='no naoh',
                                              t_out=t_co2_tank,
                                              adiabatic=False)
        v2 = self.unit_handler.mixer(name='M-101',
                                     inputs=[v1, vr4],
                                     input_type='no naoh',
                                     t_out=t_co2_tank,
                                     adiabatic=False)
        v3, gpurge1 = self.unit_handler.splitter(name='S-101',
                                                 inputs=[v2],
                                                 input_type='no naoh',
                                                 split_factor=0.1,
                                                 adiabatic=False)
        v4 = self.unit_handler.compressor(name='C-101',
                                          inputs=[v3],
                                          input_type='no naoh',
                                          isentropic_eff=0.9,
                                          t_isen=t_c101_isen,
                                          t_out=t_c101,
                                          p_out=p_r101,
                                          adiabatic=True)
        sl1 = self.unit_handler.mixer(name='M-102',
                                      inputs=[solid_liquid, lr1_tear_stream],
                                      input_type='with naoh',
                                      t_out=t_m102,
                                      adiabatic=True)
        sl2 = self.unit_handler.pump(name='P-102',
                                     inputs=[sl1],
                                     input_type='with naoh',
                                     pump_eff=0.35,
                                     p_out=p_r101,
                                     t_out=t_p102,
                                     adiabatic=True)
        sl3 = self.unit_handler.change_pt(name='HE-101_cold',
                                          inputs=[sl2],
                                          input_type='with naoh',
                                          t_out=t_he101_cold,
                                          adiabatic=False)
        sl4 = self.unit_handler.change_pt(name='H-102',
                                          inputs=[sl3 ],
                                          input_type='with naoh',
                                          t_out=t_r101,
                                          adiabatic=False)
        pr = self.unit_handler.reactor(name='R-101',
                                       inputs=[sl4, v4],
                                       input_type='with naoh',
                                       frac_conversion=0.95,
                                       slr=0.4,
                                       molality=1,
                                       t_out=t_r101,
                                       adiabatic=False)
        vr1, p1 = self.unit_handler.flash(name='V-R',
                                          inputs=[pr],
                                          input_type='with naoh',
                                          t_out=t_r101,
                                          adiabatic=False)
        p2 = self.unit_handler.change_pt(name='HE-101_hot',
                                         inputs=[p1],
                                         input_type='with naoh',
                                         t_out=t_he_hot_out,
                                         adiabatic=False)
        p3 = self.unit_handler.change_pt(name='VA-102',
                                         inputs=[p2],
                                         input_type='with naoh',
                                         p_out=p_v102,
                                         adiabatic=False)
        vv2, p4 = self.unit_handler.flash(name='V-102',
                                          inputs=[p3],
                                          input_type='with naoh',
                                          adiabatic=False)
        p5 = self.unit_handler.change_pt(name='VA-103',
                                         inputs=[p4],
                                         input_type='with naoh',
                                         p_out=p_v103)
        vv3, p6 = self.unit_handler.flash(name='V-103',
                                          inputs=[p5],
                                          input_type='with naoh',
                                          adiabatic=False)
        p7 = self.unit_handler.change_pt(name='VA-104',
                                         inputs=[p6],
                                         input_type='with naoh',
                                         p_out=p_v104)
        vv4, p8 = self.unit_handler.flash(name='V-104',
                                          inputs=[p7],
                                          input_type='with naoh',
                                          adiabatic=False)
        p9 = self.unit_handler.change_pt(name='VA-105',
                                         inputs=[p8],
                                         input_type='with naoh',
                                         t_out=t_filter,
                                         p_out=p_filter,
                                         adiabatic=False)
        lr1, product = self.unit_handler.filter(name='F-101',
                                                inputs=[p9],
                                                input_type='with naoh',
                                                solid_split=0.99,
                                                res_moisture=liquid_split,
                                                # TODO: this is now liquid split factor not res moisture
                                                t_out=t_filter,
                                                adiabatic=False)
        vc4 = self.unit_handler.compressor(name='C-104',
                                           inputs=[vv4],
                                           input_type='no naoh',
                                           isentropic_eff=0.9,
                                           t_isen=t_c104_isen,
                                           t_out=t_c104,
                                           p_out=p_v103)
        vc3 = self.unit_handler.compressor(name='C-103',
                                           inputs=[vv3, vc4],
                                           input_type='no naoh',
                                           isentropic_eff=0.9,
                                           t_isen=t_c103_isen,
                                           t_out=t_c103,
                                           p_out=p_v102)
        vc2 = self.unit_handler.compressor(name='C-102',
                                           inputs=[vv2, vc3],
                                           input_type='no naoh',
                                           isentropic_eff=0.9,
                                           t_isen=t_c102_isen,
                                           t_out=t_c102,
                                           p_out=p_co2_tank)

        if self.model.get_equations:
            # equality contraint for HE101
            q_he101_hot = self.model.unit_heat_duties['HE-101_hot']
            q_he101_cold = self.model.unit_heat_duties['HE-101_cold']
            self.model.equalities.append((q_he101_hot + q_he101_cold) / maingopy.neg(q_he101_hot))

            # Equality constraint CO2
            co2_r = vr1[IDX['CO2']]
            co2_sto = sl4[IDX['Forsterite']] * 0.95 * 2
            co2_sto_spec = (co2_r + co2_sto) / maingopy.pos(co2_sto + NON_ZERO_EPSILON) - 1.5
            self.model.equalities.append(co2_sto_spec)

            # Equality constraint SLR
            # m_s = sum(content[IDX[s]] * MOLAR_MASS[s] for s in SOL_SPECIES)
            m_s = sum(sl4[IDX[s]] * MOLAR_MASS[s] for s in ['Forsterite', 'Fayalite'])
            m_w = sl4[IDX['H2O']] * MOLAR_MASS['H2O']
            slr = m_s / maingopy.pos(m_w + NON_ZERO_EPSILON) - 0.4
            self.model.equalities.append(slr)

            # Equality constrain Molality
            m_w = sl4[IDX['H2O']] * MOLAR_MASS['H2O']
            mol = sl4[IDX['NaOH']] / maingopy.pos(m_w + NON_ZERO_EPSILON) - 1
            self.model.equalities.append(mol)

            # Residual Moisture
            m_s_p = sum(product[IDX[s]] * MOLAR_MASS[s] for s in SOL_SPECIES)
            m_l_p = sum(product[IDX[s]] * MOLAR_MASS[s] for s in VLE_SPECIES)
            res_moisture = m_l_p / maingopy.pos(m_s_p + NON_ZERO_EPSILON) - 0.2
            self.model.equalities.append(res_moisture)

            # define the objective of the optimization
            tear_streams_errors = []
            for specie in VLE_SPECIES + SOL_SPECIES:
                molar_balance = (lr1_tear_stream[IDX[specie]] - lr1[IDX[specie]]) \
                                / maingopy.pos(lr1_tear_stream[IDX[specie]] + NON_ZERO_EPSILON)
                tear_streams_errors.append(molar_balance ** 2)
            for specie in ['CO2', 'H2O']:
                molar_balance = (vr1_tear_stream[IDX[specie]] - vr1[IDX[specie]]) \
                                / maingopy.pos(vr1_tear_stream[IDX[specie]] + NON_ZERO_EPSILON)
                tear_streams_errors.append(molar_balance ** 2)
            for specie in ['CO2', 'H2O']:
                molar_balance = (vc2_tear_stream[IDX[specie]] - vc2[IDX[specie]]) \
                                / maingopy.pos(vc2_tear_stream[IDX[specie]] + NON_ZERO_EPSILON)
                tear_streams_errors.append(molar_balance ** 2)
            self.model.equalities += tear_streams_errors
            # sum_molar_balances_squared = sum(np.array(tear_streams_errors))
            # objective = sum_molar_balances_squared
            return

        # when just evaluating, return all stream values
        else:
            # define the objective of the optimization
            tear_streams_errors = {}
            for specie in VLE_SPECIES + SOL_SPECIES:
                den1 = (lr1_tear_stream[IDX[specie]])
                molar_balance = (lr1_tear_stream[IDX[specie]] - lr1[IDX[specie]]) / den1 if den1 > 0 else 0.0
                tear_streams_errors[f'lr1_{specie}'] = molar_balance
            for specie in ['CO2', 'H2O']:
                den2 = vr1_tear_stream[IDX[specie]]
                molar_balance = (vr1_tear_stream[IDX[specie]] - vr1[IDX[specie]]) / den2 if den2 > 0 else 0.0
                tear_streams_errors[f'vr4_{specie}'] = molar_balance
            for specie in ['CO2', 'H2O']:
                den3 = vc2_tear_stream[IDX[specie]]
                molar_balance = (vc2_tear_stream[IDX[specie]] - vc2[IDX[specie]]) / den3 if den3 > 0 else 0.0
                tear_streams_errors[f'vc2_{specie}'] = molar_balance

            stream_dict = {
                'V-1': v1,
                'V-2': v2,
                'GPURGE2': gpurge1,
                'V-3': v3,
                'V-4': v4,
                'V-R1': vr1,
                'V-R2': vr2,
                'V-R3': vr3,
                'LPURGE': lpurge,
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
                'LR-1': lr1,
                'PRODUCT': product,
                'VV4': vv4,
                'VV3': vv3,
                'VV2': vv2,
                'VC4': vc4,
                'VC3': vc3,
                'VC2': vc2
            }
            return tear_streams_errors, stream_dict
