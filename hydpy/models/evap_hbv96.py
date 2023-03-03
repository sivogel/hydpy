# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""Implementation of the potential evapotranspiration routines of HBV96
:cite:p:`ref-Lindstrom1997HBV96`.

The primary purpose of |evap_hbv96| is to serve as a submodel that provides estimates
of potential evapotranspiration.  Of course, you can connect it to |hland_v1| if you
long for a close HBV96 emulation, but it also works with other main models like
|lland_v1| or |wland_v001|.

|evap_hbv96| itself requires another model for determining precipitation.  By
default, it queries the already available precipitation from its main model.
Alternatively, it can handle its own submodel.  The following tests rely on the latter
option.

Integration tests
=================

.. how_to_understand_integration_tests::

According to the intended usage as a submodel, |evap_hbv96| requires no connections to
any nodes.  Hence, assigning a model instance to a blank |Element| instance is
sufficient:

>>> from hydpy import Element
>>> from hydpy.models.evap_hbv96 import *
>>> parameterstep("1h")
>>> element = Element("element")
>>> element.model = model

We perform the integration test for a single simulation step, the first hour of the
second day of the simulation period selected for the integration tests of |hland_v1|:

>>> from hydpy import IntegrationTest, pub
>>> pub.timegrids = "2000-01-02 00:00", "2000-01-02 01:00", "1h"

We set all parameter values identical to the ones defined in the :ref:`hland_v1_field`
example of |hland_v1|:

>>> nmbhru(1)
>>> hruarea(1.0)
>>> hrualtitude(100.0)
>>> evapotranspirationfactor(0.7)
>>> airtemperaturefactor(0.1)
>>> altitudefactor(-0.1)
>>> precipitationfactor(0.1)

A |meteo_precip_io| submodel provides the required precipitation:

>>> with model.add_precipmodel_v2("meteo_precip_io"):
...     precipitationfactor(1.0)

Now we can initialise an |IntegrationTest| object:

>>> test = IntegrationTest(element)
>>> test.dateformat = "%d/%m %H:00"

The following meteorological input also stems from the input data of the
:ref:`hland_v1_field` example:

>>> inputs.airtemperature.series = 19.2
>>> inputs.normalairtemperature.series = 18.2
>>> inputs.normalevapotranspiration.series = 0.097474

The following precipitation value is from the results table of the
:ref:`hland_v1_field` example:

>>> model.precipmodel.sequences.inputs.precipitation.series = 0.847

The following simulation results contain the calculated reference and potential
evapotranspiration.  Reference evapotranspiration is not available in the results of
the :ref:`hland_v1_field` example of |hland_v1|.  The potential evapotranspiration
estimate is the same in both tables:

.. integration-test::

    >>> test()
    |        date | airtemperature | normalairtemperature | normalevapotranspiration | precipitation | referenceevapotranspiration | potentialevapotranspiration | meanpotentialevapotranspiration |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 02/01 00:00 |           19.2 |                 18.2 |                 0.097474 |         0.847 |                    0.075055 |                     0.06896 |                         0.06896 |
"""
# import...
# ...from HydPy
from hydpy.core import modeltools
from hydpy.exe.modelimports import *
from hydpy.interfaces import precipinterfaces
from hydpy.models.evap import evap_model


class Model(
    evap_model.Main_PrecipModel_V1,
    evap_model.Main_PrecipModel_V2,
    evap_model.Sub_PETModel_V1,
):
    """The HBV96 version of HydPy-Evap."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        evap_model.Calc_Precipitation_V1,
        evap_model.Calc_ReferenceEvapotranspiration_V5,
        evap_model.Adjust_ReferenceEvapotranspiration_V1,
        evap_model.Calc_PotentialEvapotranspiration_V3,
        evap_model.Calc_MeanPotentialEvapotranspiration_V1,
    )
    INTERFACE_METHODS = (
        evap_model.Determine_PotentialEvapotranspiration_V1,
        evap_model.Get_PotentialEvapotranspiration_V2,
        evap_model.Get_MeanPotentialEvapotranspiration_V2,
    )
    ADD_METHODS = (
        evap_model.Calc_Precipitation_PrecipModel_V1,
        evap_model.Calc_Precipitation_PrecipModel_V2,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        precipinterfaces.PrecipModel_V1,
        precipinterfaces.PrecipModel_V2,
    )
    SUBMODELS = ()

    precipmodel = modeltools.SubmodelProperty(
        precipinterfaces.PrecipModel_V1, precipinterfaces.PrecipModel_V2
    )


tester = Tester()
cythonizer = Cythonizer()
