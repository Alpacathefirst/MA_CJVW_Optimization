from process_unit_classes import *


class UnitHandler:
    def __init__(self, model):
        self.model = model
        self.ann = AnnHandler(self.model)

    def stream(self, inputs, input_type):
        output, ineq = self.ann.evaluate(ann_type='hs', inputs=inputs, input_type=input_type)
        self.model.inequalities += ineq
        return output[0]

    def mixer(self, name, inputs, input_type, t_out, p_out=None, adiabatic=True):
        return MixerUnit(model=self.model, ann_handler=self.ann, name=name, inputs=inputs, input_type=input_type,
                         t_out=t_out, p_out=p_out, adiabatic=adiabatic).run()

    def flash(self, name, inputs, input_type, t_out, p_out=None, adiabatic=True):
        return FlashUnit(model=self.model, ann_handler=self.ann, name=name, inputs=inputs, input_type=input_type,
                         t_out=t_out, p_out=p_out, adiabatic=adiabatic).run()

    def reactor(self, name, inputs, input_type, frac_conversion, t_out, p_out=None, adiabatic=False):
        return ReactorUnit(model=self.model, ann_handler=self.ann, name=name, inputs=inputs, input_type=input_type,
                           frac_conversion=frac_conversion, t_out=t_out, p_out=p_out, adiabatic=adiabatic).run()

    def pump(self, name, inputs, input_type, pump_eff, t_out, p_out=None, adiabatic=True):
        return PumpUnit(model=self.model, ann_handler=self.ann, name=name, inputs=inputs, input_type=input_type,
                        pump_eff=pump_eff, t_out=t_out, p_out=p_out, adiabatic=adiabatic).run()

    def filter(self, name, inputs, input_type, solid_split, res_moisture, t_out, p_out=None, adiabatic=True):
        return FilterUnit(model=self.model, ann_handler=self.ann, name=name, inputs=inputs, input_type=input_type,
                          solid_split=solid_split, res_moisture=res_moisture,
                          t_out=t_out, p_out=p_out, adiabatic=adiabatic).run()

    def change_pt(self, name, inputs, input_type, t_out=None, p_out=None, adiabatic=False):
        return ChangePTUnit(model=self.model, ann_handler=self.ann, name=name, inputs=inputs, input_type=input_type,
                            t_out=t_out, p_out=p_out, adiabatic=adiabatic).run()
