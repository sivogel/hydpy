# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# import...
# ...from HydPy
from hydpy.core import sequencetools


class Precipitation(sequencetools.InputSequence):
    """Precipitation [mm]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.PRECIPITATION


class Evaporation(sequencetools.InputSequence):
    """Potential evaporation [mm]."""

    NDIM, NUMERIC = 0, False
    STANDARD_NAME = sequencetools.StandardInputNames.EVAPOTRANSPIRATION
