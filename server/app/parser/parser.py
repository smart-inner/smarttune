from app.types import UnitType
from app.utils import *

class Parser:
    def __init__(self, system_id):
        self.system_id = system_id
        self.valid_true_val = ("on", "true", "yes")
        self.valid_false_val = ("off", "false", "no")

    def parse_system_variables(self, variables):
        valid_variables = {}
        for scope, sub_vars in variables.items():
            if sub_vars is None:
                continue
            if scope == 'global' or scope == 'local':
                for var_name, var_value in sub_vars.items():
                    full_name = scope + '.' + var_name
                    if full_name not in valid_variables:
                        valid_variables[full_name] =[]
                    valid_variables[full_name].append(var_value)
            else:
                raise Exception('Unsupported variable scope: %s' % scope)
        return valid_variables

    def extract_valid_variables(self, variables, catalog, default_value=None):
        valid_variables = {}
        lc_catalog = {k.lower(): v for k, v in catalog.items()}

        for var_name, var_value in variables.items():
            if var_name in catalog:
                valid_variables[var_name] = var_value
            else:
                lc_var_name = var_name.lower()
                if lc_var_name in lc_catalog:
                    valid_name = lc_catalog[lc_var_name].name
                    valid_variables[valid_name] = var_value
        
        lc_variables = {k.lower() for k in variables.keys()}
        for valid_lc_name, metadata in lc_catalog.items():
            if valid_lc_name not in lc_variables:
                valid_variables[metadata.name] = default_value if \
                    default_value is not None else metadata.default
        assert len(valid_variables) == len(catalog)
        return valid_variables

    def convert_bool(self, bool_value, metadata):
        if isinstance(bool_value, str):
            bool_value = bool_value.lower()

        if bool_value in self.valid_true_val:
            res = int(True)
        elif bool_value in self.valid_false_val:
            res = int(False)
        else:
            raise Exception("Invalid boolean value for variable {} ({})".format(
                metadata.name, bool_value))

        return res

    def convert_enum(self, enum_value, metadata):
        enumvals = metadata.enumvals.split(',')
        lower_enumvals = [ev.lower() for ev in enumvals]
        lower_enum_value = enum_value.lower()
        try:
            res = lower_enumvals.index(lower_enum_value)
        except ValueError:
            raise Exception('Invalid enum value for variable {} ({})'.format(
                metadata.name, enum_value))

        return res

    def convert_integer(self, int_value, metadata):
        if str(int_value) == 'null' or len(str(int_value)) == 0:
            return 0
        try:
            try:
                converted = int(int_value)
            except ValueError:
                converted = int(float(int_value))
        except ValueError:
            if metadata.unit == UnitType.BYTES.value:
                converted = Conversion.get_raw_size(
                    int_value, Conversion.DEFAULT_BYTES_SYSTEM)
            elif metadata.unit == UnitType.MILLISECONDS.value:
                converted = Conversion.get_raw_size(
                    int_value, Conversion.DEFAULT_TIME_SYSTEM)
            else:
                converted = None
        if converted is None:
            raise Exception('Cannot convert knob {} from {} to integer'.format(
                metadata.name, int_value))
        
        return converted

    def convert_real(self, real_value, metadata):
        try:
            return float(real_value)
        except ValueError:
            raise Exception('Cannot convert knob {} from {} to float'.format(
                metadata.name, real_value))
