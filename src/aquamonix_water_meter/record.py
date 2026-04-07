import time


def from_two_words(high16, low16):
    return (high16 << 16) | (low16 & 0xFFFF)


def l_per_sec_to_megs_per_day(in_val):
    return (in_val * 60 * 60 * 24) / 1000000


class Record:
    def __init__(self, register_values):
        self.register_values = register_values
        self.ts = time.time()

    @property
    def total(self):
        on_peak_high = self.register_values[32]
        on_peak_low = self.register_values[33]
        on_peak_result = from_two_words(on_peak_high, on_peak_low)

        off_peak_high = self.register_values[34]
        off_peak_low = self.register_values[35]
        off_peak_result = from_two_words(off_peak_high, off_peak_low)

        return (on_peak_result + off_peak_result) / 1000

    @property
    def current_flow(self):
        return l_per_sec_to_megs_per_day(self.register_values[29])

    @property
    def battery_volts(self):
        return self.register_values[30] / 10

    @property
    def solar_volts(self):
        return self.register_values[31] / 10

    @property
    def is_ready(self):
        return self.register_values[41] == 0
