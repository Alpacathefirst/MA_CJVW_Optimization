from get_min_max import *
from constants.c1_constants import *


class AnnHandler:
    def __init__(self, model):
        self.model = model
        self.anns = {}
        self.input_bounds = {}
        self.load_models_and_bounds()

    def load_models_and_bounds(self):
        for ann_type in ['XY', 'AA', 'ALOAD', 'AY', 'HS']:
            self.anns[ann_type] = dict()
            self.input_bounds[ann_type] = dict()
            for input_type in ['with naoh', 'no naoh']:
                file_id = ANN_FILES.get(ann_type, {}).get(input_type)

                # Accept None: skip loading and store None placeholders
                if file_id is None:
                    self.anns[ann_type][input_type] = None
                    self.input_bounds[ann_type][input_type] = None
                    continue

                ann = maingopy.melonpy.FeedForwardNet()
                ann.load_model(NN_DIR, f'{file_id}.xml', maingopy.melonpy.XML)
                self.anns[ann_type][input_type] = ann
                self.input_bounds[ann_type][input_type] = get_min_max(file_id)

    def get_stream_specs(self, inputs, input_type):
        t = inputs[IDX['T']]
        p = inputs[IDX['P']]
        co2 = inputs[IDX['CO2']]
        h2o = inputs[IDX['H2O']]
        naoh = inputs[IDX['NaOH']]
        n_total = co2 + h2o + naoh

        if self.model.get_equations:
            # co2_frac = -co2 / maingopy.neg(-(co2 + h2o + NON_ZERO_EPSILON))
            co2_frac = co2 / maingopy.pos((co2 + h2o + NON_ZERO_EPSILON))
            # den = maingopy.lb_func(co2 + h2o, NON_ZERO_EPSILON)
            # co2_frac = co2 / den

            # self.model.inequalities.append(-co2_frac)
            if input_type == 'with naoh':
                molality = naoh / maingopy.pos((h2o * MOLAR_MASS['H2O'] + NON_ZERO_EPSILON))
            else:
                molality = 0

        # when just evaluating the model, the FFNN needs to return doubles not FFVars, his is done by loading the NN
        # differently. Also can't use maingopy.pos()
        else:
            den1 = co2 + h2o
            co2_frac = co2 / den1 if den1 > 0 else 0.0
            den2 = h2o * MOLAR_MASS['H2O']
            molality = naoh / den2 if den2 > 0 else 0.0

        return t, p, co2, h2o, naoh, co2_frac, molality, n_total

    def scale_input(self, unscaled, ann_type, input_type):
        min_in = self.input_bounds[ann_type][input_type]['min_in']
        max_in = self.input_bounds[ann_type][input_type]['max_in']
        return 2 * (unscaled - min_in) / (max_in - min_in) - 1

    def inverse_scale_output(self, unscaled, ann_type, input_type):
        min_out = self.input_bounds[ann_type][input_type]['min_out']
        max_out = self.input_bounds[ann_type][input_type]['max_out']
        scaled = 0.5 * (unscaled + 1) * (max_out - min_out) + min_out
        if ann_type == 'XY':
            # inverse log transform y_h2o
            scaled[0] = 10 ** scaled[0] - 1e-16
        elif ann_type in ['ALOAD', 'AA', 'AY']:
            # inverse log transform A_H2O
            scaled[1] = 10 ** scaled[1] - 1e-16
        return scaled

    def run_ann(self, inputs, ann_type, input_type):
        t, p, co2, h2o, naoh, co2_frac, molality, n_total = self.get_stream_specs(inputs, input_type)
        # scale the ann inputs between 0 and 1
        ineqs, ann_inputs_scaled = self.get_ineqs_and_ann_inputs(ann_type=ann_type, input_type=input_type, t=t, p=p,
                                                                 co2=co2, h2o=h2o, naoh=naoh,
                                                                 co2_frac=co2_frac, molality=molality)
        if self.model.get_equations:
            # Evaluate the network (in reduced-space)
            ann_outputs_scaled = self.anns[ann_type][input_type].calculate_prediction_reduced_space(ann_inputs_scaled)
        else:
            file = ANN_FILES[ann_type][input_type]
            ann = maingopy.melonpy.FeedForwardNetDouble(f'{NN_DIR}\\{file}', maingopy.melonpy.MODEL_FILE_TYPE.XML)
            ann_outputs_scaled = ann.calculate_prediction_reduced_space(ann_inputs_scaled)
        # scale the outputs back
        ann_outputs = self.inverse_scale_output(np.array(ann_outputs_scaled), ann_type=ann_type, input_type=input_type)
        if ann_type == 'XY':
            vap_out, aq_out = self.handle_vle_xy_output(inputs, input_type, ann_outputs, t, p, co2, h2o, naoh, n_total)
            return vap_out, aq_out, ineqs
        elif ann_type == 'AA':
            vap_out, aq_out = self.handle_vle_A_based_output(inputs, input_type, ann_outputs, t, p, co2, h2o, naoh)
            return vap_out, aq_out, ineqs
        elif ann_type == 'ALOAD':
            vap_out, aq_out = self.handle_vle_load_output(inputs, input_type, ann_outputs, t, p, co2, h2o, naoh)
            return vap_out, aq_out, ineqs
        elif ann_type == 'AY':
            vap_out, aq_out = self.handle_vle_AY_output(inputs, input_type, ann_outputs, t, p, co2, h2o, naoh)
            return vap_out, aq_out, ineqs
        elif ann_type == 'HS':
            outputs = self.handle_hs_output(inputs, input_type, ann_outputs, t, p, co2, h2o, naoh, n_total)
            return outputs, ineqs

    # the inequalities are the bounds of the ann_inputs, for which the network is trained
    def get_ineqs_and_ann_inputs(self, ann_type, input_type, t, p, co2, h2o, naoh, co2_frac, molality):
        # min_in = self.input_bounds[ann_type][input_type]['min_in']
        # max_in = self.input_bounds[ann_type][input_type]['max_in']

        # t_ineq_min = min_in[0] - t
        # t_ineq_max = t - max_in[0]
        # p_ineq_min = min_in[1] - p
        # p_ineq_max = p - max_in[1]
        # co2_ineq = -co2
        # h2o_ineq = -h2o
        # naoh_ineq = -naoh
        # co2_frac_ineq_min = - co2_frac
        # co2_frac_ineq_max = co2_frac - max_in[2]

        t_ineq_min = 273.15 - t
        t_ineq_max = t - 737.15
        p_ineq_min = 1 - p
        p_ineq_max = p - 200
        co2_ineq = -co2
        h2o_ineq = -h2o
        naoh_ineq = -naoh
        co2_frac_ineq_min = -co2_frac
        co2_frac_ineq_max = co2_frac - 1

        # ineqs = [t_ineq_min, t_ineq_max, p_ineq_min, p_ineq_max, co2_ineq, h2o_ineq, naoh_ineq]
        ineqs = [t_ineq_min, t_ineq_max, p_ineq_min, p_ineq_max, co2_frac_ineq_min, co2_frac_ineq_max, co2_ineq,
                 h2o_ineq, naoh_ineq]

        # ineqs = []
        if input_type == 'with naoh':
            molality_ineq_min = 0 - molality
            molality_ineq_max = molality - 5
            ineqs += [molality_ineq_min, molality_ineq_max]
            ann_inputs = [t, p, co2_frac, molality]
        elif input_type == 'no naoh':
            ann_inputs = [t, p, co2_frac]
        else:
            raise Exception(f'Input type {input_type} not supported')
        # drop all float constraints
        ineqs = [v for v in ineqs if not (isinstance(v, (int, float)))]
        ann_inputs_scaled = self.scale_input(np.array(ann_inputs), ann_type=ann_type, input_type=input_type)
        return ineqs, ann_inputs_scaled

    def handle_vle_xy_output(self, inputs, input_type, ann_outputs, t, p, co2, h2o, naoh, n_total):
        # ann_outputs: ['Y_H2O', 'X_CO2', 'vapor fraction']
        n_vap = n_total * ann_outputs[2]
        n_liq = n_total - n_vap

        h2o_vap = n_vap * ann_outputs[0]
        co2_liq = n_liq * ann_outputs[1]

        # recreate the complete output arrays
        vap_outputs = [0] * len(NAMES)
        aq_outputs = [0] * len(NAMES)

        vap_outputs[IDX['T']] = t
        vap_outputs[IDX['P']] = p

        vap_outputs[IDX['CO2']] = co2 - co2_liq
        vap_outputs[IDX['H2O']] = h2o_vap

        aq_outputs[IDX['T']] = t
        aq_outputs[IDX['P']] = p
        aq_outputs[IDX['CO2']] = co2_liq
        aq_outputs[IDX['H2O']] = h2o - h2o_vap

        if input_type == 'with naoh':
            aq_outputs[IDX['NaOH']] = naoh
            for s in SOL_SPECIES:
                aq_outputs[IDX[s]] = inputs[IDX[s]]

        return vap_outputs, aq_outputs

    def handle_vle_A_based_output(self, inputs, input_type, ann_outputs, t, p, co2, h2o, naoh):
        # ann_outputs: [A_CO2, A_H2O]
        co2_liq = ann_outputs[0] * co2
        h2o_vap = ann_outputs[1] * h2o

        # recreate the complete output arrays
        vap_outputs = [0] * len(NAMES)
        aq_outputs = [0] * len(NAMES)

        vap_outputs[IDX['T']] = t
        vap_outputs[IDX['P']] = p

        vap_outputs[IDX['CO2']] = co2 - co2_liq
        vap_outputs[IDX['H2O']] = h2o_vap

        aq_outputs[IDX['T']] = t
        aq_outputs[IDX['P']] = p
        aq_outputs[IDX['CO2']] = co2_liq
        aq_outputs[IDX['H2O']] = h2o - h2o_vap

        if input_type == 'with naoh':
            aq_outputs[IDX['NaOH']] = naoh
            for s in SOL_SPECIES:
                aq_outputs[IDX[s]] = inputs[IDX[s]]

        return vap_outputs, aq_outputs

    def handle_vle_load_output(self, inputs, input_type, ann_outputs, t, p, co2, h2o, naoh):
        # ann_outputs: [A_CO2, load_h2o]
        co2_liq = ann_outputs[0] * co2
        co2_vap = co2 - co2_liq

        # h2o_vap = ann_outputs[1] * co2_vap / denom
        h2o_vap = ann_outputs[1] * co2_vap

        # recreate the complete output arrays
        vap_outputs = [0] * len(NAMES)
        aq_outputs = [0] * len(NAMES)

        vap_outputs[IDX['T']] = t
        vap_outputs[IDX['P']] = p

        vap_outputs[IDX['CO2']] = co2_vap
        vap_outputs[IDX['H2O']] = h2o_vap

        aq_outputs[IDX['T']] = t
        aq_outputs[IDX['P']] = p
        aq_outputs[IDX['CO2']] = co2_liq
        aq_outputs[IDX['H2O']] = h2o - h2o_vap

        if input_type == 'with naoh':
            aq_outputs[IDX['NaOH']] = naoh
            for s in SOL_SPECIES:
                aq_outputs[IDX[s]] = inputs[IDX[s]]

        return vap_outputs, aq_outputs

    def handle_vle_AY_output(self, inputs, input_type, ann_outputs, t, p, co2, h2o, naoh):
        # ann_outputs: [A_CO2, Y_h2o]
        co2_liq = ann_outputs[0] * co2
        co2_vap = co2 - co2_liq

        if self.model.get_equations:
            denom = maingopy.pos(1 - ann_outputs[1] + NON_ZERO_EPSILON)
        else:
            # keep it purely numeric in eval mode and avoid 0-div
            denom_raw = 1 - ann_outputs[1]
            denom = denom_raw if denom_raw > 0 else NON_ZERO_EPSILON

        h2o_vap = ann_outputs[1] * co2_vap / denom

        # recreate the complete output arrays
        vap_outputs = [0] * len(NAMES)
        aq_outputs = [0] * len(NAMES)

        vap_outputs[IDX['T']] = t
        vap_outputs[IDX['P']] = p

        vap_outputs[IDX['CO2']] = co2_vap
        vap_outputs[IDX['H2O']] = h2o_vap

        aq_outputs[IDX['T']] = t
        aq_outputs[IDX['P']] = p
        aq_outputs[IDX['CO2']] = co2_liq
        aq_outputs[IDX['H2O']] = h2o - h2o_vap

        if input_type == 'with naoh':
            aq_outputs[IDX['NaOH']] = naoh
            for s in SOL_SPECIES:
                aq_outputs[IDX[s]] = inputs[IDX[s]]

        return vap_outputs, aq_outputs

    def handle_hs_output(self, inputs, input_type, ann_outputs, t, p, co2, h2o, naoh, n_total):
        # ann_outputs: ['entropy', 'dH_approx']
        # molar amount co2_aq is approx molar amount naoh
        h0 = co2 * REF_STATE_HS['CO2']['Hf298'] + h2o * REF_STATE_HS['H2O']['Hf298'] + \
                   naoh * REF_STATE_HS['NaOH']['Hf298']

        dh = ann_outputs[1] * n_total
        enthalpy = h0 + dh
        # print(t, p, co2 / (co2 + h2o), naoh / (h2o * MOLAR_MASS['H2O']))
        # print('t, p, h_aproxm dH_approx, enthalpy', t, p, h_approx/n_total, ann_outputs[1], enthalpy / n_total)
        outputs = list(inputs)
        # VLE properties from ANN
        outputs[IDX['enthalpy_vle']] = enthalpy
        outputs[IDX['entropy_vle']] = ann_outputs[0] * n_total

        if input_type == 'with naoh':
            s_outputs = []
            for s in SOL_SPECIES:
                s_outputs.append(inputs[IDX[s]])
            outputs[IDX['enthalpy_s']] = self.enthalpy_solids(outputs[IDX['T']], np.array(s_outputs))

        return outputs

    def enthalpy_solids(self, t, solids):
        # A, B, C, D, Hf are defined in c1_constants
        t_ref = 298.15
        t = maingopy.pos(t) if self.model.get_equations else t
        h = A_SOLID * (t - t_ref) + 0.5 * B_SOLID * (t ** 2 - t_ref ** 2) + C_SOLID * (
                    1 / t_ref - 1 / t) + 2 * D_SOLID * (
                    t ** 0.5 - t_ref ** 0.5)
        enthalpy_s = np.sum(np.dot(solids, h + Hf_SOLID))
        return enthalpy_s

    def evaluate(self, ann_type, inputs, input_type):
        if ann_type == 'vle':
            if input_type == 'with naoh':
                ann_type = VLE_TYPE_WITH_NaOH
            elif input_type == 'no naoh':
                ann_type = VLE_TYPE_NO_NaOH
            vap_output, aq_output, ineqs_vle = self.run_ann(inputs, ann_type=ann_type, input_type=input_type)
            vap_output_complete, ineqs_vap = self.run_ann(vap_output, ann_type='HS', input_type='no naoh') # there is never NaOH in vapor
            aq_output_complete, ineqs_aq = self.run_ann(aq_output, ann_type='HS', input_type=input_type)
            ineqs = ineqs_vle + ineqs_vap + ineqs_aq
            return [vap_output_complete, aq_output_complete], ineqs
        elif ann_type == 'HS':
            output, ineqs = self.run_ann(inputs, ann_type='HS', input_type=input_type)
            return [output], ineqs
        else:
            raise Exception(f'ann type cant be {ann_type}')
