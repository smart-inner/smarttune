from app.models import KnobCatalog
from .parser import Parser
from app.types import VarType

class KnobParser(Parser):
    def __init__(self, system_id):
        super().__init__(system_id)

    def parse_system_knobs(self, knobs):
        valid_knobs = self.parse_system_variables(knobs)
        for key in valid_knobs.keys():
            assert len(valid_knobs[key]) == 1
            valid_knobs[key] = valid_knobs[key][0]
        knob_catalog = {knob.name: knob for knob in KnobCatalog.query.filter(KnobCatalog.system_id == self.system_id)}
        return self.extract_valid_variables(valid_knobs, knob_catalog)

    def check_knob_bool_val(self, value):
        if isinstance(value, str):
            value = value.lower()
        return value in self.valid_true_val or value in self.valid_false_val
    
    def check_knob_value_in_range(self, value, metadata):
        if metadata.min_val is None or metadata.max_val is None:
            return True
        min_val = float(metadata.min_val)
        max_val = float(metadata.max_val)
        return min_val <= float(value) <= max_val

    def convert_system_knobs(self, knobs, knob_catalog=None):
        knob_data = {}
        if knob_catalog is None:
            filters = {
                KnobCatalog.system_id == self.system_id,
                KnobCatalog.tunable == True
            }
            knob_catalog = KnobCatalog.query().filter(*filters).all()
        
        for metadata in knob_catalog:
            name = metadata.name
            if name not in knobs:
                continue
            value = knobs[name]
            conv_value = None

            if metadata.var_type == VarType.BOOL.value:
                if not self.check_knob_bool_val(value):
                    raise Exception("Knob '%s' boolean value not valid!" % name)
                conv_value = self.convert_bool(value, metadata)
            elif metadata.var_type == VarType.ENUM.value:
                conv_value = self.convert_enum(value, metadata)
            elif metadata.var_type == VarType.INTEGER.value:
                conv_value = self.convert_integer(value, metadata)
                if not self.check_knob_value_in_range(conv_value, metadata):
                    raise Exception("Knob '%s' integer value not in range, min: %s, max: %s, "
                                    "actual: %s" % (name, metadata.min_val, metadata.max_val, str(conv_value)))
            elif metadata.var_type == VarType.REAL.value:
                conv_value = self.convert_real(value, metadata)
                if not self.check_knob_value_in_range(conv_value, metadata):
                    raise Exception("Knob '%s' real value not in range, min: %s, max: %s, "
                                    "actual: %s" % (name, metadata.min_val, metadata.max_val, str(conv_value)))
            elif metadata.var_type == VarType.STRING.value or metadata.var_type == VarType.TIEMSTAMP.value:
                conv_value = value
            else:
                raise Exception('Unknown variable type: %s' % metadata.var_type)

            if conv_value is None:
                raise Exception("Param value for '%s' cannot be null" % name)
            knob_data[name] = conv_value

        return knob_data
