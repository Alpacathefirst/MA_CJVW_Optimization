from get_min_max import *
from constants.c1_constants import *


# handling prediction of X, Y, vapor fraction
class SHHandler:
    def __init__(self, model):
        self.file = SH_FILE
        self.dir = NN_DIR
        self.full_path = f'{NN_DIR}\{SH_FILE}'
        self.model = model
        self.ann = maingopy.melonpy.FeedForwardNet()
        # open (define that it is an XML instead of a CSV)
        self.ann.load_model(self.dir, f'{self.file}.xml', maingopy.melonpy.XML)
        self.min_in, self.max_in, self.min_out, self.max_out = get_min_max(self.file)
        # track current specie amounts
        self.co2 = 0
        self.h2o = 0
        self.naoh = 0

    def scale_input(self, unscaled):
        return 2 * (unscaled - self.min_in) / (self.max_in - self.min_in) - 1

    def inverse_scale_output(self, unscaled):
        scaled = 0.5 * (unscaled + 1) * (self.max_out - self.min_out) + self.min_out
        return scaled

    def run_flash_ann(self, inputs):
        self.co2 = inputs[IDX['CO2_vap']] + inputs[IDX['CO2_aq']]
        self.h2o = inputs[IDX['H2O_vap']] + inputs[IDX['H2O_aq']]
        self.naoh = inputs[IDX['NaOH_aq']]

        if self.model.get_equations:
            eps = 1e-5
            co2_frac = self.co2 / maingopy.pos((self.co2 + self.h2o) + eps)
            molality = self.naoh / maingopy.pos((self.h2o * MOLAR_MASS['H2O']) + eps)

        # when just evaluating the model, the FFNN needs to return doubles not FFVars, his is done by loading the NN
        # differently. Als can't use maingopy.pos()
        else:
            den1 = self.co2 + self.h2o
            co2_frac = self.co2 / den1 if den1 > 0 else 0.0
            den2 = self.h2o * MOLAR_MASS['H2O']
            molality = self.naoh / den2 if den2 > 0 else 0.0

            self.ann = maingopy.melonpy.FeedForwardNetDouble(self.full_path, maingopy.melonpy.MODEL_FILE_TYPE.XML)

        ann_inputs = [inputs[IDX['T']],  # T
                      inputs[IDX['P']],  # P
                      co2_frac,  # CO2_frac = CO2 / (CO2 + H2O)
                      molality,  # Molality = NaOH / (H2O * molar mass)
                      ]

        ineqs = self.get_inequalities(inputs[IDX['T']], inputs[IDX['P']], co2_frac, molality)

        # ann_inputs: [T, P, CO2_frac, molality]
        # scale the ann inputs between 0 and 1
        ann_inputs_scaled = self.scale_input(np.array(ann_inputs))
        # Evaluate the network (in reduced-space)
        ann_outputs = self.ann.calculate_prediction_reduced_space(ann_inputs_scaled)
        # scale the outputs back
        outputs = self.inverse_scale_output(np.array(ann_outputs))
        return outputs, ineqs

    def evaluate(self, inputs):
        # ann_outputs: ['Y_H2O', 'X_CO2', 'vapor fraction', 'enthalpy']
        ann_outputs, ineqs = self.run_flash_ann(inputs)

        n_total = self.co2 + self.h2o + self.naoh

        # recreate the complete output array
        outputs = [0] * len(NAMES)
        for entry in NAMES:
            outputs[IDX[entry]] = inputs[IDX[entry]]

        # VLE properties from ANN
        outputs[IDX['enthalpy_vle']] = ann_outputs[0] * n_total
        outputs[IDX['entropy_vle']] = ann_outputs[1] * n_total

        s_outputs = []
        for s in SOL_SPECIES:
            s_outputs.append(inputs[IDX[s]])

        outputs[IDX['enthalpy_s']] = self.enthalpy_solids(outputs[IDX['T']], np.array(s_outputs))

        return np.array(outputs), ineqs

    def get_inequalities(self, t, p, co2_frac, molality):
        t_ineq_min = self.min_in[0] - t
        t_ineq_max = t - self.max_in[1]
        p_ineq_min = self.min_in[1] - p
        p_ineq_max = p - self.max_in[1]
        co2_frac_ineq_min = self.min_in[2] - co2_frac
        co2_frac_ineq_max = co2_frac - self.max_in[2]
        molality_ineq_min = self.min_in[3] - molality
        molality_ineq_max = molality - self.max_in[3]
        return [t_ineq_min, t_ineq_max, p_ineq_min, p_ineq_max, co2_frac_ineq_min, co2_frac_ineq_max,
                molality_ineq_min, molality_ineq_max]

    def enthalpy_solids(self, t, solids):
        t_ref = 298.15
        t = maingopy.pos(t) if self.model.get_equations else t
        h = A * (t - t_ref) + 0.5 * B * (t ** 2 - t_ref ** 2) + C * (1 / t_ref - 1 / t) + 2 * D * (
                t ** 0.5 - t_ref ** 0.5)
        enthalpy_s = np.sum(np.dot(solids, h + Hf))
        return enthalpy_s
