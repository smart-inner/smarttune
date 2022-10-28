from app.types import UnitType
from app.utils import *
from app.models import *

class Parser:
    def __init__(self, system_id):
        self.system_id = system_id
        self.conversion_system = json.loads(
            SystemCatalog.query.filter(SystemCatalog.id == self.system_id).first().conversion)

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

    def convert_enum(self, enum_value, metadata):
        enum_vals = metadata.enum_vals.split(',')
        lower_enum_vals = [ev.lower() for ev in enum_vals]
        lower_enum_value = enum_value.lower()
        try:
            res = lower_enum_vals.index(lower_enum_value)
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
                    int_value, self.conversion_system['BYTES_SYSTEM'])
            elif metadata.unit == UnitType.MILLISECONDS.value:
                converted = Conversion.get_raw_size(
                    int_value, self.conversion_system['TIME_SYSTEM'])
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

    def format_enum(self, enum_value, metadata):
        enum_vals = metadata.enum_vals.split(',')
        if "false" in enum_vals and "true" in enum_vals:
            return True if enum_vals[int(round(enum_value))] == 'true' else False
        return enum_vals[int(round(enum_value))]

    def format_integer(self, int_value, metadata):
        int_value = int(round(int_value))
        if metadata.unit != UnitType.OTHER.value and int_value > 0:
            if metadata.unit == UnitType.BYTES.value:
                int_value = Conversion.get_human_readable(
                    int_value, self.conversion_system['BYTES_SYSTEM'], self.conversion_system['MIN_BYTES_UNIT'])
            elif metadata.unit == UnitType.MILLISECONDS.value:
                int_value = Conversion.get_human_readable(
                    int_value, self.conversion_system['TIME_SYSTEM'], self.conversion_system['MIN_TIME_UNIT'])
            else:
                raise Exception(
                    'Invalid unit type for {}: {}'.format(
                        metadata.name, metadata.unit))

        return int_value

    def format_real(self, real_value):
        value = round(float(real_value), 3)
        if value % 1.0 == 0.0:
            return value + 0.001
        return value

    def format_string(self, string_value):
        return string_value

    def format_timestamp(self, timestamp_value):
        return timestamp_value
