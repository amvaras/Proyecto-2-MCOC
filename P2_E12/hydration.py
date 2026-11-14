"""Una curva del archivo docente, con integración exacta por tramos."""

import re

import numpy as np

from mcoc_p2.e07.hydration import AdiabaticCurve


def read_curve(path, column):
    columns = {}
    with path.open(encoding="utf-8-sig") as stream:
        for line in stream:
            if not line.startswith("#"):
                break
            match = re.match(r"^#\s+(\d+)\s+(M\d+_\w+_W_m3)\s", line)
            if match:
                columns[match[2]] = int(match[1]) - 1
    if column not in columns:
        raise ValueError(f"Columna de hidratación desconocida: {column}")
    hours, power = np.loadtxt(path, usecols=(0, columns[column]), unpack=True)
    valid = np.flatnonzero(np.isfinite(power))
    if (len(valid) < 2 or not np.array_equal(valid, np.arange(len(valid)))
            or not np.isnan(power[len(valid):]).all()):
        raise ValueError("La curva permite NaN únicamente al final del registro")
    return TabulatedCurve(hours[valid] * 3600, power[valid])


class TabulatedCurve(AdiabaticCurve):
    def __init__(self, seconds, power):
        time = np.array(seconds, dtype=float)
        source = np.array(power, dtype=float)
        widths = np.diff(time)
        if (time.ndim != 1 or source.shape != time.shape or len(time) < 2 or time[0] != 0
                or not np.isfinite(time).all() or not np.isfinite(source).all()
                or np.any(widths <= 0) or np.any(source < 0)):
            raise ValueError("Se requiere una curva finita, creciente en tiempo y con fuente no negativa")
        cumulative = np.r_[0., np.cumsum(widths * (source[:-1] + source[1:]) / 2)]
        super().__init__(float(cumulative[-1]), float(time[-1]))
        time.flags.writeable = source.flags.writeable = cumulative.flags.writeable = False
        object.__setattr__(self, "_time", time)
        object.__setattr__(self, "_power", source)
        object.__setattr__(self, "_cumulative", cumulative)

    def source(self, age_s):
        age = np.asarray(age_s, dtype=float)
        if not np.isfinite(age).all():
            raise ValueError("Edad finita")
        return np.interp(age, self._time, self._power, left=0., right=0.)

    def _integral(self, age_s):
        age = np.asarray(age_s, dtype=float)
        if not np.isfinite(age).all():
            raise ValueError("Edad finita")
        age = np.clip(age, 0., self.duration_s)
        i = np.clip(np.searchsorted(self._time, age, side="right") - 1, 0, len(self._time) - 2)
        elapsed = age - self._time[i]
        return self._cumulative[i] + elapsed * (self._power[i] + self.source(age)) / 2

    def released(self, age0_s, age1_s):
        if np.any(np.asarray(age1_s) < np.asarray(age0_s)):
            raise ValueError("Edades deben aumentar")
        return self._integral(age1_s) - self._integral(age0_s)

    def degree(self, age_s):
        return self._integral(age_s) / self.H_vol_J_m3 if self.H_vol_J_m3 else self._integral(age_s)
