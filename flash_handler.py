from get_min_max import *
from constants.c1_constants import *


class FlashHandler:
    def __init__(self, model):
        self.pt_file = PT_FILE
        self.dir = "inputs/d6_trained_nn"
        self.full_path = f'inputs\\d6_trained_nn\\{self.pt_file}.xml'
        self.model = model
        self.pt_flash = maingopy.melonpy.FeedForwardNet()
        # open (define that it is an XML instead of a CSV)
        self.pt_flash.load_model(self.dir, f'{self.pt_file}.xml', maingopy.melonpy.XML)
        self.min_in, self.max_in, self.min_out, self.max_out = dict(), dict(), dict(), dict()
        self.min_in[self.pt_file], self.max_in[self.pt_file], self.min_out[self.pt_file], self.max_out[
            self.pt_file] = get_min_max(self.pt_file)

    def scale_input(self, unscaled, f):
        return 2 * (unscaled - self.min_in[f]) / (self.max_in[f] - self.min_in[f]) - 1

    def inverse_scale_output(self, scaled, f):
        return 0.5 * (scaled + 1) * (self.max_out[f] - self.min_out[f]) + self.min_out[f]

    def evaluate_pt_flash(self, inputs):
        co2 = inputs[IDX['CO2_vap']] + inputs[IDX['CO2_aq']]
        h2o = inputs[IDX['H2O_vap']] + inputs[IDX['H2O_aq']]
        naoh = inputs[IDX['NaOH_aq']]

        co2_frac = co2 / maingopy.pos((co2 + h2o))
        molality = naoh / maingopy.pos((h2o * MOLAR_MASS_WATER))
        ann_inputs = np.array([inputs[IDX['T']],  # T
                               inputs[IDX['P']],  # P
                               co2_frac,  # CO2_frac = CO2 / (CO2 + H2O)
                               molality,  # Molality = NaOH / (H2O * molar mass)
                               ])
        # when just evaluating the model, the FFNN needs to return doubles not FFVars, his is done by loading the NN
        # differently
        if not self.model.get_equations:
            co2_frac = co2 / (co2 + h2o)
            molality = naoh / (h2o * MOLAR_MASS_WATER + EPSILON)
            ann_inputs = [inputs[IDX['T']],  # T
                          inputs[IDX['P']],  # P
                          co2_frac,  # CO2_frac = CO2 / (CO2 + H2O)
                          molality,  # Molality = NaOH / (H2O * molar mass)
                          ]
            self.pt_flash = maingopy.melonpy.FeedForwardNetDouble(self.full_path, maingopy.melonpy.MODEL_FILE_TYPE.XML)
        # ann_inputs: [T, P, CO2_frac, molality]
        # scale the ann inputs between 0 and 1
        ann_inputs_scaled = self.scale_input(ann_inputs, self.pt_file)
        # Evaluate the network (in reduced-space)
        ann_outputs = self.pt_flash.calculate_prediction_reduced_space(ann_inputs_scaled)
        # scale the outputs back
        ann_outputs = self.inverse_scale_output(np.array(ann_outputs), self.pt_file)
        # ann_outputs: ['A_CO2', 'A_H2O', 'enthalpy', 'entropy']

        co2_vap = co2 * (1 - ann_outputs[0])
        h2o_vap = h2o * ann_outputs[1]

        # recreate the complete output array
        outputs = [0] * len(NAMES)
        outputs[IDX['T']] = inputs[IDX['T']]
        outputs[IDX['P']] = inputs[IDX['P']]
        outputs[IDX['CO2_vap']] = co2_vap
        outputs[IDX['N2_vap']] = inputs[IDX['N2_vap']]  # TODO: implement Henries law for N2
        outputs[IDX['H2O_vap']] = h2o_vap
        outputs[IDX['CO2_aq']] = co2 - co2_vap
        outputs[IDX['N2_aq']] = inputs[IDX['N2_aq']]  # unchanged for now
        outputs[IDX['H2O_aq']] = h2o - h2o_vap
        outputs[IDX['NaOH_aq']] = inputs[IDX['NaOH_aq']]

        n_total = co2 + h2o + naoh
        # VLE properties from ANN
        outputs[IDX['enthalpy_vle']] = ann_outputs[2] * n_total
        outputs[IDX['entropy_vle']] = ann_outputs[3] * n_total

        s_outputs = []
        for s in SOL_SPECIES:
            outputs[IDX[s]] = inputs[IDX[s]]
            s_outputs.append(inputs[IDX[s]])

        outputs[IDX['enthalpy_s']] = self.enthalpy_solids(outputs[IDX['T']], np.array(s_outputs))
        #
        # print('inputs:\n',inputs)
        # print('ann_inputs: \n', ann_inputs)
        # print('ann_outputs: \n', ann_outputs)
        # print('outputs: \n', outputs)
        return np.array(outputs)

    def enthalpy_solids(self, t, solids):
        t_ref = 298.15
        h = A * (t - t_ref) + 0.5 * B * (t ** 2 - t_ref ** 2) + C * (1 / t_ref - 1 / t) + 2 * D * (
                t ** 0.5 - t_ref ** 0.5)
        enthalpy_s = np.sum(np.dot(solids, h + Hf))
        return enthalpy_s
