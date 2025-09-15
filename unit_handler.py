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

    def flash(self, name, inputs, input_type, t_out, p_out=None, adiabatic=False):
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

    def splitter(self, name, inputs, input_type, split_factor, t_out=None, p_out=None, adiabatic=False):
        return SplitterUnit(model=self.model, ann_handler=self.ann, name=name, inputs=inputs, input_type=input_type,
                            split_factor=split_factor, t_out=t_out, p_out=p_out, adiabatic=adiabatic).run()
