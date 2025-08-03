from flash_handler import *


class UnitHandler:
    def __init__(self, model):
        self.model = model
        self.flash_handler = FlashHandler(self.model)

    def evaluate_heater(self, inputs, t_out):
        inputs = self.combine_inputs(inputs)
        # [0, 1, 2      , 3     , 4      , 5           , 6     , 7    , 8     , 9      , 10         , 11       , 12        , 13      , 14              , 15        ]
        # [T, P, CO2_vap, N2_vap, H2O_vap, enthalpy_vap, CO2_aq, N2_aq, H2O_aq, NaOH_aq, enthalpy_aq, Magnesite, Forsterite, Fayalite, Amorphous_Silica, enthalpy_s]
        enthalpy_in = inputs[5] + inputs[10] + inputs[15]
        inputs[0] = t_out
        outputs = self.flash_handler.evaluate_pt_flash(inputs)
        enthalpy_out = outputs[5] + outputs[10] + outputs[15]
        heat_supply = enthalpy_out - enthalpy_in
        return outputs, heat_supply

    def evaluate_reactor(self, inputs, t_out):
        inputs = self.combine_inputs(inputs)
        # [0, 1, 2      , 3     , 4      , 5           , 6     , 7    , 8     , 9      , 10         , 11       , 12        , 13      , 14              , 15        ]
        # [T, P, CO2_vap, N2_vap, H2O_vap, enthalpy_vap, CO2_aq, N2_aq, H2O_aq, NaOH_aq, enthalpy_aq, Magnesite, Forsterite, Fayalite, Amorphous_Silica, enthalpy_s]
        enthalpy_in = inputs[5] + inputs[10] + inputs[15]
        inputs[0] = t_out
        # reaction
        fractional_conversion = 0.95
        n_reacted = fractional_conversion * inputs[12]
        # Forsterite + 2 CO2 = 2 Magnesite + Amourphous_silica
        inputs[12] -= n_reacted
        inputs[2] -= 2 * n_reacted
        inputs[11] += 2 * n_reacted
        inputs[14] += n_reacted
        outputs = self.flash_handler.evaluate_pt_flash(inputs)
        enthalpy_out = outputs[5] + outputs[10] + inputs[15]
        heat_supply = enthalpy_out - enthalpy_in
        return outputs, heat_supply

    # mixer is implemented as adiabatic only
    def evaluate_mixer(self, inputs, t_out):
        inputs = self.combine_inputs(inputs)
        # [0, 1, 2      , 3     , 4      , 5           , 6     , 7    , 8     , 9      , 10         , 11       , 12        , 13      , 14              , 15        ]
        # [T, P, CO2_vap, N2_vap, H2O_vap, enthalpy_vap, CO2_aq, N2_aq, H2O_aq, NaOH_aq, enthalpy_aq, Magnesite, Forsterite, Fayalite, Amorphous_Silica, enthalpy_s]
        inputs[0] = t_out
        outputs = self.flash_handler.evaluate_pt_flash(inputs)
        enthalpy_in = inputs[5] + inputs[10] + inputs[15]
        enthalpy_out = outputs[5] + outputs[10] + outputs[15]
        if self.model.get_equations:
            enthalpy = maingopy.neg(enthalpy_in)
        else:
            enthalpy = enthalpy_in
        eq_constraint = (enthalpy_out - enthalpy_in) / enthalpy
        return outputs, eq_constraint

    def evaluate_pump(self, inputs, p_out):
        inputs = self.combine_inputs(inputs)
        inputs[1] = p_out
        outputs = self.flash_handler.evaluate_pt_flash(inputs)
        return outputs

    def evaluate_flash(self, inputs, t_out, p_out):
        # [0, 1, 2      , 3     , 4      , 5           , 6     , 7    , 8     , 9      , 10         , 11       , 12        , 13      , 14              , 15        ]
        # [T, P, CO2_vap, N2_vap, H2O_vap, enthalpy_vap, CO2_aq, N2_aq, H2O_aq, NaOH_aq, enthalpy_aq, Magnesite, Forsterite, Fayalite, Amorphous_Silica, enthalpy_s]
        inputs = self.combine_inputs(inputs)
        inputs[0] = t_out
        inputs[1] = p_out
        outputs = self.flash_handler.evaluate_pt_flash(inputs)
        gas_outputs = [0] * len(outputs)  # plain Python list, can hold FFVar
        gas_outputs[:6] = outputs[:6]
        liquid_outputs = [0] * len(outputs)
        liquid_outputs[:2] = outputs[:2]
        liquid_outputs[6:] = outputs[6:]
        return np.array(gas_outputs), np.array(liquid_outputs)

    def evaluate_filter(self, inputs):
        # [0, 1, 2      , 3     , 4      , 5           , 6     , 7    , 8     , 9      , 10         , 11       , 12        , 13      , 14              , 15        ]
        # [T, P, CO2_vap, N2_vap, H2O_vap, enthalpy_vap, CO2_aq, N2_aq, H2O_aq, NaOH_aq, enthalpy_aq, Magnesite, Forsterite, Fayalite, Amorphous_Silica, enthalpy_s]
        inputs = self.combine_inputs(inputs)
        g_l_outputs = [0] * len(inputs)
        g_l_outputs[:11] = inputs[:11]
        s_outputs = [0] * len(inputs)
        s_outputs[:2] = inputs[:2]
        s_outputs[11:] = inputs[11:]
        return np.array(g_l_outputs), np.array(s_outputs)

    def evaluate_change_pt(self, t, p, inputs):
        inputs = self.combine_inputs(inputs)
        inputs[0] = t
        inputs[1] = p
        outputs = self.flash_handler.evaluate_pt_flash(inputs)
        return outputs

    def combine_inputs(self, inputs):
        if len(inputs) == 1:
            return np.array(inputs[0])  # just return the single stream as-is
        stacked = np.stack(inputs)
        summed_species = np.sum(stacked[:, 2:], axis=0)
        total_input = np.concatenate([inputs[0][:2], summed_species])
        return total_input

    def simplify_tearstream(self, inputs):
        # inputs = [T, P, CO2, N2, H2O, NaOH]
        # [0, 1, 2      , 3     , 4      , 5           , 6     , 7    , 8     , 9      , 10         , 11       , 12        , 13      , 14              , 15        ]
        # [T, P, CO2_vap, N2_vap, H2O_vap, enthalpy_vap, CO2_aq, N2_aq, H2O_aq, NaOH_aq, enthalpy_aq, Magnesite, Forsterite, Fayalite, Amorphous_Silica, enthalpy_s]
        inputs_simple = [
                         inputs[2] + inputs[6],  # CO2
                         inputs[3] + inputs[7],  # N2
                         inputs[4] + inputs[8],  # H2O
                         inputs[9]]  # NaOH
        return np.array(inputs_simple)

    def complicate_tearstream(self, t, p, inputs):
        inputs_comp = np.array([t,  # T
                       p,  # P
                       inputs[0],  # CO2_vap
                       inputs[1],  # N2_Vap
                       inputs[2],  # H2O_vap
                       0, 0, 0, 0,
                       inputs[3],  # NaOH
                       0, 0, 0, 0, 0, 0])
        inputs_comp = self.flash_handler.evaluate_pt_flash(inputs_comp)
        return inputs_comp
