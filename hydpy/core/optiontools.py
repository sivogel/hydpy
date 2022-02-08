# -*- coding: utf-8 -*-
"""This module implements features for defining local or global *HydPy* options."""

# import...
# ...from standard library
from __future__ import annotations
import itertools
import types
from typing import *

# ...from HydPy
import hydpy
from hydpy.core import exceptiontools
from hydpy.core import propertytools
from hydpy.core import timetools

TypeOption = TypeVar(
    "TypeOption",
    bool,
    int,
    str,
    timetools.Period,
)
TypeOptionContextBase = TypeVar("TypeOptionContextBase", bound="OptionContextBase[Any]")


class OptionPropertyBase(propertytools.BaseDescriptor, Generic[TypeOption]):
    """Base class for defining descriptors that both work like regular |property|
    instances and support the `with` statement to change the property's value
    temporarily."""

    _CONVERTER: Tuple[Callable[[TypeOption], TypeOption]]
    _default: TypeOption
    _obj2value: Dict[Hashable, TypeOption]

    def __init__(self, default: TypeOption, doc: str) -> None:
        self._default = default
        self._obj2value = {}
        self.set_doc(doc)

    def __set__(self, obj: Hashable, value: TypeOption) -> None:
        self._obj2value[obj] = self._CONVERTER[0](value)

    def __delete__(self, obj: Hashable) -> None:
        if obj in self._obj2value:
            del self._obj2value[obj]

    def _get_value(self, obj: Hashable) -> TypeOption:
        return self._obj2value.get(obj, self._default)

    def _set_value(self, obj: Hashable, value: Optional[TypeOption] = None) -> None:
        if value is not None:
            self._obj2value[obj] = self._CONVERTER[0](value)


class OptionPropertyBool(OptionPropertyBase[bool]):
    """Descriptor for defining options of type |bool|.

    Framework or model developers should implement options of type |bool| as follows:

    >>> from hydpy.core.optiontools import OptionPropertyBool
    >>> class T:
    ...     v = OptionPropertyBool(True, "x")

    Users can change the current value "normally" by assignments:

    >>> t = T()
    >>> assert t.v
    >>> t.v = False
    >>> assert not t.v

    Deleting restores the default value:

    >>> del t.v
    >>> assert t.v

    In most cases, the prefered way is to change options "temporarily" for a specific
    code block introduced by the `with` statement:

    >>> with t.v(False):
    ...     assert not t.v
    ...     with t.v(True):
    ...         assert t.v
    ...         with t.v():
    ...             assert t.v
    ...             with t.v(None):
    ...                 assert t.v
    ...                 with t.v(False):
    ...                     assert not t.v
    ...                 with t.v():
    ...                     t.v = False
    ...                     assert not t.v
    ...                 assert t.v
    ...             assert t.v
    ...         assert t.v
    ...     assert not t.v
    >>> assert t.v

    >>> with t.v(False):
    ...     assert not t.v
    ...     raise RuntimeError
    Traceback (most recent call last):
    ...
    RuntimeError
    >>> assert t.v
    """

    _CONVERTER = (bool,)

    def __get__(self, obj: Hashable, typ: Type[Hashable]) -> OptionContextBool:
        return OptionContextBool(
            self._get_value(obj), lambda value: self._set_value(obj, value)
        )


class OptionPropertyInt(OptionPropertyBase[int]):
    """Descriptor for defining options of type |int|.

    Framework or model developers should implement options of type |int| as follows:

    >>> from hydpy.core.optiontools import OptionPropertyInt
    >>> class T:
    ...     v = OptionPropertyInt(1, "x")

    Users can change the current value "normally" by assignments:

    >>> t = T()
    >>> assert t.v == 1
    >>> t.v = 2
    >>> assert t.v == 2

    Deleting restores the default value:

    >>> del t.v
    >>> assert t.v == 1

    In most cases, the prefered way is to change options "temporarily" for a specific
    code block introduced by the `with` statement:

    >>> with t.v(2):
    ...     assert t.v == 2
    ...     with t.v(3):
    ...         assert t.v == 3
    ...         with t.v():
    ...             assert t.v == 3
    ...             with t.v(None):
    ...                 assert t.v == 3
    ...                 with t.v(1):
    ...                     assert t.v == 1
    ...                 with t.v():
    ...                     t.v = 4
    ...                     assert t.v == 4
    ...                 assert t.v == 3
    ...             assert t.v == 3
    ...         assert t.v == 3
    ...     assert t.v == 2
    >>> assert t.v == 1

    >>> with t.v(2):
    ...     assert t.v == 2
    ...     raise RuntimeError
    Traceback (most recent call last):
    ...
    RuntimeError
    >>> assert t.v == 1
    """

    _CONVERTER = (int,)

    def __get__(self, obj: Hashable, typ: Type[Hashable]) -> OptionContextInt:
        return OptionContextInt(
            self._get_value(obj), lambda value: self._set_value(obj, value)
        )


