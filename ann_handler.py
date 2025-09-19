from get_min_max import *
from constants.c1_constants import *


class AnnHandler:
    def __init__(self, model):
        self.model = model
        self.anns = {}
        self.input_bounds = {}
        self.load_models_and_bounds()

    def load_models_and_bounds(self):
        for ann_type in ['vle', 'hs']:
            self.anns[ann_type] = dict()
            self.input_bounds[ann_type] = dict()
            for input_type in ['with naoh', 'no naoh']:
                for range_type in ['high pressure', 'low pressure']:
                    ann = maingopy.melonpy.FeedForwardNet()
                    ann.load_model(NN_DIR, f'{ANN_FILES[ann_type][input_type]}.xml', maingopy.melonpy.XML)
                    self.anns[ann_type][input_type] = ann
                    self.input_bounds[ann_type][input_type] = get_min_max(ANN_FILES[ann_type][input_type])


    def get_stream_specs(self, inputs, input_type):
        t = inputs[IDX['T']]
        p = inputs[IDX['P']]
        co2 = inputs[IDX['CO2']]
        h2o = inputs[IDX['H2O']]
        naoh = inputs[IDX['NaOH']]
        n_total = co2 + h2o + naoh

        if self.model.get_equations:
            co2_frac = co2 / maingopy.pos((co2 + h2o))
            if input_type == 'with naoh':
                molality = naoh / maingopy.pos((h2o * MOLAR_MASS['H2O']))
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
        if ann_type == 'vle':
            # inverse log transform y_h2o
            scaled[0] = 10 ** scaled[0] - 1e-16
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
        if ann_type == 'vle':
            vap_out, aq_out = self.handle_vle_output(inputs, input_type, ann_outputs, t, p, co2, h2o, naoh, n_total)
            return vap_out, aq_out, ineqs
        elif ann_type == 'hs':
            outputs = self.handle_hs_output(inputs, input_type, ann_outputs, n_total)
            return outputs, ineqs

    # the inequalities are the bounds of the ann_inputs, for which the network is trained
    def get_ineqs_and_ann_inputs(self, ann_type, input_type, t, p, co2, h2o, naoh, co2_frac, molality):
        min_in = self.input_bounds[ann_type][input_type]['min_in']
        max_in = self.input_bounds[ann_type][input_type]['max_in']

        t_ineq_min = min_in[0] - t
        t_ineq_max = t - max_in[0]
        p_ineq_min = min_in[1] - p
        p_ineq_max = p - max_in[1]
        co2_ineq = -co2
        h2o_ineq = -h2o
        naoh_ineq = -naoh
        co2_frac_ineq_min = min_in[2] - co2_frac
        co2_frac_ineq_max = co2_frac - max_in[2]

        ineqs = [t_ineq_min, t_ineq_max, p_ineq_min, p_ineq_max, co2_ineq, h2o_ineq, naoh_ineq]
        # ineqs = [t_ineq_min, t_ineq_max, p_ineq_min, p_ineq_max, co2_frac_ineq_min, co2_frac_ineq_max, co2_ineq, h2o_ineq, naoh_ineq]

        if input_type == 'with naoh':
            molality_ineq_min = min_in[3] - molality
            molality_ineq_max = molality - max_in[3]
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

    def handle_vle_output(self, inputs, input_type, ann_outputs, t, p, co2, h2o, naoh, n_total):
        # ann_outputs: ['Y_H2O', 'X_CO2', 'vapor fraction', 'enthalpy']
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

    def handle_hs_output(self, inputs, input_type, ann_outputs, n_total):
        # ann_outputs: ['enthalpy', 'entropy']
        outputs = list(inputs)
        # VLE properties from ANN
        outputs[IDX['enthalpy_vle']] = ann_outputs[0] * n_total
        outputs[IDX['entropy_vle']] = ann_outputs[1] * n_total

        if input_type == 'with naoh':
            s_outputs = []
            for s in SOL_SPECIES:
                s_outputs.append(inputs[IDX[s]])
            outputs[IDX['enthalpy_s']] = self.enthalpy_solids(outputs[IDX['T']], np.array(s_outputs))

        return outputs

    def enthalpy_solids(self, t, solids):
        t_ref = 298.15
        t = maingopy.pos(t) if self.model.get_equations else t
        h = A * (t - t_ref) + 0.5 * B * (t ** 2 - t_ref ** 2) + C * (1 / t_ref - 1 / t) + 2 * D * (
                t ** 0.5 - t_ref ** 0.5)
        enthalpy_s = np.sum(np.dot(solids, h + Hf))
        return enthalpy_s

    def evaluate(self, ann_type, inputs, input_type):
        if ann_type == 'vle':
            vap_output, aq_output, ineqs_vle = self.run_ann(inputs, ann_type='vle', input_type=input_type)
            vap_output_complete, ineqs_vap = self.run_ann(vap_output, ann_type='hs', input_type=input_type)
            aq_output_complete, ineqs_aq = self.run_ann(aq_output, ann_type='hs', input_type=input_type)
            ineqs = ineqs_vle + ineqs_vap + ineqs_aq
            return [vap_output_complete, aq_output_complete], ineqs
        elif ann_type == 'hs':
            output, ineqs = self.run_ann(inputs, ann_type='hs', input_type=input_type)
            return [output], ineqs
        else:
            raise Exception(f'ann type must be vle or hs not {ann_type}')
