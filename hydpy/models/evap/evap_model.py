# -*- coding: utf-8 -*-
# pylint: disable=missing-module-docstring

# imports...
# ...from standard library
import contextlib

# ...from HydPy
from hydpy.core import importtools
from hydpy.core import modeltools
from hydpy.core.typingtools import *
from hydpy.cythons import modelutils
from hydpy.interfaces import petinterfaces
from hydpy.interfaces import precipinterfaces
from hydpy.interfaces import tempinterfaces
from hydpy.models.evap import evap_parameters
from hydpy.models.evap import evap_control
from hydpy.models.evap import evap_derived
from hydpy.models.evap import evap_sequences
from hydpy.models.evap import evap_inputs
from hydpy.models.evap import evap_factors
from hydpy.models.evap import evap_fluxes
from hydpy.models.evap import evap_logs


class Calc_AirTemperature_TempModel_V1(modeltools.Method):
    """Query hydrological response units' air temperature from a main model referenced
    as a sub-submodel and follows the |TempModel_V1| interface.

    Example:

        We use the combination of |hland_v1| and |evap_tw2002| as an example:

        >>> from hydpy.models.hland_v1 import *
        >>> parameterstep()
        >>> area(10.0)
        >>> nmbzones(3)
        >>> zonearea(5.0, 3.0, 2.0)
        >>> zonetype(FIELD)
        >>> zonez(2.0)
        >>> with model.add_petmodel_v1("evap_tw2002"):
        ...     pass
        >>> factors.tc = 2.0, 0.0, 5.0
        >>> model.petmodel.calc_airtemperature_v1()
        >>> model.petmodel.sequences.factors.airtemperature
        airtemperature(2.0, 0.0, 5.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_factors.AirTemperature,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: tempinterfaces.TempModel_V1
    ) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.airtemperature[k] = submodel.get_temperature(k)


class Calc_AirTemperature_TempModel_V2(modeltools.Method):
    """Let a submodel that complies with the |TempModel_V2| interface determine the air
    temperature of the hydrological response units.

    Example:

        We use the combination of |evap_tw2002| and |meteo_temp_io| as an example:

        >>> from hydpy.models.evap_tw2002 import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> hruarea(0.5, 0.3, 0.2)
        >>> with model.add_tempmodel_v2("meteo_temp_io"):
        ...     temperatureaddend(1.0, 2.0, 4.0)
        ...     inputs.temperature = 2.0
        >>> model.calc_airtemperature_v1()
        >>> factors.airtemperature
        airtemperature(3.0, 4.0, 6.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_factors.AirTemperature,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: petinterfaces.PETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        submodel.determine_temperature()
        for k in range(con.nmbhru):
            fac.airtemperature[k] = submodel.get_temperature(k)


class Calc_AirTemperature_V1(modeltools.Method):
    """Let a submodel that complies with the |TempModel_V1| or |TempModel_V2| interface
    determine the air temperature of the individual hydrological response units."""

    SUBMODELINTERFACES = (
        tempinterfaces.TempModel_V1,
        tempinterfaces.TempModel_V2,
    )
    SUBMETHODS = (
        Calc_AirTemperature_TempModel_V1,
        Calc_AirTemperature_TempModel_V2,
    )
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_factors.AirTemperature,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.tempmodel_typeid == 1:
            model.calc_airtemperature_tempmodel_v1(
                cast(tempinterfaces.TempModel_V1, model.tempmodel)
            )
        elif model.tempmodel_typeid == 2:
            model.calc_airtemperature_tempmodel_v2(
                cast(tempinterfaces.TempModel_V2, model.tempmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_MeanAirTemperature_TempModel_V1(modeltools.Method):
    """Query mean air temperature from a main model referenced as a sub-submodel and
    follows the |TempModel_V1| interface.

    Example:

        We use the combination of |hland_v1| and |evap_hbv96| as an example:

        >>> from hydpy.models.hland_v1 import *
        >>> parameterstep()
        >>> area(10.0)
        >>> nmbzones(3)
        >>> zonearea(5.0, 3.0, 2.0)
        >>> zonetype(FIELD)
        >>> zonez(2.0)
        >>> with model.add_petmodel_v1("evap_hbv96"):
        ...     pass
        >>> inputs.t = 2.0
        >>> model.petmodel.calc_meanairtemperature_v1()
        >>> model.petmodel.sequences.factors.meanairtemperature
        meanairtemperature(2.0)
    """

    RESULTSEQUENCES = (evap_factors.MeanAirTemperature,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: tempinterfaces.TempModel_V1
    ) -> None:
        fac = model.sequences.factors.fastaccess
        fac.meanairtemperature = submodel.get_meantemperature()


class Calc_MeanAirTemperature_TempModel_V2(modeltools.Method):
    """Let a submodel that complies with the |TempModel_V2| interface determine the
    mean air temperature.

    Example:

        We use the combination of |evap_hbv96| and |meteo_temp_io| as an example:

        >>> from hydpy.models.evap_hbv96 import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> hruarea(0.5, 0.3, 0.2)
        >>> with model.add_tempmodel_v2("meteo_temp_io"):
        ...     temperatureaddend(1.0, 2.0, 4.0)
        ...     inputs.temperature = 2.0
        >>> model.calc_meanairtemperature_v1()
        >>> factors.meanairtemperature
        meanairtemperature(3.9)
    """

    RESULTSEQUENCES = (evap_factors.MeanAirTemperature,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: petinterfaces.PETModel_V1) -> None:
        fac = model.sequences.factors.fastaccess
        submodel.determine_temperature()
        fac.meanairtemperature = submodel.get_meantemperature()


class Calc_MeanAirTemperature_V1(modeltools.Method):
    """Let a submodel that complies with the |TempModel_V1| or |TempModel_V2| interface
    determine the air temperature."""

    SUBMODELINTERFACES = (
        tempinterfaces.TempModel_V1,
        tempinterfaces.TempModel_V2,
    )
    SUBMETHODS = (
        Calc_MeanAirTemperature_TempModel_V1,
        Calc_MeanAirTemperature_TempModel_V2,
    )
    RESULTSEQUENCES = (evap_factors.MeanAirTemperature,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.tempmodel_typeid == 1:
            model.calc_meanairtemperature_tempmodel_v1(
                cast(tempinterfaces.TempModel_V1, model.tempmodel)
            )
        elif model.tempmodel_typeid == 2:
            model.calc_meanairtemperature_tempmodel_v2(
                cast(tempinterfaces.TempModel_V2, model.tempmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_AdjustedWindSpeed_V1(modeltools.Method):
    r"""Adjust the measured wind speed to a height of two meters above the ground
    according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 47, modified for higher
    precision):

      .. math::
        AdjustedWindSpeed = WindSpeed \cdot
        \frac{ln((2-d)/z_0)}{ln((MeasuringHeightWindSpeed-d)/z_0)}`

      :math:`d = 2 / 3 \cdot 0.12`

      :math:`z_0 = 0.123 \cdot 0.12`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> measuringheightwindspeed(10.0)
        >>> inputs.windspeed = 5.0
        >>> model.calc_adjustedwindspeed_v1()
        >>> factors.adjustedwindspeed
        adjustedwindspeed(3.738763)
    """

    CONTROLPARAMETERS = (evap_control.MeasuringHeightWindSpeed,)
    REQUIREDSEQUENCES = (evap_inputs.WindSpeed,)
    RESULTSEQUENCES = (evap_factors.AdjustedWindSpeed,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        d_d = 2.0 / 3.0 * 0.12
        d_z0 = 0.123 * 0.12
        fac.adjustedwindspeed = inp.windspeed * (
            modelutils.log((2.0 - d_d) / d_z0)
            / modelutils.log((con.measuringheightwindspeed - d_d) / d_z0)
        )


class Calc_SaturationVapourPressure_V1(modeltools.Method):
    r"""Calculate the saturation vapour pressure according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 11):
      :math:`SaturationVapourPressure = 6.108 \cdot
      \exp \left( \frac{17.27 \cdot AirTemperature}{AirTemperature + 237.3} \right)`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> factors.airtemperature = 10.0
        >>> model.calc_saturationvapourpressure_v1()
        >>> factors.saturationvapourpressure
        saturationvapourpressure(12.279626)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (evap_factors.AirTemperature,)
    RESULTSEQUENCES = (evap_factors.SaturationVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.saturationvapourpressure[k] = 6.108 * modelutils.exp(
                17.27 * fac.airtemperature[k] / (fac.airtemperature[k] + 237.3)
            )


class Calc_SaturationVapourPressureSlope_V1(modeltools.Method):
    r"""Calculate the slope of the saturation vapour pressure curve according to
    :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 13):
      :math:`SaturationVapourPressureSlope = 4098 \cdot
      \frac{SaturationVapourPressure}{(AirTemperature + 237.3)^2}`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> factors.airtemperature = 10.0
        >>> factors.saturationvapourpressure = 12.279626
        >>> model.calc_saturationvapourpressureslope_v1()
        >>> factors.saturationvapourpressureslope
        saturationvapourpressureslope(0.822828)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (
        evap_factors.AirTemperature,
        evap_factors.SaturationVapourPressure,
    )
    RESULTSEQUENCES = (evap_factors.SaturationVapourPressureSlope,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.saturationvapourpressureslope[k] = (
                4098.0
                * fac.saturationvapourpressure[k]
                / (fac.airtemperature[k] + 237.3) ** 2
            )


class Calc_ActualVapourPressure_V1(modeltools.Method):
    r"""Calculate the actual vapour pressure according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 19, modified):
      :math:`ActualVapourPressure = SaturationVapourPressure \cdot
      RelativeHumidity / 100`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> inputs.relativehumidity = 60.0
        >>> factors.saturationvapourpressure = 30.0
        >>> model.calc_actualvapourpressure_v1()
        >>> factors.actualvapourpressure
        actualvapourpressure(18.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (
        evap_inputs.RelativeHumidity,
        evap_factors.SaturationVapourPressure,
    )
    RESULTSEQUENCES = (evap_factors.ActualVapourPressure,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        for k in range(con.nmbhru):
            fac.actualvapourpressure[k] = (
                fac.saturationvapourpressure[k] * inp.relativehumidity / 100.0
            )


class Update_LoggedClearSkySolarRadiation_V1(modeltools.Method):
    """Log the clear sky solar radiation values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        three memorised values to the right and stores the respective new value on the
        most left position:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedclearskysolarradiation.shape = 3
        >>> logs.loggedclearskysolarradiation = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedclearskysolarradiation_v1,
        ...                 last_example=4,
        ...                 parseqs=(inputs.clearskysolarradiation,
        ...                          logs.loggedclearskysolarradiation))
        >>> test.nexts.clearskysolarradiation = 1.0, 3.0, 2.0, 4.0
        >>> del test.inits.loggedclearskysolarradiation
        >>> test()
        | ex. | clearskysolarradiation |           loggedclearskysolarradiation\
 |
        -----------------------------------------------------------------------\
--
        |   1 |                    1.0 | 1.0  0.0                           0.0\
 |
        |   2 |                    3.0 | 3.0  1.0                           0.0\
 |
        |   3 |                    2.0 | 2.0  3.0                           1.0\
 |
        |   4 |                    4.0 | 4.0  2.0                           3.0\
 |
    """

    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_inputs.ClearSkySolarRadiation,)
    UPDATEDSEQUENCES = (evap_logs.LoggedClearSkySolarRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedclearskysolarradiation[idx] = log.loggedclearskysolarradiation[
                idx - 1
            ]
        log.loggedclearskysolarradiation[0] = inp.clearskysolarradiation


class Update_LoggedGlobalRadiation_V1(modeltools.Method):
    """Log the global radiation values of the last 24 hours.

    Example:

        The following example shows that each new method call successively moves the
        three memorised values to the right and stores the respective new value on the
        most left position:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> derived.nmblogentries(3)
        >>> logs.loggedglobalradiation.shape = 3
        >>> logs.loggedglobalradiation = 0.0
        >>> from hydpy import UnitTest
        >>> test = UnitTest(model,
        ...                 model.update_loggedglobalradiation_v1,
        ...                 last_example=4,
        ...                 parseqs=(inputs.globalradiation,
        ...                          logs.loggedglobalradiation))
        >>> test.nexts.globalradiation = 1.0, 3.0, 2.0, 4.0
        >>> del test.inits.loggedglobalradiation
        >>> test()
        | ex. | globalradiation |           loggedglobalradiation |
        -----------------------------------------------------------
        |   1 |             1.0 | 1.0  0.0                    0.0 |
        |   2 |             3.0 | 3.0  1.0                    0.0 |
        |   3 |             2.0 | 2.0  3.0                    1.0 |
        |   4 |             4.0 | 4.0  2.0                    3.0 |
    """

    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (evap_inputs.GlobalRadiation,)
    UPDATEDSEQUENCES = (evap_logs.LoggedGlobalRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        log = model.sequences.logs.fastaccess
        for idx in range(der.nmblogentries - 1, 0, -1):
            log.loggedglobalradiation[idx] = log.loggedglobalradiation[idx - 1]
        log.loggedglobalradiation[0] = inp.globalradiation


class Calc_NetShortwaveRadiation_V1(modeltools.Method):
    r"""Calculate the net shortwave radiation for the hypothetical grass reference
    crop according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 38):
      :math:`NetShortwaveRadiation = (1.0 - 0.23) \cdot GlobalRadiation`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> inputs.globalradiation = 200.0
        >>> model.calc_netshortwaveradiation_v1()
        >>> fluxes.netshortwaveradiation
        netshortwaveradiation(154.0)
    """

    REQUIREDSEQUENCES = (evap_inputs.GlobalRadiation,)
    RESULTSEQUENCES = (evap_fluxes.NetShortwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        flu.netshortwaveradiation = (1.0 - 0.23) * inp.globalradiation


class Calc_NetLongwaveRadiation_V1(modeltools.Method):
    r"""Calculate the net longwave radiation according to :cite:t:`ref-Allen1998`.

    Basic equations (:cite:t:`ref-Allen1998`, equation 39, modified):
      :math:`NetLongwaveRadiation =
      \sigma \cdot (AirTemperature + 273.16)^4
      \cdot \left( 0.34 - 0.14 \sqrt{ActualVapourPressure / 10} \right) \cdot
      (1.35 \cdot GR / CSSR - 0.35)`

      .. math::
        GR =
        \begin{cases}
        GlobalRadiation &|\ ClearSkySolarRadiation > 0
        \\
        \sum{LoggedGlobalRadiation} &|\ ClearSkySolarRadiation = 0
        \end{cases}

      .. math::
        CSSR =
        \begin{cases}
        ClearSkySolarRadiation &|\ ClearSkySolarRadiation > 0
        \\
        \sum{LoggedClearSkySolarRadiation} &|\ ClearSkySolarRadiation = 0
        \end{cases}

      :math:`\sigma = 5.6747685185185184 \cdot 10^{-8}`

    Note that when clear sky radiation is zero at night, we use the global radiation
    and clear sky radiation sums of the last 24 hours.  Averaging over three hours
    before sunset, as :cite:t:`ref-Allen1998` suggests, could be more precise but is a
    more complicated and error-prone approach.

    Example:

        The following calculation agrees with example 11 of :cite:t:`ref-Allen1998`:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> derived.nmblogentries(1)
        >>> inputs.globalradiation = 167.824074
        >>> inputs.clearskysolarradiation = 217.592593
        >>> factors.airtemperature = 22.1
        >>> factors.actualvapourpressure = 21.0
        >>> model.calc_netlongwaveradiation_v1()
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(40.87786)

        >>> inputs.clearskysolarradiation = 0.0
        >>> logs.loggedclearskysolarradiation.shape = 1
        >>> logs.loggedclearskysolarradiation = 138.888889
        >>> logs.loggedglobalradiation.shape = 1
        >>> logs.loggedglobalradiation = 115.740741
        >>> model.calc_netlongwaveradiation_v1()
        >>> fluxes.netlongwaveradiation
        netlongwaveradiation(45.832275)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.NmbLogEntries,)
    REQUIREDSEQUENCES = (
        evap_inputs.ClearSkySolarRadiation,
        evap_inputs.GlobalRadiation,
        evap_factors.AirTemperature,
        evap_factors.ActualVapourPressure,
        evap_logs.LoggedGlobalRadiation,
        evap_logs.LoggedClearSkySolarRadiation,
    )
    RESULTSEQUENCES = (evap_fluxes.NetLongwaveRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        log = model.sequences.logs.fastaccess
        if inp.clearskysolarradiation > 0.0:
            d_globalradiation = inp.globalradiation
            d_clearskysolarradiation = inp.clearskysolarradiation
        else:
            d_globalradiation = 0.0
            d_clearskysolarradiation = 0.0
            for idx in range(der.nmblogentries):
                d_clearskysolarradiation += log.loggedclearskysolarradiation[idx]
                d_globalradiation += log.loggedglobalradiation[idx]
        for k in range(con.nmbhru):
            flu.netlongwaveradiation[k] = (
                5.674768518518519e-08
                * (fac.airtemperature[k] + 273.16) ** 4
                * (0.34 - 0.14 * (fac.actualvapourpressure[k] / 10.0) ** 0.5)
                * (1.35 * d_globalradiation / d_clearskysolarradiation - 0.35)
            )


class Calc_NetRadiation_V1(modeltools.Method):
    """Calculate the total net radiation according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 40):
      :math:`NetRadiation = NetShortwaveRadiation - NetLongwaveRadiation`

    Example:

        The following calculation agrees with example 12 of :cite:t:`ref-Allen1998`:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> fluxes.netshortwaveradiation  = 111.0
        >>> fluxes.netlongwaveradiation  = 35.0
        >>> model.calc_netradiation_v1()
        >>> fluxes.netradiation
        netradiation(76.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (
        evap_fluxes.NetShortwaveRadiation,
        evap_fluxes.NetLongwaveRadiation,
    )
    RESULTSEQUENCES = (evap_fluxes.NetRadiation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.netradiation[k] = (
                flu.netshortwaveradiation - flu.netlongwaveradiation[k]
            )


class Calc_SoilHeatFlux_V1(modeltools.Method):
    r"""Calculate the soil heat flux according to :cite:t:`ref-Allen1998`.

    Basic equation for daily timesteps (:cite:t:`ref-Allen1998`, equation 42):
      :math:`SoilHeatFlux = 0` \n

    Basic equation for (sub)hourly timesteps (:cite:t:`ref-Allen1998`, eq. 45 and 46 ):
      :math:`SoilHeatFlux = \Bigl \lbrace
      {
      {0.1 \cdot SoilHeatFlux \ | \ NetRadiation \geq 0}
      \atop
      {0.5 \cdot SoilHeatFlux \ | \ NetRadiation < 0}
      }`

    Examples:

        For simulation time steps shorter than one day, we define all steps with
        positive |NetRadiation| as part of the daylight period and all with negative
        |NetRadiation| as part of the nighttime period.  The total |SoilHeatFlux| is
        zero if the summed |NetRadiation| during daytime is five times as high as the
        absolute summed |NetRadiation| during nighttime:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> derived.days(1/24)
        >>> fluxes.netradiation = 100.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(10.0)
        >>> fluxes.netradiation = -20.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(-10.0)

        For any simulation step size of at least one day, method |Calc_SoilHeatFlux_V1|
        sets the |SoilHeatFlux| to zero, which :cite:t:`ref-Allen1998` suggests for
        daily simulation steps only:

        >>> derived.days(1)
        >>> fluxes.netradiation = 100.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(0.0)
        >>> fluxes.netradiation = -20.0
        >>> model.calc_soilheatflux_v1()
        >>> fluxes.soilheatflux
        soilheatflux(0.0)

        Hence, be aware that function |Calc_SoilHeatFlux_V1| does not give the best
        results for intermediate (e.g. 12 hours) or larger step sizes (e.g. one month).
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.Days,)
    REQUIREDSEQUENCES = (evap_fluxes.NetRadiation,)
    RESULTSEQUENCES = (evap_fluxes.SoilHeatFlux,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        if der.days < 1.0:
            for k in range(con.nmbhru):
                if flu.netradiation[k] >= 0.0:
                    flu.soilheatflux[k] = 0.1 * flu.netradiation[k]
                else:
                    flu.soilheatflux[k] = 0.5 * flu.netradiation[k]
        else:
            for k in range(con.nmbhru):
                flu.soilheatflux[k] = 0.0


class Calc_PsychrometricConstant_V1(modeltools.Method):
    r"""Calculate the psychrometric constant according to :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 8):
      :math:`PsychrometricConstant = 6.65 \cdot 10^{-4} \cdot AtmosphericPressure`

    Example:

        The following calculation agrees with example 2 of :cite:t:`ref-Allen1998`:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> inputs.atmosphericpressure = 818.0
        >>> model.calc_psychrometricconstant_v1()
        >>> factors.psychrometricconstant
        psychrometricconstant(0.54397)
    """

    REQUIREDSEQUENCES = (evap_inputs.AtmosphericPressure,)
    RESULTSEQUENCES = (evap_factors.PsychrometricConstant,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        fac.psychrometricconstant = 6.65e-4 * inp.atmosphericpressure


class Calc_Precipitation_PrecipModel_V1(modeltools.Method):
    """Query precipitation from a main model that is referenced as a sub-submodel and
    follows the |PrecipModel_V1| interface.

    Example:

        We use the combination of |hland_v1| and |evap_hbv96| as an example:

        >>> from hydpy.models.hland_v1 import *
        >>> parameterstep()
        >>> area(10.0)
        >>> nmbzones(3)
        >>> zonearea(5.0, 3.0, 2.0)
        >>> zonetype(FIELD)
        >>> zonez(2.0)
        >>> with model.add_petmodel_v1("evap_hbv96"):
        ...     pass
        >>> fluxes.pc(1.0, 3.0, 2.0)
        >>> model.petmodel.calc_precipitation_v1()
        >>> model.petmodel.sequences.fluxes.precipitation
        precipitation(1.0, 3.0, 2.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.Precipitation,)

    @staticmethod
    def __call__(
        model: modeltools.Model, submodel: precipinterfaces.PrecipModel_V1
    ) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.precipitation[k] = submodel.get_precipitation(k)


class Calc_Precipitation_PrecipModel_V2(modeltools.Method):
    """Let a submodel that complies with the |PrecipModel_V2| interface determine the
    precipitation.

    Example:

        We use the combination of |evap_hbv96| and |meteo_precip_io| as an example:

        >>> from hydpy.models.evap_hbv96 import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> hruarea(0.5, 0.3, 0.2)
        >>> with model.add_precipmodel_v2("meteo_precip_io"):
        ...     precipitationfactor(0.5, 1.0, 2.0)
        ...     inputs.precipitation = 2.0
        >>> model.calc_precipitation_v1()
        >>> fluxes.precipitation
        precipitation(1.0, 2.0, 4.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.Precipitation,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: petinterfaces.PETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        submodel.determine_precipitation()
        for k in range(con.nmbhru):
            flu.precipitation[k] = submodel.get_precipitation(k)


class Calc_Precipitation_V1(modeltools.Method):
    """Let a submodel that complies with the |PrecipModel_V1| or |PrecipModel_V2|
    interface determine precipitation."""

    SUBMODELINTERFACES = (
        precipinterfaces.PrecipModel_V1,
        precipinterfaces.PrecipModel_V2,
    )
    SUBMETHODS = (
        Calc_Precipitation_PrecipModel_V1,
        Calc_Precipitation_PrecipModel_V2,
    )
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.Precipitation,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.precipmodel_typeid == 1:
            model.calc_precipitation_precipmodel_v1(
                cast(precipinterfaces.PrecipModel_V1, model.precipmodel)
            )
        elif model.precipmodel_typeid == 2:
            model.calc_precipitation_precipmodel_v2(
                cast(precipinterfaces.PrecipModel_V2, model.precipmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_ReferenceEvapotranspiration_V1(modeltools.Method):
    r"""Calculate the reference evapotranspiration constant according to
    :cite:t:`ref-Allen1998`.

    Basic equation (:cite:t:`ref-Allen1998`, equation 6):
      :math:`ReferenceEvapotranspiration =
      \frac{
      0.408 \cdot SaturationVapourPressureSlope \cdot (NetRadiation - SoilHeatFlux) +
      PsychrometricConstant \cdot
      \frac{37.5 \cdot Hours}{AirTemperature + 273}
      \cdot AdjustedWindSpeed \cdot (SaturationVapourPressure - ActualVapourPressure)
      }
      {
      SaturationVapourPressureSlope +
      PsychrometricConstant \cdot (1 + 0.34 \cdot AdjustedWindSpeed)
      }`

    Note that :cite:t:`ref-Allen1998` recommends the coefficient 37 for hourly
    simulations and 900 for daily simulations.  |Calc_ReferenceEvapotranspiration_V1|
    generally uses 37.5, which gives 900 when multiplied by 24.

    Example:

        The following calculation agrees with example 18 of :cite:t:`ref-Allen1998`,
        dealing with a daily simulation step:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(1)
        >>> derived.days(1)
        >>> derived.hours(24)
        >>> factors.psychrometricconstant = 0.666
        >>> factors.airtemperature = 16.9
        >>> factors.adjustedwindspeed = 2.078
        >>> factors.actualvapourpressure = 14.09
        >>> factors.saturationvapourpressure = 19.97
        >>> factors.saturationvapourpressureslope = 1.22
        >>> fluxes.netradiation = 153.7037
        >>> fluxes.soilheatflux = 0.0
        >>> model.calc_referenceevapotranspiration_v1()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(3.877117)

        The following calculation agrees with example 19 of :cite:t:`ref-Allen1998`,
        dealing with an hourly simulation step (note that there is a  difference due to
        using 37.5 instead of 37, which is smaller than the precision of the results
        tabulated by :cite:t:`ref-Allen1998`:

        >>> derived.days(1/24)
        >>> derived.hours(1)
        >>> factors.psychrometricconstant = 0.673
        >>> factors.airtemperature = 38.0
        >>> factors.adjustedwindspeed = 3.3
        >>> factors.actualvapourpressure = 34.45
        >>> factors.saturationvapourpressure = 66.25
        >>> factors.saturationvapourpressureslope = 3.58
        >>> fluxes.netradiation = 485.8333
        >>> fluxes.soilheatflux = 48.6111
        >>> model.calc_referenceevapotranspiration_v1()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(0.629106)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (
        evap_derived.Days,
        evap_derived.Hours,
    )
    REQUIREDSEQUENCES = (
        evap_factors.SaturationVapourPressureSlope,
        evap_factors.PsychrometricConstant,
        evap_factors.AirTemperature,
        evap_factors.AdjustedWindSpeed,
        evap_factors.SaturationVapourPressure,
        evap_factors.ActualVapourPressure,
        evap_fluxes.NetRadiation,
        evap_fluxes.SoilHeatFlux,
    )
    RESULTSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.referenceevapotranspiration[k] = (
                0.0352512
                * der.days
                * fac.saturationvapourpressureslope[k]
                * (flu.netradiation[k] - flu.soilheatflux[k])
                + (fac.psychrometricconstant * 3.75 * der.hours)
                / (fac.airtemperature[k] + 273.0)
                * fac.adjustedwindspeed
                * (fac.saturationvapourpressure[k] - fac.actualvapourpressure[k])
            ) / (
                fac.saturationvapourpressureslope[k]
                + fac.psychrometricconstant * (1.0 + 0.34 * fac.adjustedwindspeed)
            )


class Calc_ReferenceEvapotranspiration_V2(modeltools.Method):
    r"""Calculate reference evapotranspiration after Turc-Wendling.

    Basic equation:
      :math:`ReferenceEvapotranspiration =
      \frac{(8.64 \cdot GlobalRadiation + 93 \cdot CoastFactor) \cdot
      (AirTemperature + 22)}
      {165 \cdot (AirTemperature + 123) \cdot
      (1 + 0.00019 \cdot min(Altitude, 600))}`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> coastfactor(0.6)
        >>> hrualtitude(200.0, 600.0, 1000.0)
        >>> inputs.globalradiation = 200.0
        >>> factors.airtemperature = 15.0
        >>> model.calc_referenceevapotranspiration_v2()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(2.792463, 2.601954, 2.601954)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.HRUAltitude,
        evap_control.CoastFactor,
    )
    REQUIREDSEQUENCES = (
        evap_inputs.GlobalRadiation,
        evap_factors.AirTemperature,
    )
    RESULTSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.referenceevapotranspiration[k] = (
                (8.64 * inp.globalradiation + 93.0 * con.coastfactor[k])
                * (fac.airtemperature[k] + 22.0)
            ) / (
                165.0
                * (fac.airtemperature[k] + 123.0)
                * (1.0 + 0.00019 * min(con.hrualtitude[k], 600.0))
            )


class Calc_ReferenceEvapotranspiration_V3(modeltools.Method):
    r"""Take the input reference evapotranspiration for each hydrological response
    unit.

    Basic equation:
      :math:`ReferenceEvapotranspiration_{fluxes} =
      ReferenceEvapotranspiration_{inputs}`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> inputs.referenceevapotranspiration = 2.0
        >>> model.calc_referenceevapotranspiration_v3()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(2.0, 2.0)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    REQUIREDSEQUENCES = (evap_inputs.ReferenceEvapotranspiration,)
    RESULTSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.referenceevapotranspiration[k] = inp.referenceevapotranspiration


class Calc_ReferenceEvapotranspiration_PETModel_V1(modeltools.Method):
    """Let a submodel that complies with the |PETModel_V1| interface calculate the
    reference evapotranspiration.

    Example:

        We use |evap_tw2002| as an example:

        >>> from hydpy.models.evap_mlc import *
        >>> parameterstep()
        >>> nmbhru(3)
        >>> hruarea(0.5, 0.3, 0.2)
        >>> with model.add_retmodel_v1("evap_tw2002"):
        ...     hrualtitude(200.0, 600.0, 1000.0)
        ...     coastfactor(0.6)
        ...     evapotranspirationfactor(1.1)
        ...     inputs.globalradiation = 200.0
        ...     with model.add_tempmodel_v2("meteo_temp_io"):
        ...         temperatureaddend(1.0)
        ...         inputs.temperature = 14.0
        >>> model.calc_referenceevapotranspiration_v4()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(3.07171, 2.86215, 2.86215)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model, submodel: petinterfaces.PETModel_V1) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        submodel.determine_potentialevapotranspiration()
        for k in range(con.nmbhru):
            flu.referenceevapotranspiration[
                k
            ] = submodel.get_potentialevapotranspiration(k)


class Calc_ReferenceEvapotranspiration_V4(modeltools.Method):
    """Let a submodel that complies with the |PETModel_V1| interface calculate the
    reference evapotranspiration."""

    SUBMODELINTERFACES = (petinterfaces.PETModel_V1,)
    SUBMETHODS = (Calc_ReferenceEvapotranspiration_PETModel_V1,)
    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    RESULTSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        if model.retmodel_typeid == 1:
            model.calc_referenceevapotranspiration_petmodel_v1(
                cast(petinterfaces.PETModel_V1, model.retmodel)
            )
        # ToDo:
        #     else:
        #         assert_never(model.petmodel)


class Calc_ReferenceEvapotranspiration_V5(modeltools.Method):
    r"""Adjust the normal evapotranspiration to the difference between actual air
    temperature and normal air temperature :cite:p:`ref-Lindstrom1997HBV96`.

    Basic equation:
      :math:`ReferenceEvapotranspiration = NormalEvapotranspiration \cdot
      (1 + AirTemperatureFactor \cdot (MeanAirTemperature - NormalAirTemperature))`

    Restriction:
      :math:`0 \leq ReferenceEvapotranspiration \leq 2 \cdot NormalEvapotranspiration`

    Examples:

        We prepare four hydrological response units with different values for the
        |AirTemperatureFactor| (the negative value of the first unit is not meaningful
        but applied for illustration):

        >>> from hydpy.models.evap import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbhru(4)
        >>> airtemperaturefactor(-0.5, 0.0, 0.1, 0.5)
        >>> inputs.normalairtemperature = 20.0
        >>> inputs.normalevapotranspiration = 2.0

        With actual temperature equal to normal temperature, actual (uncorrected)
        evapotranspiration equals normal evapotranspiration:

        >>> factors.meanairtemperature = 20.0
        >>> model.calc_referenceevapotranspiration_v5()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(2.0, 2.0, 2.0, 2.0)

        For an actual temperature of 5 °C higher than normal, reference
        evapotranspiration is increased by 1 mm for the third unit.  For the first
        unit, reference evapotranspiration is 0 mm (the smallest value allowed), and
        for the fourth unit, it is the doubled normal value (the largest value
        allowed):

        >>> factors.meanairtemperature  = 25.0
        >>> model.calc_referenceevapotranspiration_v5()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(0.0, 2.0, 3.0, 4.0)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.AirTemperatureFactor,
    )
    REQUIREDSEQUENCES = (
        evap_inputs.NormalEvapotranspiration,
        evap_inputs.NormalAirTemperature,
        evap_factors.MeanAirTemperature,
    )
    RESULTSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        inp = model.sequences.inputs.fastaccess
        fac = model.sequences.factors.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.referenceevapotranspiration[k] = inp.normalevapotranspiration * (
                1.0
                + con.airtemperaturefactor[k]
                * (fac.meanairtemperature - inp.normalairtemperature)
            )
            flu.referenceevapotranspiration[k] = min(
                max(flu.referenceevapotranspiration[k], 0.0),
                2.0 * inp.normalevapotranspiration,
            )


class Calc_PotentialEvapotranspiration_V1(modeltools.Method):
    r"""Calculate month-specific potential evaporation based on reference
    evapotranspiration.

    Basic equation:
      :math:`PotentialEvapotranspiration = MonthFactor \cdot
      ReferenceEvapotranspiration`

    Examples:

        >>> from hydpy import pub, UnitTest
        >>> pub.timegrids = '2000-03-30', '2000-04-03', '1d'
        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> monthfactor.mar = 0.5
        >>> monthfactor.apr = 2.0
        >>> derived.moy.update()
        >>> fluxes.referenceevapotranspiration = 1.0, 2.0
        >>> model.idx_sim = pub.timegrids.init['2000-03-31']
        >>> model.calc_potentialevapotranspiration_v1()
        >>> fluxes.potentialevapotranspiration
        potentialevapotranspiration(0.5, 1.0)
        >>> model.idx_sim = pub.timegrids.init['2000-04-01']
        >>> model.calc_potentialevapotranspiration_v1()
        >>> fluxes.potentialevapotranspiration
        potentialevapotranspiration(2.0, 4.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.MonthFactor,
    )
    DERIVEDPARAMETERS = (evap_derived.MOY,)
    REQUIREDSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)
    RESULTSEQUENCES = (evap_fluxes.PotentialEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            factor: float = con.monthfactor[
                der.moy[model.idx_sim] - con._monthfactor_entrymin
            ]
            flu.potentialevapotranspiration[k] = (
                factor * flu.referenceevapotranspiration[k]
            )


class Calc_PotentialEvapotranspiration_V2(modeltools.Method):
    r"""Calculate month- and land cover-specific potential evaporation based on
    reference evapotranspiration.

    Basic equation:
      :math:`PotentialEvapotranspiration = LandMonthFactor \cdot
      ReferenceEvapotranspiration`

    Examples:

        Base model |evap| does not define any land cover types by itself but takes the
        ones of the respective main model.  Here, we manually introduce the land cover
        types of grass, trees, and water to apply |evap| as a stand-alone model:

        >>> from hydpy import pub
        >>> pub.timegrids = '2000-03-30', '2000-04-03', '1d'
        >>> from hydpy.core.parametertools import Constants
        >>> GRASS, TREES, WATER = 1, 2, 3
        >>> constants = Constants(GRASS=GRASS, TREES=TREES, WATER=WATER)
        >>> from hydpy.models.evap.evap_control import HRUType, LandMonthFactor
        >>> with HRUType.modify_constants(constants), \
        ...         LandMonthFactor.modify_rows(constants):
        ...     from hydpy.models.evap import *
        ...     parameterstep()
        >>> nmbhru(2)
        >>> hrutype(TREES, WATER)
        >>> landmonthfactor.trees_mar = 1.0
        >>> landmonthfactor.trees_apr = 2.0
        >>> landmonthfactor.water_mar = 0.5
        >>> landmonthfactor.water_apr = 2.0
        >>> derived.moy.update()
        >>> fluxes.referenceevapotranspiration = 1.0, 2.0
        >>> model.idx_sim = pub.timegrids.init['2000-03-31']
        >>> model.calc_potentialevapotranspiration_v2()
        >>> fluxes.potentialevapotranspiration
        potentialevapotranspiration(1.0, 1.0)
        >>> model.idx_sim = pub.timegrids.init['2000-04-01']
        >>> model.calc_potentialevapotranspiration_v2()
        >>> fluxes.potentialevapotranspiration
        potentialevapotranspiration(2.0, 4.0)

        .. testsetup::

            >>> del pub.timegrids
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.HRUType,
        evap_control.LandMonthFactor,
    )
    DERIVEDPARAMETERS = (evap_derived.MOY,)
    REQUIREDSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)
    RESULTSEQUENCES = (evap_fluxes.PotentialEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            factor: float = con.landmonthfactor[
                con.hrutype[k] - con._landmonthfactor_rowmin,
                der.moy[model.idx_sim] - con._landmonthfactor_columnmin,
            ]
            flu.potentialevapotranspiration[k] = (
                factor * flu.referenceevapotranspiration[k]
            )


class Calc_PotentialEvapotranspiration_V3(modeltools.Method):
    r"""Apply the altitude- and precipitation-related adjustment factors on reference
    evapotranspiration to determine potential evapotranspiration
    :cite:p:`ref-Lindstrom1997HBV96`.

    Basic equation:
      :math:`PotentialEvapotranspiration = ReferenceEvapotranspiration \cdot
      (1 + AltitudeFactor \cdot (HRUAltitude - Altitude)) \cdot
      exp(-PrecipitationFactor \cdot Precipitation)`


    Examples:

        Three hydrological response units are at an altitude of 200 m.  A reference
        evapotranspiration value of 2 mm and a precipitation value of 5 mm are
        available at each unit:

        >>> from hydpy.models.evap import *
        >>> simulationstep("12h")
        >>> parameterstep("1d")
        >>> nmbhru(3)
        >>> hrualtitude(3.0)
        >>> fluxes.referenceevapotranspiration = 2.0
        >>> fluxes.precipitation = 5.0
        >>> derived.altitude(2.0)

        The first two units illustrate the individual altitude-related
        (|AltitudeFactor|, first unit) and the precipitation-related adjustments
        (|PrecipitationFactor|, second unit).  The third zone illustrates the
        interaction between both adjustments:

        >>> import math
        >>> altitudefactor(0.1, 0.0, 0.1)
        >>> precipitationfactor(0.0, -math.log(0.7)/10.0, -math.log(0.7)/10.0)
        >>> model.calc_potentialevapotranspiration_v3()
        >>> fluxes.potentialevapotranspiration
        potentialevapotranspiration(1.8, 1.4, 1.26)

        Method |Calc_PotentialEvapotranspiration_V3| performs truncations required to
        prevent negative potential evapotranspiration:

        >>> altitudefactor(2.0)
        >>> model.calc_potentialevapotranspiration_v3()
        >>> fluxes.potentialevapotranspiration
        potentialevapotranspiration(0.0, 0.0, 0.0)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.AltitudeFactor,
        evap_control.HRUAltitude,
        evap_control.PrecipitationFactor,
    )
    DERIVEDPARAMETERS = (evap_derived.Altitude,)
    REQUIREDSEQUENCES = (
        evap_fluxes.ReferenceEvapotranspiration,
        evap_fluxes.Precipitation,
    )
    RESULTSEQUENCES = (evap_fluxes.PotentialEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.potentialevapotranspiration[k] = flu.referenceevapotranspiration[k] * (
                1.0 - con.altitudefactor[k] * (con.hrualtitude[k] - der.altitude)
            )
            if flu.potentialevapotranspiration[k] <= 0.0:
                flu.potentialevapotranspiration[k] = 0.0
            else:
                flu.potentialevapotranspiration[k] *= modelutils.exp(
                    -con.precipitationfactor[k] * flu.precipitation[k]
                )


class Adjust_ReferenceEvapotranspiration_V1(modeltools.Method):
    r"""Adjust the previously calculated reference evapotranspiration.

    Basic equation:
      :math:`ReferenceEvapotranspiration_{new} = EvapotranspirationFactor \cdot
      ReferenceEvapotranspiration_{old}`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> evapotranspirationfactor(0.5, 2.0)
        >>> fluxes.referenceevapotranspiration = 2.0
        >>> model.adjust_referenceevapotranspiration_v1()
        >>> fluxes.referenceevapotranspiration
        referenceevapotranspiration(1.0, 4.0)
    """

    CONTROLPARAMETERS = (
        evap_control.NmbHRU,
        evap_control.EvapotranspirationFactor,
    )
    UPDATEDSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        flu = model.sequences.fluxes.fastaccess
        for k in range(con.nmbhru):
            flu.referenceevapotranspiration[k] *= con.evapotranspirationfactor[k]


class Calc_MeanReferenceEvapotranspiration_V1(modeltools.Method):
    r"""Calculate the average reference evapotranspiration.

    Basic equation:
      :math:`MeanReferenceEvapotranspiration =
      \sum_{i=1}^{NmbHRU} HRUAreaFraction_i \cdot ReferenceEvapotranspiration_i`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> derived.hruareafraction(0.8, 0.2)
        >>> fluxes.referenceevapotranspiration = 1.0, 2.0
        >>> model.calc_meanreferenceevapotranspiration_v1()
        >>> fluxes.meanreferenceevapotranspiration
        meanreferenceevapotranspiration(1.2)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.HRUAreaFraction,)
    REQUIREDSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)
    RESULTSEQUENCES = (evap_fluxes.MeanReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.meanreferenceevapotranspiration = 0.0
        for s in range(con.nmbhru):
            flu.meanreferenceevapotranspiration += (
                der.hruareafraction[s] * flu.referenceevapotranspiration[s]
            )


class Calc_MeanPotentialEvapotranspiration_V1(modeltools.Method):
    r"""Calculate the average potential evapotranspiration.

    Basic equation:
      :math:`MeanPotentialEvapotranspiration =
      \sum_{i=1}^{NmbHRU} HRUAreaFraction_i \cdot PotentialEvapotranspiration_i`

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> derived.hruareafraction(0.8, 0.2)
        >>> fluxes.potentialevapotranspiration = 1.0, 2.0
        >>> model.calc_meanpotentialevapotranspiration_v1()
        >>> fluxes.meanpotentialevapotranspiration
        meanpotentialevapotranspiration(1.2)
    """

    CONTROLPARAMETERS = (evap_control.NmbHRU,)
    DERIVEDPARAMETERS = (evap_derived.HRUAreaFraction,)
    REQUIREDSEQUENCES = (evap_fluxes.PotentialEvapotranspiration,)
    RESULTSEQUENCES = (evap_fluxes.MeanPotentialEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> None:
        con = model.parameters.control.fastaccess
        der = model.parameters.derived.fastaccess
        flu = model.sequences.fluxes.fastaccess

        flu.meanpotentialevapotranspiration = 0.0
        for s in range(con.nmbhru):
            flu.meanpotentialevapotranspiration += (
                der.hruareafraction[s] * flu.potentialevapotranspiration[s]
            )


class Determine_PotentialEvapotranspiration_V1(modeltools.Method):
    r"""Interface method that applies the complete application model by executing all
    "run methods"."""

    @staticmethod
    def __call__(model: modeltools.AdHocModel) -> None:
        model.run()


class Get_PotentialEvapotranspiration_V1(modeltools.Method):
    """Get the current reference evapotranspiration from the selected hydrological
    response unit.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> fluxes.referenceevapotranspiration = 2.0, 4.0
        >>> model.get_potentialevapotranspiration_v1(0)
        2.0
        >>> model.get_potentialevapotranspiration_v1(1)
        4.0
    """

    REQUIREDSEQUENCES = (evap_fluxes.ReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.referenceevapotranspiration[s]


class Get_PotentialEvapotranspiration_V2(modeltools.Method):
    """Get the current potential evapotranspiration from the selected hydrological
    response unit.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> fluxes.potentialevapotranspiration = 2.0, 4.0
        >>> model.get_potentialevapotranspiration_v2(0)
        2.0
        >>> model.get_potentialevapotranspiration_v2(1)
        4.0
    """

    REQUIREDSEQUENCES = (evap_fluxes.PotentialEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model, s: int) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.potentialevapotranspiration[s]


class Get_MeanPotentialEvapotranspiration_V1(modeltools.Method):
    """Get the averaged reference evapotranspiration.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> fluxes.meanreferenceevapotranspiration = 3.0
        >>> model.get_meanpotentialevapotranspiration_v1()
        3.0
    """

    REQUIREDSEQUENCES = (evap_fluxes.MeanReferenceEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.meanreferenceevapotranspiration


class Get_MeanPotentialEvapotranspiration_V2(modeltools.Method):
    """Get the averaged potential evapotranspiration.

    Example:

        >>> from hydpy.models.evap import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> fluxes.meanpotentialevapotranspiration = 3.0
        >>> model.get_meanpotentialevapotranspiration_v2()
        3.0
    """

    REQUIREDSEQUENCES = (evap_fluxes.MeanPotentialEvapotranspiration,)

    @staticmethod
    def __call__(model: modeltools.Model) -> float:
        flu = model.sequences.fluxes.fastaccess

        return flu.meanpotentialevapotranspiration


class Model(modeltools.AdHocModel):
    """The HydPy-Evap base model."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        Calc_AirTemperature_V1,
        Calc_AdjustedWindSpeed_V1,
        Calc_SaturationVapourPressure_V1,
        Calc_SaturationVapourPressureSlope_V1,
        Calc_ActualVapourPressure_V1,
        Update_LoggedClearSkySolarRadiation_V1,
        Update_LoggedGlobalRadiation_V1,
        Calc_NetShortwaveRadiation_V1,
        Calc_NetLongwaveRadiation_V1,
        Calc_NetRadiation_V1,
        Calc_SoilHeatFlux_V1,
        Calc_PsychrometricConstant_V1,
        Calc_ReferenceEvapotranspiration_V1,
        Calc_ReferenceEvapotranspiration_V2,
        Calc_ReferenceEvapotranspiration_V3,
        Calc_ReferenceEvapotranspiration_V4,
        Calc_ReferenceEvapotranspiration_V5,
        Adjust_ReferenceEvapotranspiration_V1,
        Calc_PotentialEvapotranspiration_V1,
        Calc_PotentialEvapotranspiration_V2,
        Calc_PotentialEvapotranspiration_V3,
        Calc_MeanReferenceEvapotranspiration_V1,
        Calc_MeanPotentialEvapotranspiration_V1,
    )
    INTERFACE_METHODS = (
        Determine_PotentialEvapotranspiration_V1,
        Get_PotentialEvapotranspiration_V1,
        Get_PotentialEvapotranspiration_V2,
        Get_MeanPotentialEvapotranspiration_V1,
        Get_MeanPotentialEvapotranspiration_V2,
    )
    ADD_METHODS = (
        Calc_ReferenceEvapotranspiration_PETModel_V1,
        Calc_AirTemperature_TempModel_V1,
        Calc_AirTemperature_TempModel_V2,
        Calc_Precipitation_PrecipModel_V1,
        Calc_Precipitation_PrecipModel_V2,
    )
    OUTLET_METHODS = ()
    SENDER_METHODS = ()
    SUBMODELINTERFACES = (
        petinterfaces.PETModel_V1,
        tempinterfaces.TempModel_V1,
        tempinterfaces.TempModel_V2,
        precipinterfaces.PrecipModel_V1,
        precipinterfaces.PrecipModel_V2,
    )
    SUBMODELS = ()

    retmodel = modeltools.SubmodelProperty(petinterfaces.PETModel_V1)
    retmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    retmodel_typeid = modeltools.SubmodelTypeIDProperty()

    tempmodel = modeltools.SubmodelProperty(
        tempinterfaces.TempModel_V1, tempinterfaces.TempModel_V2
    )
    tempmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    tempmodel_typeid = modeltools.SubmodelTypeIDProperty()

    precipmodel = modeltools.SubmodelProperty(
        precipinterfaces.PrecipModel_V1, precipinterfaces.PrecipModel_V2
    )
    precipmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    precipmodel_typeid = modeltools.SubmodelTypeIDProperty()


class Sub_PETModel_V1(modeltools.AdHocModel, petinterfaces.PETModel_V1):
    """Base class for HydPy-Evap models that comply with the |PETModel_V1| submodel
    interface."""

    @staticmethod
    @contextlib.contextmanager
    def share_configuration(
        sharable_configuration: SharableConfiguration,
    ) -> Generator[None, None, None]:
        """Take the `landtype_constants` data to adjust the parameters
        |evap_control.HRUType| and |evap_control.LandMonthFactor|, the
        `landtype_refindices` parameter instance to adjust the index references of all
        parameters inherited from |evap_parameters.ZipParameter1D| and the `refweights`
        parameter instance to adjust the weight references of all sequences inherited
        from |evap_sequences.FactorSequence1D| or |evap_sequences.FluxSequence1D|,
        temporarily:

        >>> from hydpy.core.parametertools import Constants, NameParameter, Parameter
        >>> consts = Constants(GRASS=1, TREES=3, WATER=2)
        >>> class LandType(NameParameter):
        ...     __name__ = "temp.py"
        ...     constants = consts
        >>> class Subarea(Parameter):
        ...     ...
        >>> from hydpy.models.evap.evap_model import Sub_PETModel_V1
        >>> with Sub_PETModel_V1.share_configuration(
        ...         {"landtype_constants": consts,
        ...          "landtype_refindices": LandType,
        ...          "refweights": Subarea}):
        ...     from hydpy.models.evap.evap_control import HRUType, LandMonthFactor
        ...     HRUType.constants
        ...     LandMonthFactor.rowmin, LandMonthFactor.rownames
        ...     from hydpy.models.evap.evap_parameters import ZipParameter1D
        ...     ZipParameter1D.refindices.__name__
        ...     ZipParameter1D._refweights.__name__
        ...     from hydpy.models.evap.evap_sequences import FactorSequence1D, \
FluxSequence1D
        ...     FactorSequence1D._refweights.__name__
        ...     FluxSequence1D._refweights.__name__
        {'GRASS': 1, 'TREES': 3, 'WATER': 2}
        (1, ('grass', 'water', 'trees'))
        'LandType'
        'Subarea'
        'Subarea'
        'Subarea'
        >>> HRUType.constants
        {'ANY': 1}
        >>> LandMonthFactor.rowmin, LandMonthFactor.rownames
        (0, ('ANY',))
        >>> ZipParameter1D.refindices
        >>> ZipParameter1D._refweights
        >>> FactorSequence1D._refweights
        >>> FluxSequence1D._refweights
        """
        with evap_control.HRUType.modify_constants(
            sharable_configuration["landtype_constants"]
        ), evap_control.LandMonthFactor.modify_rows(
            sharable_configuration["landtype_constants"]
        ), evap_parameters.ZipParameter1D.modify_refindices(
            sharable_configuration["landtype_refindices"]
        ), evap_parameters.ZipParameter1D.modify_refweights(
            sharable_configuration["refweights"]
        ), evap_parameters.ZipParameter1D.modify_refweights(
            sharable_configuration["refweights"]
        ), evap_sequences.FactorSequence1D.modify_refweights(
            sharable_configuration["refweights"]
        ), evap_sequences.FluxSequence1D.modify_refweights(
            sharable_configuration["refweights"]
        ):
            yield

    @importtools.define_targetparameter(evap_control.NmbHRU)
    def prepare_nmbzones(self, nmbzones: int) -> None:
        """Set the number of hydrological response units.

        >>> from hydpy.models.evap_tw2002 import *
        >>> parameterstep()
        >>> model.prepare_nmbzones(2)
        >>> nmbhru
        nmbhru(2)
        """
        self.parameters.control.nmbhru(nmbzones)

    @importtools.define_targetparameter(evap_control.NmbHRU)
    def prepare_zonetypes(self, zonetypes: Sequence[int]) -> None:
        """Set the hydrological response unit types.

        >>> GRASS, TREES, WATER = 1, 3, 2
        >>> from hydpy.core.parametertools import Constants
        >>> constants = Constants(GRASS=GRASS, TREES=TREES, WATER=WATER)
        >>> from hydpy.models.evap.evap_control import HRUType
        >>> with HRUType.modify_constants(constants):
        ...     from hydpy.models.evap_mlc import *
        ...     parameterstep()
        >>> nmbhru(2)
        >>> model.prepare_zonetypes([TREES, WATER])
        >>> hrutype
        hrutype(TREES, WATER)
        """
        if (hrutype := getattr(self.parameters.control, "hrutype", None)) is not None:
            hrutype(zonetypes)

    @importtools.define_targetparameter(evap_control.HRUArea)
    def prepare_subareas(self, subareas: Sequence[float]) -> None:
        """Set the area of all hydrological response units in km².

        >>> from hydpy.models.evap_tw2002 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> model.prepare_subareas([1.0, 3.0])
        >>> hruarea
        hruarea(1.0, 3.0)
        """
        self.parameters.control.hruarea(subareas)

    @importtools.define_targetparameter(evap_control.HRUAltitude)
    def prepare_elevations(self, elevations: Sequence[float]) -> None:
        """Set the altitude of all hydrological response units in m.

        >>> from hydpy.models.evap_tw2002 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> model.prepare_elevations([1.0, 3.0])
        >>> hrualtitude
        hrualtitude(1.0, 3.0)
        """
        self.parameters.control.hrualtitude(elevations)


class Main_PETModel_V1(modeltools.AdHocModel):
    """Base class for HydPy-Evap models that use submodels that comply with the
    |PETModel_V1| interface."""

    retmodel: modeltools.SubmodelProperty
    retmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    retmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "retmodel",
        petinterfaces.PETModel_V1,
        petinterfaces.PETModel_V1.prepare_nmbzones,
        petinterfaces.PETModel_V1.prepare_subareas,
    )
    def add_retmodel_v1(self, retmodel: petinterfaces.PETModel_V1) -> None:
        """Initialise the given `retmodel` that follows the |PETModel_V1| interface and
        is responsible for calculating the reference evapotranspiration.

        >>> from hydpy import pub
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> from hydpy.models.evap_m import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> hruarea(2.0, 8.0)
        >>> with model.add_retmodel_v1("evap_io"):
        ...     nmbhru
        nmbhru(2)
        >>> model.retmodel.parameters.control.hruarea
        hruarea(2.0, 8.0)
        """
        control = self.parameters.control
        retmodel.prepare_nmbzones(control.nmbhru.value)
        retmodel.prepare_subareas(control.hruarea.values)


class Main_TempModel_V1(modeltools.AdHocModel, modeltools.SubmodelInterface):
    """Base class for HydPy-Evap models that can use main models as their sub-submodels
    if they comply with the |TempModel_V1| interface."""

    tempmodel: modeltools.SubmodelProperty
    tempmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    tempmodel_typeid = modeltools.SubmodelTypeIDProperty()

    def add_mainmodel_as_subsubmodel(self, mainmodel: modeltools.Model) -> bool:
        """Add the given main model as a submodel if it complies with the
        |TempModel_V1| interface.

        >>> from hydpy import prepare_model
        >>> evap = prepare_model("evap_hbv96")
        >>> evap.add_mainmodel_as_subsubmodel(prepare_model("evap_io"))
        False
        >>> evap.tempmodel
        >>> evap.tempmodel_is_mainmodel
        False
        >>> evap.tempmodel_typeid
        0

        >>> hland = prepare_model("hland_v1")
        >>> evap.add_mainmodel_as_subsubmodel(hland)
        True
        >>> evap.tempmodel is hland
        True
        >>> evap.tempmodel_is_mainmodel
        True
        >>> evap.tempmodel_typeid
        1
        """
        if isinstance(mainmodel, tempinterfaces.TempModel_V1):
            self.tempmodel = mainmodel
            self.tempmodel_is_mainmodel = True
            self.tempmodel_typeid = tempinterfaces.TempModel_V1.typeid
            super().add_mainmodel_as_subsubmodel(mainmodel)
            return True
        return super().add_mainmodel_as_subsubmodel(mainmodel)


class Main_TempModel_V2(modeltools.AdHocModel):
    """Base class for HydPy-Evap models that support submodels that comply with the
    |TempModel_V2| interface."""

    tempmodel: modeltools.SubmodelProperty
    tempmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    tempmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "tempmodel",
        tempinterfaces.TempModel_V2,
        tempinterfaces.TempModel_V2.prepare_nmbzones,
        tempinterfaces.TempModel_V2.prepare_subareas,
    )
    def add_tempmodel_v2(self, tempmodel: tempinterfaces.TempModel_V2) -> None:
        """Initialise the given precipitation model that follows the |TempModel_V2|
        interface and set the number and the subareas of its zones.

        >>> from hydpy.models.evap_hbv96 import *
        >>> simulationstep("1d")
        >>> parameterstep("1d")
        >>> nmbhru(2)
        >>> hruarea(2.0, 8.0)
        >>> with model.add_tempmodel_v2("meteo_temp_io"):
        ...     nmbhru
        ...     hruarea
        ...     temperatureaddend(1.0, 2.0)
        nmbhru(2)
        hruarea(2.0, 8.0)
        >>> model.tempmodel.parameters.control.temperatureaddend
        temperatureaddend(1.0, 2.0)
        """
        control = self.parameters.control
        tempmodel.prepare_nmbzones(control.nmbhru.value)
        tempmodel.prepare_subareas(control.hruarea.value)


class Main_PrecipModel_V1(modeltools.AdHocModel, modeltools.SubmodelInterface):
    """Base class for HydPy-Evap models that can use main models as their sub-submodels
    if they comply with the |PrecipModel_V1| interface."""

    precipmodel: modeltools.SubmodelProperty
    precipmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    precipmodel_typeid = modeltools.SubmodelTypeIDProperty()

    def add_mainmodel_as_subsubmodel(self, mainmodel: modeltools.Model) -> bool:
        """Add the given main model as a submodel if it complies with the
        |PrecipModel_V1| interface.

        >>> from hydpy import prepare_model
        >>> evap = prepare_model("evap_hbv96")
        >>> evap.add_mainmodel_as_subsubmodel(prepare_model("evap_io"))
        False
        >>> evap.precipmodel
        >>> evap.precipmodel_is_mainmodel
        False
        >>> evap.precipmodel_typeid
        0

        >>> hland = prepare_model("hland_v1")
        >>> evap.add_mainmodel_as_subsubmodel(hland)
        True
        >>> evap.precipmodel is hland
        True
        >>> evap.precipmodel_is_mainmodel
        True
        >>> evap.precipmodel_typeid
        1
        """
        if isinstance(mainmodel, precipinterfaces.PrecipModel_V1):
            self.precipmodel = mainmodel
            self.precipmodel_is_mainmodel = True
            self.precipmodel_typeid = precipinterfaces.PrecipModel_V1.typeid
            super().add_mainmodel_as_subsubmodel(mainmodel)
            return True
        return super().add_mainmodel_as_subsubmodel(mainmodel)


class Main_PrecipModel_V2(modeltools.AdHocModel):
    """Base class for HydPy-Evap models that support submodels that comply with the
    |PrecipModel_V2| interface."""

    precipmodel: modeltools.SubmodelProperty
    precipmodel_is_mainmodel = modeltools.SubmodelIsMainmodelProperty()
    precipmodel_typeid = modeltools.SubmodelTypeIDProperty()

    @importtools.prepare_submodel(
        "precipmodel",
        precipinterfaces.PrecipModel_V2,
        precipinterfaces.PrecipModel_V2.prepare_nmbzones,
        precipinterfaces.PrecipModel_V2.prepare_subareas,
    )
    def add_precipmodel_v2(self, precipmodel: precipinterfaces.PrecipModel_V2) -> None:
        """Initialise the given precipitation model that follows the |PrecipModel_V2|
        interface and set the number and the subareas of its zones.

        >>> from hydpy.models.evap_hbv96 import *
        >>> parameterstep()
        >>> nmbhru(2)
        >>> hruarea(2.0, 8.0)
        >>> with model.add_precipmodel_v2("meteo_precip_io"):
        ...     nmbhru
        ...     hruarea
        ...     precipitationfactor(1.0, 2.0)
        nmbhru(2)
        hruarea(2.0, 8.0)
        >>> model.precipmodel.parameters.control.precipitationfactor
        precipitationfactor(1.0, 2.0)
        """
        control = self.parameters.control
        precipmodel.prepare_nmbzones(control.nmbhru.value)
        precipmodel.prepare_subareas(control.hruarea.value)