#     def evaluate_reactor(self, name, inputs, t_out):
#
#         def get_equalities():
#             # SLR Equality constraint
#             m_s = 0  # total amount of solids in kg
#             for s in SOL_SPECIES:
#                 m_s += inputs[IDX[s]] * MOLAR_MASS[s]
#             m_water = (inputs[IDX['H2O_vap']] + inputs[IDX['H2O_aq']]) * MOLAR_MASS['H2O']
#             slr_equality = m_s / maingopy.pos(m_water) - 0.4
#
#             # Molality equality constraint
#             molality_eq = inputs[IDX['NaOH_aq']] / maingopy.pos(m_water) - 1
#
#             return [slr_equality, molality_eq]
#
#         # get_output function
#         def get_content(combined_inputs):
#             content = combined_inputs
#             fractional_conversion = 0.95
#             n_reacted = fractional_conversion * inputs[IDX['Forsterite']]
#
#             # Forsterite + 2 CO2 = 2 Magnesite + Amourphous_silica
#             content[IDX['Forsterite']] -= n_reacted
#             content[IDX['CO2_vap']] -= 2 * n_reacted
#             content[IDX['Magnesite']] += 2 * n_reacted
#             content[IDX['Amorphous_Silica']] += n_reacted
#
#             return [content]
#
#         unit_handler = GeneralUnit(model=self.model,
#                                    name=name,
#                                    ann_type='hs',
#                                    inputs=inputs,
#                                    input_type='with naoh',
#                                    content_func=get_content,
#                                    eq_func=get_equalities,
#                                    t_out=t_out,
#                                    p_out=False,
#                                    adiabatic=False)
#
#         output = unit_handler.outputs
#         q = unit_handler.Q
#         eqs = get_equalities()
#         ineqs = unit_handler.inequalities
#
#         return output, q, eqs, ineqs
#
#     # mixer is implemented as adiabatic only
#     def evaluate_mixer(self, name, inputs, input_type, t_out):
#
#         def get_content(combined_inputs):
#             return [combined_inputs]
#
#         unit_handler = GeneralUnit(model=self.model,
#                                    name=name,
#                                    ann_type='hs',
#                                    inputs=inputs,
#                                    input_type=input_type,
#                                    content_func=get_content,
#                                    eq_func=False,
#                                    t_out=t_out,
#                                    p_out=False,
#                                    adiabatic=True)
#
#         return unit_handler.return_outputs()
#
#     def evaluate_pump(self, name, inputs, input_type, t_out, p_out, adiabatic=True):
#
#         def get_content(combined_inputs):
#
#             delta_p = p_out - combined_inputs[IDX['P']]
#             volume_flow = combined_inputs[IDX['H2O_aq']] * MOLAR_MASS['H2O'] / 1000  # in m3 / time_unit
#             power = delta_p * volume_flow / 1  # pump efficiency = 1
#             content = combined_inputs
#             content['vle_enthalpy'] += power
#
#             return [content]
#
#         unit_handler = GeneralUnit(model=self.model,
#                                    name=name,
#                                    ann_type='hs',
#                                    inputs=inputs,
#                                    input_type=input_type,
#                                    content_func=get_content,
#                                    eq_func=False,
#                                    t_out=t_out,
#                                    p_out=p_out,
#                                    adiabatic=adiabatic)
#
#         return unit_handler.return_outputs()
#
#     def evaluate_flash(self, name, inputs, input_type):
#
#         def get_content(combined_inputs):
#             return [combined_inputs]
#
#         unit_handler = GeneralUnit(model=self.model,
#                                    name=name,
#                                    ann_type='vle',
#                                    inputs=inputs,
#                                    input_type=input_type,
#                                    content_func=get_content,
#                                    eq_func=False,
#                                    t_out=False,
#                                    p_out=False,
#                                    adiabatic=True)
#
#         return unit_handler.return_outputs()
#
#     def evaluate_filter(self, name, inputs, solid_split, res_moisture):
#
#         def get_content(combined_inputs):
#             vle_outputs = [0] * len(combined_inputs)
#             s_outputs = [0] * len(combined_inputs)
#
#             vle_outputs[IDX['T']] = combined_inputs[IDX['T']]
#             vle_outputs[IDX['P']] = combined_inputs[IDX['P']]
#             s_outputs[IDX['T']] = combined_inputs[IDX['T']]
#             s_outputs[IDX['P']] = combined_inputs[IDX['P']]
#
#             m_s = 0  # total amount of solids in kg
#             for s in SOL_SPECIES:
#                 m_s += inputs[IDX[s]] * MOLAR_MASS[s]
#             m_l = 0
#             for s in AQ_SCECIES:
#                 m_l += inputs[IDX[s]] * MOLAR_MASS[s]
#
#             m_s_cake = solid_split * m_s
#             # from res_m = m_l_cake / (m_l_cake + m_s_cake)
#             m_l_cake = res_moisture / (1 - res_moisture) * m_s_cake
#
#             liquid_split = m_l_cake / m_l
#
#             for s in (VAP_SCECIES + AQ_SCECIES):
#                 vle_outputs[IDX[s]] = inputs[IDX[s]] * liquid_split
#                 s_outputs[IDX[s]] = inputs[IDX[s]] * (1 - liquid_split)
#
#             for s in SOL_SPECIES:
#                 vle_outputs[IDX[s]] = inputs[IDX[s]] * (1 - solid_split)
#                 s_outputs[IDX[s]] = inputs[IDX[s]] * solid_split
#
#             return [vle_outputs, s_outputs]
#
#         unit_handler = GeneralUnit(model=self.model,
#                                    name=name,
#                                    ann_type='hs',
#                                    inputs=inputs,
#                                    input_type='with naoh',
#                                    content_func=get_content,
#                                    eq_func=False,
#                                    t_out=False,
#                                    p_out=False,
#                                    adiabatic=True)
#
#         return unit_handler.return_outputs()
#
#     def evaluate_change_pt(self, name, inputs, input_type, t_out=False, p_out=False, adiabatic=False):
#
#         def get_content(combined_inputs):
#             return [combined_inputs]
#
#         unit_handler = GeneralUnit(model=self.model,
#                                    name=name,
#                                    ann_type='hs',
#                                    inputs=inputs,
#                                    input_type=input_type,
#                                    content_func=get_content,
#                                    eq_func=False,
#                                    t_out=t_out,
#                                    p_out=p_out,
#                                    adiabatic=adiabatic)
#
#         return unit_handler.return_outputs()
#
#
# class GeneralUnit:
#     def __init__(self, model, name, ann_type, inputs, input_type, content_func, eq_func, adiabatic, p_out, t_out):
#         self.model = model
#         self.name = name
#         self.ann_handler = AnnHandler(model)
#         self.ann_type = ann_type
#         self.input_type = input_type
#         self.combined_inputs = self.combine_inputs(inputs)
#         self.h_in = self.get_enthalpy_in()
#         self.set_pt(p_out, t_out)
#         self.content = content_func(self.combined_inputs)
#         self.outputs, self.inequalities = self.run_anns()
#         self.equalities = self.get_equalities(eq_func)
#         self.Q = self.enthalpy_balance(adiabatic)
#
#     # combine all the inputs into 1 input by summing the species
#     def combine_inputs(self, inputs):
#         if len(inputs) == 1:
#             return np.array(inputs[0])  # just return the single stream as-is
#         stacked = np.stack(inputs)
#         summed_entries = np.sum(stacked[:, 2:], axis=0)  # sum all entries except T and P
#         total_input = np.concatenate([inputs[0][:2], summed_entries])
#         return total_input
#
#     def get_enthalpy_in(self):
#         return self.combined_inputs[IDX['enthalpy_vle']] + self.combined_inputs[IDX['enthalpy_s']]
#
#     def set_pt(self, t_out, p_out):
#         if p_out:
#             self.combined_inputs[IDX['P']] = p_out
#         if t_out:
#             self.combined_inputs[IDX['T']] = t_out
#
#     def run_anns(self):
#         outputs = []
#         ineqs = []
#         for content in self.content:
#             output, ineq = self.ann_handler.evaluate(ann_type=self.ann_type, inputs=content, input_type=self.input_type)
#             outputs += output
#             ineqs += ineq
#         return outputs, ineqs
#
#     def get_equalities(self, eq_func):
#         if eq_func:
#             return eq_func()
#         else:
#             return []
#
#     def enthalpy_balance(self, adiabatic):
#         h_out = 0
#         for output in self.outputs:
#             h_out += output[IDX['enthalpy_vle']] + output[IDX['enthalpy_s']]
#         # when the unit is adiabatic set the scaled heat flow as an equality constraint
#         if adiabatic:
#             if self.model.get_equations:
#                 enthalpy = maingopy.neg(self.h_in)  # tell maingopy this value will always be negative
#             else:
#                 enthalpy = self.h_in
#             q_equality = (h_out - self.h_in) / enthalpy
#             self.equalities.append(q_equality)
#         Q = h_out - self.h_in
#         return Q
#
#     def return_outputs(self):
#         self.model.equalities += self.equalities
#         self.model.inequalities += self.inequalities
#         self.model.heat_duties[self.name] = self.Q
#         return self.outputs[0] if len(self.outputs) == 1 else (*self.outputs,)
