# -*- coding: utf-8 -*-
"""This module supports modelling based on instantaneous unit hydrographs.

This module implements some abstract descriptor classes, metaclasses and base classes.
If you are just interested in applying a certain instantaneous unit hydrograph (iuh)
function or if you want to implement an additional iuh, see the examples or the source
code of class |TranslationDiffusionEquation|.
"""
# import...
# ...from standard library
from __future__ import annotations
import abc
import itertools
import math
from typing import *

# ...from site-packages
import numpy

# ...from Hydpy
from hydpy.core import exceptiontools
from hydpy.core import objecttools
from hydpy.auxs import statstools
from hydpy.auxs import armatools
from hydpy.core.typingtools import *

if TYPE_CHECKING:
    from matplotlib import pyplot
    from scipy import special
else:
    pyplot = exceptiontools.OptionalImport("pyplot", ["matplotlib.pyplot"], locals())
    special = exceptiontools.OptionalImport("special", ["scipy.special"], locals())


class ParameterIUH:
    """Descriptor base class for |PrimaryParameterIUH| and |SecondaryParameterIUH|.

    The first initialisation argument is the parameters name.  Optionally, an
    alternative type (the default type is |float|) and a documentation string can be
    passed.
    """

    name: str
    """Name of the handled |IUH| parameter."""
    type_: Type[float]
    """Type of the handled |IUH| parameter."""

    _name: str

    def __init__(
        self,
        name: str,
        type_: Type[Any] = float,
        doc: Optional[object] = None,
    ):
        self.name = name
        self._name = "_" + name
        self.type_ = type_
        self.__doc__ = (
            f"Instantaneous unit hydrograph parameter: "
            f"{name if doc is None else str(doc)}"
        )

    @overload
    def __get__(self, obj: None, type_: Optional[Type[IUH]] = None) -> ParameterIUH:
        ...

    @overload
    def __get__(self, obj: IUH, type_: Optional[Type[IUH]] = None) -> float:
        ...

    def __get__(
        self,
        obj: Optional[IUH],
        type_: Optional[Type[IUH]] = None,
    ) -> Union[ParameterIUH, float]:
        return self if obj is None else getattr(obj, self._name, None)

    def _convert_type(self, value: float) -> float:
        try:
            return self.type_(value)
        except BaseException:
            raise TypeError(
                f"The value `{value}` of type `{type(value).__name__}` could not be "
                f"converted to type `{self.type_.__name__}` of the instantaneous unit "
                f"hydrograph parameter `{self.name}`."
            ) from None


class PrimaryParameterIUH(ParameterIUH):
    """Descriptor base class for parameters of instantaneous unit hydrograph functions
    to be defined by the user.

    When a primary parameter value is set or deleted, the master instance is instructed
    to |IUH.update| all secondary parameter values.
    """

    def __set__(self, obj: IUH, value: float) -> None:
        value = self._convert_type(value)
        setattr(obj, self._name, value)
        obj.update()

    def __delete__(self, obj: IUH) -> None:
        setattr(obj, self._name, None)
        obj.update()


class SecondaryParameterIUH(ParameterIUH):
    """Descriptor base class for parameters of instantaneous unit hydrograph functions
    which can be determined automatically."""

    def __set__(self, obj: IUH, value: float) -> None:
        value = self._convert_type(value)
        setattr(obj, self._name, value)

    def __delete__(self, obj: IUH) -> None:
        setattr(obj, self._name, None)


class MetaIUH(type):
    """Metaclass for class |IUH|.

    For storing |PrimaryParameterIUH| and |SecondaryParameterIUH| in separate
    dictionaries.
    """

    def __new__(
        mcs,
        name: str,
        parents: Tuple[Type[Any]],
        dict_: Dict[str, Any],
    ) -> MetaIUH:
        primary_parameters = {}
        secondary_parameters = {}
        for key, value in dict_.items():
            if isinstance(value, PrimaryParameterIUH):
                primary_parameters[key] = value
            elif isinstance(value, SecondaryParameterIUH):
                secondary_parameters[key] = value
        dict_["_PRIMARY_PARAMETERS"] = primary_parameters
        dict_["_SECONDARY_PARAMETERS"] = secondary_parameters
        return type.__new__(mcs, name, parents, dict_)


