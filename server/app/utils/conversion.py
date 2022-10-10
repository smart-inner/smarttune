import math

class Conversion(object):
    @staticmethod
    def get_raw_size(value, system):
        for suffix, factor in system.items():
            if value.endswith(suffix):
                if len(value) == len(suffix):
                    amount = 1
                else:
                    try:
                        amount = int(value[:-len(suffix)])
                    except ValueError:
                        continue
                return amount * eval(factor)
        return None
    
    @staticmethod
    def get_human_readable(value, system, min_suffix):
        # Converts the value to larger units only if there is no loss of resolution.
        min_factor = None
        unit = None
        mod_system = []
        for suffix, factor in system.items():
            if suffix == min_suffix:
                if value < eval(factor):
                    return value
                min_factor = eval(factor)
                unit = min_suffix
                value = math.floor(float(value) / min_factor)
                break
            mod_system.append((eval(factor), suffix))

        if min_factor is None:
            raise ValueError('Invalid min suffix for system: suffix={}, system={}'.format(
                min_suffix, system))

        for factor, suffix in mod_system:
            adj_factor = factor / min_factor
            if value % adj_factor == 0:
                value = math.floor(float(value) / adj_factor)
                unit = suffix
                break
            if value / adj_factor > 100:
                value = round(value / adj_factor)
                unit = suffix
                break

        return '{}{}'.format(int(value), unit)