class _OptionPropertyEllipsis(OptionPropertyBase[int]):
    _CONVERTER = (int,)

    def __get__(self, obj: Hashable, typ: Type[Hashable]) -> _OptionContextEllipsis:
        return _OptionContextEllipsis(
            self._get_value(obj), lambda value: self._set_value(obj, value)
        )


class OptionPropertyStr(OptionPropertyBase[str]):
    """Descriptor for defining options of type |str|.

    Framework or model developers should implement options of type |str| as follows:

    >>> from hydpy.core.optiontools import OptionPropertyStr
    >>> class T:
    ...     v = OptionPropertyStr("1", "x")

    Users can change the current value "normally" by assignments:

    >>> t = T()
    >>> assert t.v == "1"
    >>> t.v = "2"
    >>> assert t.v == "2"

    Deleting restores the default value:

    >>> del t.v
    >>> assert t.v == "1"

    In most cases, the prefered way is to change options "temporarily" for a specific
    code block introduced by the `with` statement:

    >>> with t.v("2"):
    ...     assert t.v == "2"
    ...     with t.v("3"):
    ...         assert t.v == "3"
    ...         with t.v():
    ...             assert t.v == "3"
    ...             with t.v(None):
    ...                 assert t.v == "3"
    ...                 with t.v("1"):
    ...                     assert t.v == "1"
    ...                 with t.v():
    ...                     t.v = "4"
    ...                     assert t.v == "4"
    ...                 assert t.v == "3"
    ...             assert t.v == "3"
    ...         assert t.v == "3"
    ...     assert t.v == "2"
    >>> assert t.v == "1"

    >>> with t.v("2"):
    ...     assert t.v == "2"
    ...     raise RuntimeError
    Traceback (most recent call last):
    ...
    RuntimeError
    >>> assert t.v == "1"
    """

    _CONVERTER = (str,)

    def __get__(self, obj: Hashable, typ: Type[Hashable]) -> OptionContextStr:
        return OptionContextStr(
            self._get_value(obj), lambda value: self._set_value(obj, value)
        )


class OptionPropertyPeriod(OptionPropertyBase[timetools.Period]):
    """Descriptor for defining options of type |Period|.

    Framework or model developers should implement options of type |Period| as follows:

    >>> from hydpy.core.optiontools import OptionPropertyStr
    >>> class T:
    ...     v = OptionPropertyStr("1d", "x")

    Users can change the current value "normally" by assignments (note the automatic
    type conversion):

    >>> t = T()
    >>> assert t.v == "1d"
    >>> t.v = "2d"
    >>> from hydpy import Period
    >>> assert t.v == Period("2d")

    Deleting restores the default value:

    >>> del t.v
    >>> assert t.v == "1d"

    In most cases, the prefered way is to change options "temporarily" for a specific
    code block introduced by the `with` statement:

    >>> with t.v("2d"):
    ...     assert t.v == "2d"
    ...     with t.v("3d"):
    ...         assert t.v == "3d"
    ...         with t.v():
    ...             assert t.v == "3d"
    ...             with t.v(None):
    ...                 assert t.v == "3d"
    ...                 with t.v("1d"):
    ...                     assert t.v == "1d"
    ...                 with t.v():
    ...                     t.v = "4d"
    ...                     assert t.v == "4d"
    ...                 assert t.v == "3d"
    ...             assert t.v == "3d"
    ...         assert t.v == "3d"
    ...     assert t.v == "2d"
    >>> assert t.v == "1d"

    >>> with t.v("2d"):
    ...     assert t.v == "2d"
    ...     raise RuntimeError
    Traceback (most recent call last):
    ...
    RuntimeError
    >>> assert t.v == "1d"
    """

    _CONVERTER = (timetools.Period,)

    def __get__(self, obj: Hashable, typ: Type[Hashable]) -> OptionContextPeriod:
        return OptionContextPeriod(
            self._get_value(obj), lambda value: self._set_value(obj, value)
        )

    def __set__(self, obj: Hashable, value: timetools.PeriodConstrArg) -> None:
        self._obj2value[obj] = self._CONVERTER[0](value)

    def _set_value(
        self, obj: Hashable, value: Optional[timetools.PeriodConstrArg] = None
    ) -> None:
        if value is not None:
            self._obj2value[obj] = self._CONVERTER[0](value)


class _OptionPropertySimulationstep(OptionPropertyPeriod):
    def _get_value(self, obj: Hashable) -> timetools.Period:
        try:
            return hydpy.pub.timegrids.stepsize
        except exceptiontools.AttributeNotReady:
            return super()._get_value(obj)