class IUH(metaclass=MetaIUH):
    """Base class for instantaneous unit hydrograph function objects.

    See class |TranslationDiffusionEquation| for explanations and application examples.

    For developers: The string representation does also work for parameter-free |IUH|
    subclasses:

    >>> from hydpy.auxs.iuhtools import IUH
    >>> class Test(IUH):
    ...     __call__ = None
    ...     calc_secondary_parameters = None
    >>> Test()
    Test()
    """

    ma: armatools.MA
    """Moving Average model"""
    arma: armatools.ARMA
    """Autoregressive-Moving Average model."""
    dt_response: float = 1e-2
    """Relative stepsize for plotting and analyzing iuh functions."""
    smallest_response: float = 1e-9
    """Smallest value taken into account for plotting and analyzing iuh functions."""

    # Overwritten by metaclass:
    _PRIMARY_PARAMETERS: Dict[str, PrimaryParameterIUH] = {}
    _SECONDARY_PARAMETERS: Dict[str, SecondaryParameterIUH] = {}

    def __init__(self, **kwargs: float) -> None:
        self.ma = armatools.MA(self)
        self.arma = armatools.ARMA(ma_model=self.ma)
        if kwargs:
            self.set_primary_parameters(**kwargs)

    @abc.abstractmethod
    def __call__(self, t: float) -> float:
        """Must be implemented by the concrete |IUH| subclass."""

    def set_primary_parameters(self, **kwargs: float) -> None:
        """Set all primary parameters at once."""
        given = sorted(kwargs.keys())
        required = sorted(self._PRIMARY_PARAMETERS)
        if given == required:
            for (key, value) in kwargs.items():
                setattr(self, key, value)
        else:
            raise ValueError(
                f"When passing primary parameter values as initialization arguments of "
                f"the instantaneous unit hydrograph class `{type(self).__name__}`, or "
                f"when using method `set_primary_parameters`, one has to to define all "
                f"values at once via keyword arguments.  But instead of the primary "
                f"parameter names `{objecttools.enumeration(required)}` the following "
                f"keywords were given: {objecttools.enumeration(given)}."
            )

    @property
    def primary_parameters_complete(self) -> bool:
        """True/False flag that indicates whether the values of all primary parameters
        are defined or not."""
        for primpar in self._PRIMARY_PARAMETERS.values():
            if getattr(self, primpar.name) is None:
                return False
        return True

    @abc.abstractmethod
    def calc_secondary_parameters(self) -> None:
        """Must be implemented by the concrete |IUH| subclass."""

    def update(self) -> None:
        """Delete the coefficients of the pure MA model and also all MA and AR
        coefficients of the ARMA model.  Also calculate or delete the values of all
        secondary iuh parameters, depending on the completeness of the values of the
        primary parameters.
        """
        del self.ma.coefs
        del self.arma.ma_coefs
        del self.arma.ar_coefs
        if self.primary_parameters_complete:
            self.calc_secondary_parameters()
        else:
            for secpar in self._SECONDARY_PARAMETERS.values():
                delattr(self, secpar.name)

    @property
    def delay_response_series(self) -> Tuple[Vector[float], Vector[float]]:
        """A tuple of two numpy arrays, which hold the time delays and the associated
        iuh values respectively."""
        delays = []
        responses = []
        sum_responses = 0.0
        for t in itertools.count(self.dt_response / 2.0, self.dt_response):
            delays.append(t)
            response = self(t)
            responses.append(response)
            sum_responses += self.dt_response * response
            if (sum_responses > 0.9) and (response < self.smallest_response):
                break
        return numpy.array(delays), numpy.array(responses)

    def plot(self, threshold: Optional[float] = None, **kwargs) -> None:
        """Plot the instanteneous unit hydrograph.

        The optional argument allows for defining a threshold of the cumulative sum of
        the hydrograph, used to adjust the largest value of the x-axis.  It must be a
        value between zero and one.
        """
        delays, responses = self.delay_response_series
        pyplot.plot(delays, responses, **kwargs)
        pyplot.xlabel("time")
        pyplot.ylabel("response")
        if threshold is not None:
            threshold = numpy.clip(threshold, 0.0, 1.0)
            cumsum = numpy.cumsum(responses)
            idx = numpy.where(cumsum >= threshold * cumsum[-1])[0][0]
            pyplot.xlim(0.0, delays[idx])

    @property
    def moment1(self) -> float:
        """The first time delay weighted statistical moment of the instantaneous unit
        hydrograph."""
        delays, response = self.delay_response_series
        return statstools.calc_mean_time(delays, response)

    @property
    def moment2(self) -> float:
        """The second time delay weighted statistical momens of the instantaneous unit
        hydrograph."""
        moment1 = self.moment1
        delays, response = self.delay_response_series
        return statstools.calc_mean_time_deviation(delays, response, moment1)

    @property
    def moments(self) -> Tuple[float, float]:
        """The first two time delay weighted statistical moments of the instantaneous
        unit hydrograph."""
        return self.moment1, self.moment2

    def __repr__(self) -> str:
        parts = [type(self).__name__, "("]
        for (name, primpar) in sorted(self._PRIMARY_PARAMETERS.items()):
            value = primpar.__get__(self)
            if value is not None:
                parts.extend([name, "=", objecttools.repr_(value), ", "])
        if parts[-1] == ", ":
            parts[-1] = ")"
        else:
            parts.append(")")
        return "".join(parts)


