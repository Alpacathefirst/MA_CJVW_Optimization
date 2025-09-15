from ann_handler import *
from abc import ABC, abstractmethod


class BaseUnit(ABC):
    def __init__(self, model, ann_handler, name, inputs, input_type, t_out=None, p_out=None, adiabatic=False):
        self.model = model
        self.ann = ann_handler
        self.name = name
        self.inputs = inputs
        self.input_type = input_type
        self.t_out, self.p_out, self.adiabatic = t_out, p_out, adiabatic
        self.outputs = []
        self.inequalities = []
        self.equalities = []
        self.Q = None

    def run(self):
        combined_inputs = self.combine_inputs(self.inputs)
        h_in = combined_inputs[IDX['enthalpy_vle']] + combined_inputs[IDX['enthalpy_s']]
        if self.p_out is not None:
            combined_inputs[IDX['P']] = self.p_out
        if self.t_out is not None:
            combined_inputs[IDX['T']] = self.t_out

        contents = self.compute_content(combined_inputs)  # list of streams
        self.outputs, self.inequalities = self.run_anns(contents)  # calls ANN(s)

        self.equalities = self.get_equalities(combined_inputs)  # optional constraints
        self.Q = self.enthalpy_balance(h_in, self.adiabatic)
        self.model.equalities += self.equalities
        self.model.inequalities += self.inequalities
        self.model.unit_heat_duties[self.name] = self.Q
        return self.return_outputs()

    # --- Default/shared helpers ---
    def combine_inputs(self, inputs):
        if len(inputs) == 1:
            return np.array(inputs[0])  # just return the single stream as-is
        stacked = np.stack(inputs)
        summed_entries = np.sum(stacked[:, 2:], axis=0)  # sum all entries except T and P
        total_input = np.concatenate([inputs[0][:2], summed_entries])
        return total_input

    def run_anns(self, contents):
        outs, ineqs = [], []
        for content in contents:
            out, inq = self.ann.evaluate(self.ann_type(), content, self.input_type)
            outs += out
            ineqs += inq
        return outs, ineqs

    def enthalpy_balance(self, h_in, adiabatic):
        h_out = 0
        for output in self.outputs:
            h_out = h_out + output[IDX['enthalpy_vle']] + output[IDX['enthalpy_s']]
        if adiabatic:
            base = maingopy.neg(h_in) if self.model.get_equations else h_in
            eq = (h_out - h_in) / base
            self.equalities.append(eq)
        return h_out - h_in

    def return_outputs(self):
        return self.outputs[0] if len(self.outputs) == 1 else (*self.outputs,)

    def compute_content(self, combined_inputs):
        return[combined_inputs]

    def get_equalities(self, combined_inputs):
        return []

    @abstractmethod
    def ann_type(self):
        ...


class MixerUnit(BaseUnit):
    def ann_type(self): return 'hs'


class FlashUnit(BaseUnit):
    def ann_type(self): return 'vle'


class ReactorUnit(BaseUnit):
    def __init__(self, *args, frac_conversion, slr=None, molality=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.frac_conversion = frac_conversion
        self.slr = slr
        self.molality = molality

    def compute_content(self, combined_inputs):
        content = combined_inputs
        n_reacted = self.frac_conversion * combined_inputs[IDX['Forsterite']]
        content[IDX['Forsterite']] -= n_reacted
        content[IDX['CO2']] -= 2 * n_reacted
        content[IDX['Magnesite']] += 2 * n_reacted
        content[IDX['Amorphous_Silica']] += n_reacted
        return [content]

    def get_equalities(self, combined_inputs):
        equalities = []
        if self.slr is not None:
            m_s = sum(combined_inputs[IDX[s]] * MOLAR_MASS[s] for s in SOL_SPECIES)
            m_w = combined_inputs[IDX['H2O']] * MOLAR_MASS['H2O']
            slr = m_s / maingopy.pos(m_w) - self.slr
            equalities.append(slr)
        if self.molality is not None:
            m_w = combined_inputs[IDX['H2O']] * MOLAR_MASS['H2O']
            mol = combined_inputs[IDX['NaOH']] / maingopy.pos(m_w) - self.molality
            equalities.append(mol)
        return equalities

    def ann_type(self):
        return 'hs'


class PumpUnit(BaseUnit):
    def __init__(self, *args, pump_eff, **kwargs):
        super().__init__(*args, **kwargs)
        self.pump_eff = pump_eff

    def compute_content(self, combined_inputs):
        delta_p = self.p_out - combined_inputs[IDX['P']]
        volume_flow = combined_inputs[IDX['H2O']] * MOLAR_MASS['H2O'] / 1000  # in m3 / time_unit
        power = delta_p * volume_flow / self.pump_eff  # pump efficiency = 1
        content = combined_inputs
        content[IDX['enthalpy_vle']] += power
        return [content]

    def ann_type(self):
        return 'hs'


class FilterUnit(BaseUnit):
    def __init__(self, *args, solid_split, res_moisture, **kwargs):
        super().__init__(*args, **kwargs)
        self.solid_split = solid_split
        self.res_moisture = res_moisture

    def compute_content(self, combined_inputs):
        vle_outputs = [0] * len(combined_inputs)
        s_outputs = [0] * len(combined_inputs)

        vle_outputs[IDX['T']] = combined_inputs[IDX['T']]
        vle_outputs[IDX['P']] = combined_inputs[IDX['P']]
        s_outputs[IDX['T']] = combined_inputs[IDX['T']]
        s_outputs[IDX['P']] = combined_inputs[IDX['P']]

        # m_s = 0  # total amount of solids in kg
        # for s in SOL_SPECIES:
        #     m_s += combined_inputs[IDX[s]] * MOLAR_MASS[s]
        # m_l = 0
        # for s in VLE_SPECIES:
        #     m_l += combined_inputs[IDX[s]] * MOLAR_MASS[s]
        #
        # print('ms', m_s)
        # print('ml', m_l)
        # m_s_cake = self.solid_split * m_s
        # # from res_m = m_l_cake / (m_l_cake + m_s_cake)
        # m_l_cake = self.res_moisture / (1 - self.res_moisture) * m_s_cake
        #
        # # amount of liquid that is recycled
        # liquid_split = 1 - m_l_cake / m_l

        liquid_split = self.res_moisture

        for s in VLE_SPECIES:
            vle_outputs[IDX[s]] = combined_inputs[IDX[s]] * liquid_split
            s_outputs[IDX[s]] = combined_inputs[IDX[s]] * (1 - liquid_split)

        for s in SOL_SPECIES:
            vle_outputs[IDX[s]] = combined_inputs[IDX[s]] * (1 - self.solid_split)
            s_outputs[IDX[s]] = combined_inputs[IDX[s]] * self.solid_split

        print('vle_outputs', vle_outputs)
        print("PRODUCT", s_outputs)
        return [vle_outputs, s_outputs]

    def ann_type(self):
        return 'hs'


class ChangePTUnit(BaseUnit):
    def ann_type(self):
        return 'hs'