class OptionContextBase(Generic[TypeOption]):
    """Base class for defining context managers required for the different
    |OptionPropertyBase| subclasses."""

    _old_value: TypeOption
    _new_value: Optional[TypeOption]
    _set_value: Optional[Tuple[Callable[[Optional[TypeOption]], None]]]

    def __init__(
        self,
        value: TypeOption,
        set_value: Optional[Callable[[Optional[TypeOption]], None]] = None,
    ) -> None:
        self._old_value = value
        self._new_value = None
        if set_value is None:
            self._set_value = None
        else:
            self._set_value = (set_value,)

    def __call__(
        self: TypeOptionContextBase, new_value: Optional[TypeOption] = None
    ) -> TypeOptionContextBase:
        self._new_value = new_value
        return self

    def __enter__(self) -> None:
        if self._set_value is not None:
            self._set_value[0](self._new_value)

    def __exit__(
        self,
        exception_type: Type[BaseException],
        exception_value: BaseException,
        traceback_: types.TracebackType,
    ) -> None:
        self._new_value = None
        if self._set_value is not None:
            self._set_value[0](self._old_value)


class OptionContextBool(int, OptionContextBase[bool]):
    """Context manager required by |OptionPropertyBool|."""

    def __new__(  # pylint: disable=unused-argument
        cls,
        value: bool,
        set_value: Optional[Callable[[bool], None]] = None,
    ) -> OptionContextBool:
        return super().__new__(cls, value)


class OptionContextInt(int, OptionContextBase[int]):
    """Context manager required by |OptionPropertyInt|."""

    def __new__(  # pylint: disable=unused-argument
        cls,
        value: int,
        set_value: Optional[Callable[[int], None]] = None,
    ) -> OptionContextInt:
        return super().__new__(cls, value)


class _OptionContextEllipsis(int, OptionContextBase[int]):
    def __new__(  # pylint: disable=unused-argument
        cls,
        value: int,
        set_value: Optional[Callable[[int], None]] = None,
        optional: bool = False,
    ) -> _OptionContextEllipsis:
        return super().__new__(cls, value)

    def __call__(
        self: TypeOptionContextBase,
        new_value: Optional[int] = None,
        optional: bool = False,
    ) -> TypeOptionContextBase:
        if optional and (self._old_value != -999):
            self._new_value = self._old_value
        else:
            self._new_value = new_value
        return self


class OptionContextStr(str, OptionContextBase[str]):
    """Context manager required by |OptionPropertyStr|."""

    def __new__(  # pylint: disable=unused-argument
        cls,
        value: str,
        set_value: Optional[Callable[[str], None]] = None,
    ) -> OptionContextStr:
        return super().__new__(cls, value)


class OptionContextPeriod(timetools.Period, OptionContextBase[timetools.Period]):
    """Context manager required by |OptionPropertyPeriod|."""

    _set_value: Tuple[Callable[[Optional[timetools.PeriodConstrArg]], None]]

    def __new__(  # pylint: disable=unused-argument
        cls,
        value: timetools.PeriodConstrArg,
        set_value: Optional[
            Callable[[Optional[timetools.PeriodConstrArg]], None]
        ] = None,
    ) -> OptionContextPeriod:
        return super().__new__(cls, value)

    def __call__(
        self: TypeOptionContextBase,
        new_value: Optional[timetools.PeriodConstrArg] = None,
    ) -> TypeOptionContextBase:
        self._new_value = new_value
        return self