class TranslationDiffusionEquation(IUH):
    """An instantaneous unit hydrograph based on the `translation diffusion equation`.

    The equation used is a linear approximation of the Saint-Venant
    equations for channel routing:

      :math:`h(t) = \\frac{a}{t \\cdot \\sqrt{\\pi \\cdot t}} \\cdot
      e^{-t \\cdot (a/t-b)^2}`

    with:
      :math:`a = \\frac{x}{2 \\cdot \\sqrt{d}}`

      :math:`b = \\frac{u}{2 \\cdot \\sqrt{d}}`

    There are three primary parameters, |TranslationDiffusionEquation.u|,
    |TranslationDiffusionEquation.d|, and |TranslationDiffusionEquation.x|,  whichs
    values need to be defined by the user:

    >>> from hydpy import TranslationDiffusionEquation
    >>> tde = TranslationDiffusionEquation(u=5.0, d=15.0, x=50.0)
    >>> tde
    TranslationDiffusionEquation(d=15.0, u=5.0, x=50.0)

    The values of both secondary parameters are determined automatically:

    >>> from hydpy import round_
    >>> round_((tde.a, tde.b))
    6.454972, 0.645497

    The function can principally be evaluated for time delays larger zero, but not for
    zero time delay, which can cause trouble when applying numerical integration
    algorithms.  This is why we clip the given time delay to minimum value of 1e-10
    internally.  In most cases (like the following), the returned result should be
    workable for integration algorithms:

    >>> round_(tde([0.0, 5.0, 10.0, 15.0, 20.0]))
    0.0, 0.040559, 0.115165, 0.031303, 0.00507
    >>> round_(tde(value) for value in [0.0, 5.0, 10.0, 15.0, 20.0])
    0.0, 0.040559, 0.115165, 0.031303, 0.00507

    The first delay weighted central moment of the translation diffusion equation
    corresponds to the time lag (`x`/`u`), the second one to wave diffusion:

    >>> round_(tde.moments)
    10.0, 3.464101

    Class |TranslationDiffusionEquation| implements its own property `moment1` (used in
    the example above), which is computationally more efficient and robust than the one
    of its base class |IUH|.  But both normally, both should return very similar values:

    >>> from hydpy.auxs.iuhtools import IUH
    >>> round_(IUH.moment1.fget(tde))
    10.0


    You can also plot the graph corresponding to the actual parameterization:

    >>> tde.plot(threshold=0.9)

    .. testsetup::

        >>> from matplotlib import pyplot
        >>> pyplot.close()

    All instances of the subclasses of |IUH| provide a pure Moving Average and an
    Autoregressive-Moving Average approximation to the dt standard impulse of the
    instantaneous unit hydrograph function.  In the given example, the MA approximation
    involves 57 coefficients, and the ARMA approximation invoves 17 coefficients:

    >>> tde.ma.order
    57
    >>> tde.arma.order
    (3, 14)

    The diffusion of the MA model deviates from the iuh function due to aggregation.
    For the ARMA model, there is also a slight deviation in time delay, as the ARMA
    model itself is only a approximation of the MA model:

    >>> round_(tde.ma.moments)
    10.0, 3.488074
    >>> round_(tde.arma.moments)
    10.000091, 3.488377

    For further information on using MA and ARMA models, read the documentation on
    module |armatools|.

    Changing a primary parameter results in an updating of the secondary parameters as
    well as the MA and the ARMA model:

    >>> tde.x = 5.
    >>> round_((tde.a, tde.b))
    0.645497, 0.645497
    >>> tde.ma.order
    37
    >>> tde.arma.order
    (4, 5)

    As long as the primary parameter values are incomplete, no secondary parameter
    values are available:

    >>> del tde.x
    >>> round_((tde.a, tde.b))
    None, None

    Suitable type conversions are performed when new parameter values are set:

    >>> tde.x = "1."
    >>> tde.x
    1.0

    It a new value cannot be converted, an error is raised:

    >>> tde.x = "a"
    Traceback (most recent call last):
    ...
    TypeError: The value `a` of type `str` could not be converted to type `float` of \
the instantaneous unit hydrograph parameter `x`.

    When passing parameter values as initialization arguments or when using method
    `set_primary_parameters`, tests for completeness are performed:

    >>> TranslationDiffusionEquation(u=5.0, d=15.0)
    Traceback (most recent call last):
    ...
    ValueError: When passing primary parameter values as initialization arguments of \
the instantaneous unit hydrograph class `TranslationDiffusionEquation`, or when using \
method `set_primary_parameters`, one has to to define all values at once via keyword \
arguments.  But instead of the primary parameter names `d, u, and x` the following \
keywords were given: d and u.
    """

    u = PrimaryParameterIUH("u", doc="Wave velocity [L/T].")
    d = PrimaryParameterIUH("d", doc="Diffusion coefficient [L²/T].")
    x = PrimaryParameterIUH("x", doc="Routing distance [L].")
    a = SecondaryParameterIUH("a", doc="Distance related coefficient.")
    _a: float  # used for speeding up numerical integration
    b = SecondaryParameterIUH("b", doc="Velocity related coefficient.")
    _b: float  # used for speeding up numerical integration

    def calc_secondary_parameters(self) -> None:
        """Determine the values of the secondary parameters
        |TranslationDiffusionEquation.a| and |TranslationDiffusionEquation.b|.
        """
        self.a = self.x / (2.0 * self.d**0.5)
        self.b = self.u / (2.0 * self.d**0.5)

    @overload
    def __call__(self, t: float) -> float:
        ...

    @overload
    def __call__(self, t: Vector[float]) -> Vector[float]:
        ...

    def __call__(self, t: Union[float, Vector[float]]) -> Union[float, Vector[float]]:
        # float-handling optimised for fast numerical integration
        if isinstance(t, float):
            if t < 1e-10:  # pylint: disable=consider-using-max-builtin
                t = 1e-10
        else:
            t = numpy.clip(t, 1e-10, numpy.inf)
        return (
            self._a
            / (t * (numpy.pi * t) ** 0.5)
            * numpy.e ** (-t * (self._a / t - self._b) ** 2)
        )

    @property
    def moment1(self) -> float:
        """The first time delay weighted statistical moment of the translation
        diffusion equation."""
        return self.x / self.u


