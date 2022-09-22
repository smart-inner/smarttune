class ConversionUtil(object):

    DEFAULT_BYTES_SYSTEM = (
        (1024 ** 5, ['PB', 'PiB']),
        (1024 ** 4, ['TB', 'TiB']),
        (1024 ** 3, ['GB', 'GiB']),
        (1024 ** 2, ['MB', 'MiB']),
        (1024 ** 1, ['KB', 'KiB']),
        (1024 ** 0, ['B']),
    )

    DEFAULT_TIME_SYSTEM = (
        (1000 * 60 * 60 * 24, ['d']),
        (1000 * 60 * 60, ['h']),
        (1000 * 60, ['min', 'm']),
        (1000, ['s']),
        (1, ['ms']),
    )

    @staticmethod
    def get_raw_size(value, system):
        for factor, suffixs in system:
            for suffix in suffixs:
                if value.endswith(suffix):
                    if len(value) == len(suffix):
                        amount = 1
                    else:
                        try:
                            amount = int(value[:-len(suffix)])
                        except ValueError:
                            continue
                    return amount * factor
        return None