class Options:
    """Singleton class for the general options available in the global |pub| module.

    Most options are simple True/False or 0/1 flags.

    You can change all options in two ways.  First, using the `with` statement makes
    sure the change is reverted after leaving the corresponding code block (even if an
    error occurs):

    >>> from hydpy import pub
    >>> pub.options.printprogress = 0
    >>> pub.options.printprogress
    0
    >>> with pub.options.printprogress(True):
    ...     print(pub.options.printprogress)
    1
    >>> pub.options.printprogress
    0

    Alternatively, you can change all options via simple assignments:

    >>> pub.options.printprogress = True
    >>> pub.options.printprogress
    1

    But then you might have to keep in mind to undo the change later:

    >>> pub.options.printprogress
    1
    >>> pub.options.printprogress = False
    >>> pub.options.printprogress
    0

    When using the `with` statement, you can pass nothing or |None|, which does not
    change the original setting and resets it after leaving the `with` block:

    >>> with pub.options.printprogress(None):
    ...     print(pub.options.printprogress)
    ...     pub.options.printprogress = True
    ...     print(pub.options.printprogress)
    0
    1
    >>> pub.options.printprogress
    0

    The delete statement restores the respective default setting:

    >>> del pub.options.printprogress
    >>> pub.options.printprogress
    1
    """

    checkseries = OptionPropertyBool(
        True,
        """True/False flag for raising an error when loading an input time series that 
        does not cover the whole initialisation period or contains |numpy.nan| 
        values.""",
    )
    ellipsis = _OptionPropertyEllipsis(
        -999,
        """Ellipsis points are used to shorten the string representations of iterable 
        HydPy objects containing many entries.  Set a value to define the maximum 
        number of entries before and behind ellipsis points.  Set it to zero to avoid 
        any ellipsis points.  Set it to -999 to rely on the default values of the 
        respective iterable objects.""",
    )
    parameterstep = OptionPropertyPeriod(
        timetools.Period("1d"),
        """The actual parameter time step size.  Change it by passing a |Period| object 
        or any valid |Period| constructor argument.  The default parameter step is one 
        day.
        
        >>> from hydpy import pub
        >>> pub.options.parameterstep
        Period("1d")
        """,
    )
    printprogress = OptionPropertyBool(
        True,
        """A True/False flag for printing information about the progress of some 
        processes to the standard output.""",
    )
    reprcomments = OptionPropertyBool(
        False,
        """A True/False flag for including comments into string representations.  So 
        far, this option affects the behaviour of a few implemented classes, only.""",
    )
    reprdigits = OptionPropertyInt(
        -1,
        """Required precision of string representations of floating point numbers, 
        defined as the minimum number of digits to be reproduced by the string 
        representation (see function |repr_|).""",
    )
    simulationstep = _OptionPropertySimulationstep(
        timetools.Period(),
        """The actual simulation time step size.  Change it by passing a |Period| 
        object or any valid |Period| constructor argument.  *HydPy* does not define a 
        default simulation step (indicated by an empty |Period| object).  
        
        Note that you cannot manually define the |Options.simulationstep| whenever it 
        is already available via attribute |Timegrids.stepsize| of the global  
        |Timegrids| object in module |pub| (`pub.timegrids`):
        
        >>> from hydpy import pub
        >>> pub.options.simulationstep
        Period()
        
        >>> pub.options.simulationstep = "1h"
        >>> pub.options.simulationstep
        Period("1h")
        
        >>> pub.timegrids = "2000-01-01", "2001-01-01", "1d"
        >>> pub.options.simulationstep
        Period("1d")
     
        >>> pub.options.simulationstep = "1s"
        >>> pub.options.simulationstep
        Period("1d")
        
        >>> del pub.timegrids
        >>> pub.options.simulationstep
        Period("1s")
        
        >>> del pub.options.simulationstep
        >>> pub.options.simulationstep
        Period()
        """,
    )
    trimvariables = OptionPropertyBool(
        True,
        """A True/False flag for enabling/disabling function |trim|.  Set it to |False| 
        only for good reasons.""",
    )
    usecython = OptionPropertyBool(
        True,
        """A True/False flag for applying cythonized models if possible, which are much 
        faster than pure Python models. """,
    )
    usedefaultvalues = OptionPropertyBool(
        False,
        """A True/False flag for initialising parameters with standard values.""",
    )
    utclongitude = OptionPropertyInt(
        15,
        """Longitude of the centre of the local time zone (see option
        |Options.utcoffset|).  Defaults to 15,  which corresponds to the central 
        meridian of UTC+01:00.""",
    )
    utcoffset = OptionPropertyInt(
        60,
        """Offset of your local time from UTC in minutes (see option 
        |Options.utclongitude|.  Defaults to 60, which corresponds to  UTC+01:00.""",
    )
    warnmissingcontrolfile = OptionPropertyBool(
        False,
        """A True/False flag for only raising a warning instead of an exception when a 
        necessary control file is missing.""",
    )
    warnmissingobsfile = OptionPropertyBool(
        True,
        """A True/False flag for raising a warning when a requested observation
        sequence demanded by a node instance is missing.""",
    )
    warnmissingsimfile = OptionPropertyBool(
        True,
        """A True/False flag for raising a warning when a requested simulation sequence 
        demanded by a node instance is missing.""",
    )
    warnsimulationstep = OptionPropertyBool(
        True,
        """A True/False flag for raising a warning when function |simulationstep| is
        called for the first time directly by the user.""",
    )
    warntrim = OptionPropertyBool(
        True,
        """A True/False flag for raising a warning when a |Variable| object trims its 
        value(s) not to violate certain boundaries.  To cope with the limited precision 
        of floating-point numbers, only those violations beyond a small tolerance value 
        are reported (see function |trim|).""",
    )

    def __repr__(self) -> str:
        type_ = type(self)
        lines = ["Options("]
        for option in itertools.chain(vars(type_).keys(), vars(self).keys()):
            if not option.startswith("_"):
                value = getattr(self, option)
                lines.append(f"    {option} -> {repr(value)}")
        lines.append(")")
        return "\n".join(lines)
