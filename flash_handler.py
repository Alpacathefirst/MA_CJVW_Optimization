from get_min_max import *
from constants.constants import *


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
        # [0, 1, 2      , 3     , 4      , 5           , 6     , 7    , 8     , 9      , 10         , 11       , 12        , 13      , 14              , 15        ]
        # [T, P, CO2_vap, N2_vap, H2O_vap, enthalpy_vap, CO2_aq, N2_aq, H2O_aq, NaOH_aq, enthalpy_aq, Magnesite, Forsterite, Fayalite, Amorphous_Silica, enthalpy_s]
        ann_inputs = np.array([inputs[0],  # T
                               inputs[1],  # P
                               inputs[2] + inputs[6],  # CO2_frac = CO2 / (CO2 + H2O)
                               inputs[3] + inputs[7],  # NaOH
                               inputs[4] + inputs[8],  # H2O
                               inputs[9]  # NaOH
                               ])
        # Reduce to 1 mol total species amount (ANN is trained for this)
        eps = 1e-8
        n_in_total = ann_inputs[2] + ann_inputs[3] + ann_inputs[4] + ann_inputs[5] + eps
        # when running the optimization make sure n_total is strictly positive
        if self.model.get_equations:
            n_in_total = maingopy.pos(n_in_total)
        ann_inputs_reduced = np.array([
            ann_inputs[0],  # T
            ann_inputs[1],  # P
            ann_inputs[2] / n_in_total,  # CO2
            ann_inputs[3] / n_in_total,  # N2
            ann_inputs[4] / n_in_total,  # H2O
            ann_inputs[5] / n_in_total  # NaOH
        ])

        # when just evaluating the model, the FFNN needs to return doubles not FFVars, his is done by loading the NN
        # differently
        if not self.model.get_equations:
            self.pt_flash = maingopy.melonpy.FeedForwardNetDouble(self.full_path, maingopy.melonpy.MODEL_FILE_TYPE.XML)
        # ann_inputs: [T, P, CO2, N2, H2O, NaOH]
        # scale the ann inputs between 0 and 1
        ann_inputs_scaled = self.scale_input(np.array(ann_inputs_reduced), self.pt_file)
        # Evaluate the network (in reduced-space)
        ann_outputs = self.pt_flash.calculate_prediction_reduced_space(ann_inputs_scaled)
        ann_outputs = self.inverse_scale_output(np.array(ann_outputs), self.pt_file)
        # ann_outputs: ['A_CO2', 'A_H2O', 'A_N2', 'enthalpy_vapor', 'enthalpy]  # TODO: Change order N2, H2O
        # inputs = [T, P, CO2, N2, H2O, NaOH]
        # [0, 1, 2      , 3     , 4      , 5           , 6     , 7    , 8     , 9      , 10         , 11       , 12        , 13      , 14              , 15        ]
        # [T, P, CO2_vap, N2_vap, H2O_vap, enthalpy_vap, CO2_aq, N2_aq, H2O_aq, NaOH_aq, enthalpy_aq, Magnesite, Forsterite, Fayalite, Amorphous_Silica, enthalpy_s]
        vap_out = [ann_inputs[0],  # T
                   ann_inputs[1],  # P
                   ann_inputs[2] * (1 - ann_outputs[0]),  # CO2_vap
                   ann_inputs[3] * (1 - ann_outputs[2]),  # N2_vap # TODO: Change order N2, H2O
                   ann_inputs[4] * ann_outputs[1],  # H2O_vap # TODO: Change order N2, H2O
                   ]

        enthalpy_vap = ann_outputs[3] * (vap_out[2] + vap_out[3] + vap_out[4])
        vap_out.append(enthalpy_vap)

        aq_out = [ann_inputs[2] - vap_out[2],  # CO2_aq
                  ann_inputs[3] - vap_out[3],  # N2_aq
                  ann_inputs[4] - vap_out[4],  # H2O_aq
                  ann_inputs[5],  # NaOH_aq
                  ann_outputs[4] * n_in_total - vap_out[5]  # enthalpy aq
                  ]

        # the solid amounts didnt change
        s_out = inputs[11:15]
        h_s = np.array([self.enthalpy_solids(inputs[0], s_out)])
        outputs = np.concatenate([np.array(vap_out), np.array(aq_out), s_out, h_s])
        return outputs

    def enthalpy_solids(self, t, solids):
        t_ref = 298.15
        h = A * (t - t_ref) + 0.5 * B * (t ** 2 - t_ref ** 2) + C * (1 / t_ref - 1 / t) + 2 * D * (
                    t ** 0.5 - t_ref ** 0.5)
        enthalpy_s = np.sum(np.dot(solids, h+Hf))
        return enthalpy_s
