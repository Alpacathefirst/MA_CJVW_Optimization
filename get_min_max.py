import joblib


def get_min_max(file):
    transformer_dir = f'inputs\\d7_trained_nn_transformers\\{file}'

    minmax_inp = joblib.load(f'{transformer_dir}\\minmax_inp')
    minmax_out = joblib.load(f'{transformer_dir}\\minmax_out')

    inp_min = minmax_inp.data_min_
    inp_max = minmax_inp.data_max_

    out_min = minmax_out.data_min_
    out_max = minmax_out.data_max_

    return inp_min, inp_max, out_min, out_max