class LinearStorageCascade(IUH):
    r"""An instantaneous unit hydrograph based on the `linear storage cascade`.

    The equation involves the gamma function, allowing for a fractional number of
    storages:

      :math:`h(t) = c \cdot (t/k)^{n-1} \cdot e^{-t/k}`

    with:
      :math:`c = \frac{1}{k \cdot \gamma(n)}`

    After defining the values of the two primary parameters |LinearStorageCascade.n|
    and |LinearStorageCascade.k|, the function object can be applied:

    >>> from hydpy import LinearStorageCascade
    >>> lsc = LinearStorageCascade(n=2.5, k=2.0)
    >>> from hydpy import round_
    >>> round_(lsc.c)
    0.376126
    >>> round_(lsc([0.0, 5.0, 10.0, 15.0, 20.0]))
    0.0, 0.122042, 0.028335, 0.004273, 0.00054
    >>> round_(lsc(value) for value in [0.0, 5.0, 10.0, 15.0, 20.0])
    0.0, 0.122042, 0.028335, 0.004273, 0.00054

    Note that we do not use the above equation directly.  Instead, we apply a
    logarithmic transformation, which allows defining extremely high values for
    parameter |LinearStorageCascade.n|, resulting in spiky response functions:

    >>> round_(LinearStorageCascade(n=10, k=1.0/10)(1.0))
    1.2511
    >>> round_(LinearStorageCascade(n=10000, k=1.0/10000)(1.0))
    39.893896

    >>> round_(LinearStorageCascade(n=10, k=1.0/10)([0.9, 1.0, 1.1]))
    1.317556, 1.2511, 1.085255
    >>> round_(LinearStorageCascade(n=10000, k=1.0/10000)([0.9, 1.0, 1.1]))
    0.0, 39.893896, 0.0
    """

    n = PrimaryParameterIUH("n", doc="Number of linear storages [-].")
    _n: float  # used for speeding up numerical integration
    k = PrimaryParameterIUH(
        "k", doc="Time of concentration of each individual storage [T]."
    )
    _k: float  # used for speeding up numerical integration
    c = SecondaryParameterIUH("c", doc="Proportionality factor.")
    log_c = SecondaryParameterIUH("log_c", doc="Logarithmic value of `c`.")
    _log_c: float  # used for speeding up numerical integration
    log_k = SecondaryParameterIUH("log_k", doc="Logarithmic value of `k`.")  #
    _log_k: float  # used for speeding up numerical integration

    def calc_secondary_parameters(self) -> None:
        """Determine the values of the secondary parameters |LinearStorageCascade.c|,
        |LinearStorageCascade.log_c|, and |LinearStorageCascade.log_k|."""
        self.c = 1.0 / (self.k * special.gamma(self.n))
        self.log_c = -numpy.log(self.k) - special.gammaln(self.n)
        self.log_k = numpy.log(self.k)

    @overload
    def __call__(self, t: float) -> float:
        ...

    @overload
    def __call__(self, t: Vector[float]) -> Vector[float]:
        ...

    def __call__(self, t: Union[float, Vector[float]]) -> Union[float, Vector[float]]:
        # float-handling optimised for fast numerical integration
        if isinstance(t, float):
            if t == 0.0:
                return 0.0
            return numpy.e ** (
                self._log_c
                + (self._n - 1.0) * (math.log(t) - self._log_k)
                - t / self._k
            )
        t = numpy.asarray(t)
        values = numpy.zeros(t.shape, dtype=float)
        idxs = t > 0.0
        t = t[idxs]
        values[idxs] = numpy.exp(
            self._log_c + (self._n - 1.0) * (numpy.log(t) - self._log_k) - t / self.k
        )
        return values

    @property
    def moment1(self) -> float:
        """The first time delay weighted statistical moment of the linear storage
        cascade."""
        return self.k * self.n
