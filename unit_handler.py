from flash_handler import *
from flash_handler_2 import *


class UnitHandler:
    def __init__(self, model):
        self.model = model
        if NN_TYPE == 1:
            self.flash_handler = FlashHandler(self.model)
        else:
            self.flash_handler = FlashHandler2(self.model)

    def evaluate_heater(self, inputs, t_out):
        inputs = self.combine_inputs(inputs)
        enthalpy_in = inputs[IDX['enthalpy_vle']] + inputs[IDX['enthalpy_s']]
        inputs[IDX['T']] = t_out
        outputs = self.flash_handler.evaluate_pt_flash(inputs)
        enthalpy_out = outputs[IDX['enthalpy_vle']] + outputs[IDX['enthalpy_s']]
        heat_supply = enthalpy_out - enthalpy_in
        return outputs, heat_supply

    def evaluate_reactor(self, inputs, t_out):
        inputs = self.combine_inputs(inputs)
        enthalpy_in = inputs[IDX['enthalpy_vle']] + inputs[IDX['enthalpy_s']]
        inputs[IDX['T']] = t_out
        # reaction
        fractional_conversion = 0.95
        n_reacted = fractional_conversion * inputs[IDX['Forsterite']]
        # Forsterite + 2 CO2 = 2 Magnesite + Amourphous_silica
        inputs[IDX['Forsterite']] -= n_reacted
        inputs[IDX['CO2_vap']] -= 2 * n_reacted
        inputs[IDX['Magnesite']] += 2 * n_reacted
        inputs[IDX['Amorphous_Silica']] += n_reacted
        outputs = self.flash_handler.evaluate_pt_flash(inputs)
        enthalpy_out = outputs[IDX['enthalpy_vle']] + outputs[IDX['enthalpy_s']]
        heat_supply = enthalpy_out - enthalpy_in
        return outputs, heat_supply

    # mixer is implemented as adiabatic only
    def evaluate_mixer(self, inputs, t_out):
        inputs = self.combine_inputs(inputs)
        enthalpy_in = inputs[IDX['enthalpy_vle']] + inputs[IDX['enthalpy_s']]
        inputs[IDX['T']] = t_out
        outputs = self.flash_handler.evaluate_pt_flash(inputs)
        enthalpy_out = outputs[IDX['enthalpy_vle']] + outputs[IDX['enthalpy_s']]
        if self.model.get_equations:
            enthalpy = maingopy.neg(enthalpy_in)  # tell maingopy this value will always be negative
        else:
            enthalpy = enthalpy_in
        eq_constraint = (enthalpy_out - enthalpy_in) / enthalpy
        return outputs, eq_constraint

    def evaluate_pump(self, inputs, p_out):
        inputs = self.combine_inputs(inputs)
        inputs[IDX['P']] = p_out
        outputs = self.flash_handler.evaluate_pt_flash(inputs)
        return outputs

    def evaluate_flash(self, inputs, t_out, p_out):
        inputs = self.combine_inputs(inputs)
        inputs[IDX['T']] = t_out
        inputs[IDX['P']] = p_out

        outputs = self.flash_handler.evaluate_pt_flash(inputs)

        # initialise outputs
        vap_outputs = [0] * len(outputs)
        aq_outputs = [0] * len(outputs)

        vap_outputs[IDX['T']] = outputs[IDX['T']]
        vap_outputs[IDX['P']] = outputs[IDX['P']]
        aq_outputs[IDX['T']] = outputs[IDX['T']]
        aq_outputs[IDX['P']] = outputs[IDX['P']]

        for s in VAP_SCECIES:
            vap_outputs[IDX[s]] = outputs[IDX[s]]

        for s in AQ_SCECIES + SOL_SPECIES:
            aq_outputs[IDX[s]] = outputs[IDX[s]]

        # TODO: include energy balance

        return np.array(vap_outputs), np.array(aq_outputs)

    def evaluate_filter(self, inputs, liquid_split, solid_split):
        inputs = self.combine_inputs(inputs)
        vle_outputs = [0] * len(inputs)
        s_outputs = [0] * len(inputs)

        vle_outputs[IDX['T']] = inputs[IDX['T']]
        vle_outputs[IDX['P']] = inputs[IDX['P']]
        s_outputs[IDX['T']] = inputs[IDX['T']]
        s_outputs[IDX['P']] = inputs[IDX['P']]

        for s in (VAP_SCECIES + AQ_SCECIES):
            vle_outputs[IDX[s]] = inputs[IDX[s]] * liquid_split
            s_outputs[IDX[s]] = inputs[IDX[s]] * (1 - liquid_split)
        for s in SOL_SPECIES:
            vle_outputs[IDX[s]] = inputs[IDX[s]] * (1 - solid_split)
            s_outputs[IDX[s]] = inputs[IDX[s]] * solid_split

        # TODO: Include energy balance
        return np.array(vle_outputs), np.array(s_outputs)

    def evaluate_change_pt(self, t, p, inputs):
        inputs = self.combine_inputs(inputs)
        inputs[IDX['T']] = t
        inputs[IDX['P']] = p
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
        inputs_simple = [
                         inputs[IDX['CO2_vap']] + inputs[IDX['CO2_aq']],
                         inputs[IDX['H2O_vap']] + inputs[IDX['H2O_aq']],
                         inputs[IDX['NaOH_aq']]]
        return np.array(inputs_simple)

    def complicate_tearstream(self, t, p, inputs):
        inputs_comp = [0] * len(NAMES)
        inputs_comp[IDX['T']] = t
        inputs_comp[IDX['P']] = p
        inputs_comp[IDX['CO2_vap']] = inputs[0]
        inputs_comp[IDX['H2O_aq']] = inputs[1]
        inputs_comp[IDX['NaOH_aq']] = inputs[2]
        inputs_comp = self.flash_handler.evaluate_pt_flash(np.array(inputs_comp))
        return inputs_comp
