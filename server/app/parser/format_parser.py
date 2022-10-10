from .parser import Parser
from app.models import KnobCatalog
from app.types import VarType
from collections import OrderedDict

class FormatParser(Parser):
    def __init__(self, system_id):
        super().__init__(system_id)

    def format_system_knobs(self, knobs):
        formatted_knobs = {}
        for knob_name, knob_value in list(knobs.items()):
            filters = {
                KnobCatalog.system_id == self.system_id,
                KnobCatalog.name == knob_name
            }
            metadata = KnobCatalog.query.filter(*filters).first()
            fvalue = None
            if metadata.var_type == VarType.ENUM.value:
                fvalue = self.format_enum(knob_value, metadata)
            elif metadata.var_type == VarType.INTEGER.value:
                fvalue = self.format_integer(knob_value, metadata)
            elif metadata.var_type == VarType.REAL.value:
                fvalue = self.format_real(knob_value)
            elif metadata.var_type == VarType.STRING.value:
                fvalue = self.format_string(knob_value)
            elif metadata.var_type == VarType.TIMESTAMP.value:
                fvalue = self.format_timestamp(knob_value)
            else:
                raise Exception('Unknown variable type for {}: {}'.format(
                    knob_name, metadata.var_type))
            if fvalue is None:
                raise Exception('Cannot format value for {}: {}'.format(
                    knob_name, knob_value))
            formatted_knobs[knob_name] = fvalue
        return formatted_knobs

    def create_knob_configuration(self, tuning_knobs):
        configuration = {}
        for knob_name, knob_value in sorted(tuning_knobs.items()):
            if knob_name.startswith('global.'):
                knob_name_global = knob_name[knob_name.find('.') + 1:]
                configuration[knob_name_global] = knob_value

        configuration = OrderedDict(sorted(configuration.items()))
        return configuration