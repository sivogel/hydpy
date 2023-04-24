# -*- coding: utf-8 -*-
# pylint: disable=line-too-long, unused-wildcard-import
"""
The GR4J model (modèle du Génie Rural à 4 parametres Journalier) is a daily
lumped four-parameter rainfall-runoff model and belongs to the family of soil moisture
accounting models. It was published by :cite:t:`ref-Perrin2003` and is a modification
of GR3J. Here it is implemented according to :cite:t:`ref-airGR2017`. The model
contains two stores and has four parameters.

The following list summarises the main components of |grxjland_gr4j|:

 * Calculation of net precipitation/net rainfall
 * A production store influencing actual evaporation and percolation
 * Linear routing with two parallel unit hydrographs
 * Groundwater exchange
 * Non-linear routing store

The following figure cite:p:`ref-airGRManual` shows the general structure of HydPy
GrXJ-Land Version Gr4J:

.. image:: HydPy-GrXJ-Land_Version-Gr4J.png

.. _grxjland_gr4j_integration_tests:

Integration tests
=================

.. how_to_understand_integration_tests::

As integration test we use the example dataset L0123001 of the R-package airGR.

The integration test is performed over a period of 50 days with
a simulation step of one day:

>>> from hydpy import pub
>>> pub.timegrids = '01.01.1990', '20.02.1990', '1d'

Prepare the model instance and build the connections to element `land`
and node `outlet`:

>>> from hydpy.models.grxjland_gr4j import *
>>> from hydpy import pub
>>> pub.options.reprdigits = 6
>>> ret = pub.options.printprogress(False)
>>> parameterstep('1d')
>>> from hydpy import Node, Element
>>> outlet = Node('outlet')
>>> land = Element('land', outlets=outlet)
>>> land.model = model

All tests are performed using a lumped basin with a size of
360 km²:

>>> area(360.0)

Initialize a test function object, which prepares and runs the tests
and prints their results for the given sequences:

>>> from hydpy import IntegrationTest
>>> IntegrationTest.plotting_options.height = 900
>>> IntegrationTest.plotting_options.activated=(
...     inputs.e, inputs.p, fluxes.qt)
>>> test = IntegrationTest(land)
>>> test.dateformat = '%d.%m.'

.. _grxjland_gr4j_ex1:

Example 1
_____________

Set control parameters:

>>> x1(257.238)
>>> x2(1.012)
>>> x3(88.235)
>>> x4(2.208)

Set initial storage levels: production store 30% filled, routing store 50% filled. log.sequences empty


>>> test.inits = ((states.s, 0.3 * x1),
...               (states.r, 0.5 * x3),
...               (logs.quh1, [0.0, 0.0, 0.0]),
...               (logs.quh2, [0.0, 0.0, 0.0, 0.0, 0.0]))

Input sequences |P| and |E|:

>>> inputs.p.series = (
...     0.0,  9.3,  3.2,  7.3,  0.0,  0.0,  0.0,  0.0,  0.1,  0.2,  2.9,  0.2,  0.0,  0.0,  0.0,
...     3.3,  4.6,  0.8,  1.8,  1.1,  0.0,  5.0, 13.1, 14.6,  4.0,  0.8,  0.1,  3.3,  7.7, 10.3,
...     3.7, 15.3,  3.2,  2.7,  2.2,  8.0, 14.3,  6.3,  0.0,  5.9,  9.2,  6.1,  0.1,  0.0,  2.8,
...     10.6,  8.8,  7.2,  4.9,  1.8)
>>> inputs.e.series = (
...     0.3, 0.4, 0.4, 0.3, 0.1, 0.1, 0.1, 0.2, 0.2, 0.3, 0.3, 0.2, 0.2, 0.2, 0.2, 0.3, 0.3, 0.2, 0.2,
...     0.3, 0.2, 0.2, 0.3, 0.6, 0.4, 0.4, 0.4, 0.5, 0.4, 0.3, 0.3, 0.5, 0.5, 0.3, 0.3, 0.4, 0.4, 0.3,
...     0.2, 0.1, 0.1, 0.0, 0.1, 0.1, 0.0, 0.2, 0.9, 0.9, 0.5, 0.9)

Run Integration test

.. integration-test::

    >>> derived.uh1.update()
    >>> derived.uh2.update()
    >>> test.reset_inits()
    >>> conditions = sequences.conditions

    >>> test("grxjland_gr4j_ex1")
    |   date |    p |   e |  en |   pn |        ps |       es |       ae |       pr |    pruh1 |    pruh2 |     perc |       q9 |       q1 |        f |       qr |       qd |       qt |          s |         r |    outlet |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |  0.0 | 0.3 | 0.3 |  0.0 |       0.0 | 0.152875 | 0.152875 | 0.006036 | 0.005433 | 0.000604 | 0.006036 |  0.00075 | 0.000042 | 0.089449 | 0.670218 | 0.089491 | 0.759709 |  77.012489 | 43.537481 |  3.165453 |
    | 02.01. |  9.3 | 0.4 | 0.0 |  8.9 |  8.016066 |      0.0 |      0.4 | 0.893833 | 0.804449 | 0.089383 | 0.009898 | 0.114538 | 0.006363 |   0.0854 | 0.636315 | 0.091763 | 0.728078 |  85.018656 | 43.101104 |  3.033659 |
    | 03.01. |  3.2 | 0.4 | 0.0 |  2.8 |  2.485106 |      0.0 |      0.4 | 0.326319 | 0.293687 | 0.032632 | 0.011425 | 0.558854 |  0.03125 | 0.082442 | 0.636667 | 0.113691 | 0.750358 |  87.492337 | 43.105732 |  3.126493 |
    | 04.01. |  7.3 | 0.3 | 0.0 |  7.0 |  6.131951 |      0.0 |      0.3 | 0.884068 | 0.795661 | 0.088407 | 0.016019 | 0.474904 | 0.056451 | 0.082473 | 0.631081 | 0.138923 | 0.770004 |   93.60827 | 43.032028 |  3.208351 |
    | 05.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.059523 | 0.059523 | 0.015954 | 0.014359 | 0.001595 | 0.015954 | 0.577812 | 0.057078 |  0.08198 | 0.633099 | 0.139058 | 0.772158 |  93.532793 | 43.058721 |  3.217323 |
    | 06.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.059485 | 0.059485 |  0.01589 | 0.014301 | 0.001589 |  0.01589 |  0.18556 | 0.045765 | 0.082158 | 0.607783 | 0.127923 | 0.735706 |  93.457417 | 42.718655 |  3.065442 |
    | 07.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.059448 | 0.059448 | 0.015826 | 0.014243 | 0.001583 | 0.015826 | 0.014306 | 0.015459 |  0.07991 |  0.57353 | 0.095368 | 0.668898 |  93.382143 | 42.239341 |  2.787074 |
    | 08.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.118792 | 0.118792 | 0.015712 | 0.014141 | 0.001571 | 0.015712 | 0.014242 | 0.002256 | 0.076815 | 0.542728 | 0.079071 | 0.621799 |  93.247639 |  41.78767 |   2.59083 |
    | 09.01. |  0.1 | 0.2 | 0.1 |  0.0 |       0.0 | 0.059344 | 0.159344 | 0.015649 | 0.014084 | 0.001565 | 0.015649 | 0.014156 | 0.001579 | 0.073979 | 0.514894 | 0.075557 | 0.590452 |  93.172646 |  41.36091 |  2.460215 |
    | 10.01. |  0.2 | 0.3 | 0.1 |  0.0 |       0.0 | 0.059307 | 0.259307 | 0.015586 | 0.014028 | 0.001559 | 0.015586 | 0.014089 |  0.00157 | 0.071368 |  0.48963 | 0.072938 | 0.562568 |  93.097752 | 40.956737 |  2.344032 |
    | 11.01. |  2.9 | 0.3 | 0.0 |  2.6 |  2.251138 |      0.0 |      0.3 | 0.366411 |  0.32977 | 0.036641 | 0.017549 | 0.057625 | 0.003985 | 0.068957 | 0.469031 | 0.072942 | 0.541973 |  95.331342 | 40.614288 |  2.258219 |
    | 12.01. |  0.2 | 0.2 | 0.0 |  0.0 |       0.0 |      0.0 |      0.2 | 0.017533 | 0.015779 | 0.001753 | 0.017533 | 0.217237 | 0.012849 |  0.06696 | 0.458806 | 0.079809 | 0.538615 |  95.313809 | 40.439679 |  2.244229 |
    | 13.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.120694 | 0.120694 | 0.017406 | 0.015665 | 0.001741 | 0.017406 | 0.084569 | 0.017242 | 0.065958 | 0.442139 | 0.083199 | 0.525338 |  95.175709 | 40.148066 |  2.188908 |
    | 14.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.120559 | 0.120559 |  0.01728 | 0.015552 | 0.001728 |  0.01728 | 0.015675 | 0.007222 | 0.064308 | 0.423165 |  0.07153 | 0.494695 |   95.03787 | 39.804884 |  2.061229 |
    | 15.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.120424 | 0.120424 | 0.017156 |  0.01544 | 0.001716 | 0.017156 | 0.015562 | 0.002006 | 0.062404 | 0.405675 |  0.06441 | 0.470085 |  94.900291 | 39.477175 |  1.958689 |
    | 16.01. |  3.3 | 0.3 | 0.0 |  3.0 |  2.580474 |      0.0 |      0.3 | 0.439125 | 0.395213 | 0.043913 |   0.0196 | 0.067888 | 0.004638 | 0.060625 | 0.392045 | 0.065262 | 0.457308 |  97.461166 | 39.213642 |  1.905449 |
    | 17.01. |  4.6 | 0.3 | 0.0 |  4.3 |  3.659234 |      0.0 |      0.3 | 0.664306 | 0.597876 | 0.066431 |  0.02354 | 0.339968 | 0.019747 |  0.05922 | 0.392392 | 0.078967 | 0.471359 | 101.096859 | 39.220437 |  1.963996 |
    | 18.01. |  0.8 | 0.2 | 0.0 |  0.6 |  0.506861 |      0.0 |      0.2 | 0.117247 | 0.105522 | 0.011725 | 0.024108 | 0.485502 |  0.04198 | 0.059256 | 0.399845 | 0.101236 | 0.501081 | 101.579612 |  39.36535 |  2.087837 |
    | 19.01. |  1.8 | 0.2 | 0.0 |  1.6 |  1.347178 |      0.0 |      0.2 |  0.27854 | 0.250686 | 0.027854 | 0.025718 | 0.233451 | 0.042152 | 0.060026 | 0.394631 | 0.102177 | 0.496808 | 102.901072 | 39.264196 |  2.070032 |
    | 20.01. |  1.1 | 0.3 | 0.0 |  0.8 |  0.671148 |      0.0 |      0.3 | 0.155386 | 0.139847 | 0.015539 | 0.026534 | 0.203576 | 0.026007 | 0.059488 | 0.388254 | 0.085495 | 0.473749 | 103.545686 | 39.139005 |  1.973955 |
    | 21.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.128546 | 0.128546 | 0.026336 | 0.023703 | 0.002634 | 0.026336 | 0.148103 |  0.01992 | 0.058826 | 0.379599 | 0.078747 | 0.458345 | 103.390804 | 38.966336 |  1.909771 |
    | 22.01. |  5.0 | 0.2 | 0.0 |  4.8 |  3.994165 |      0.0 |      0.2 | 0.837623 | 0.753861 | 0.083762 | 0.031788 | 0.149944 | 0.018003 | 0.057923 |  0.37154 | 0.075926 | 0.447467 | 107.353181 | 38.802663 |  1.864445 |
    | 23.01. | 13.1 | 0.3 | 0.0 | 12.8 | 10.347284 |      0.0 |      0.3 | 2.502985 | 2.252686 | 0.250298 | 0.050269 | 0.800756 | 0.048023 | 0.057076 | 0.394712 | 0.105099 | 0.499811 | 117.650196 | 39.265783 |  2.082546 |
    | 24.01. | 14.6 | 0.6 | 0.0 | 14.0 | 10.792227 |      0.0 |      0.6 | 3.285533 |  2.95698 | 0.328553 |  0.07776 | 2.021465 | 0.140924 | 0.059496 | 0.483909 |  0.20042 | 0.684329 | 128.364663 | 40.862836 |   2.85137 |
    | 25.01. |  4.0 | 0.4 | 0.0 |  3.6 |  2.684632 |      0.0 |      0.4 | 1.001334 | 0.901201 | 0.100133 | 0.085967 | 2.518868 | 0.237037 | 0.068405 | 0.616263 | 0.305442 | 0.921704 | 130.963328 | 42.833846 |  3.840435 |
    | 26.01. |  0.8 | 0.4 | 0.0 |  0.4 |  0.296087 |      0.0 |      0.4 |  0.19057 | 0.171513 | 0.019057 | 0.086657 | 1.250964 | 0.219605 | 0.080666 | 0.667119 | 0.300271 |  0.96739 | 131.172758 | 43.498357 |  4.030791 |
    | 27.01. |  0.1 | 0.4 | 0.3 |  0.0 |       0.0 | 0.227818 | 0.327818 | 0.085625 | 0.077063 | 0.008563 | 0.085625 | 0.318374 | 0.104767 | 0.085132 | 0.648016 | 0.189898 | 0.837914 | 130.859314 | 43.253847 |   3.49131 |
    | 28.01. |  3.3 | 0.5 | 0.0 |  2.8 |  2.063892 |      0.0 |      0.5 |  0.82839 | 0.745551 | 0.082839 | 0.092282 | 0.190038 | 0.035197 | 0.083469 | 0.621605 | 0.118666 | 0.740271 | 132.830924 | 42.905748 |  3.084463 |
    | 29.01. |  7.7 | 0.4 | 0.0 |  7.3 |  5.274803 |      0.0 |      0.4 | 2.136896 | 1.923206 |  0.21369 | 0.111699 | 0.761626 | 0.048947 | 0.081141 | 0.637099 | 0.130088 | 0.767187 | 137.994028 | 43.111416 |  3.196613 |
    | 30.01. | 10.3 | 0.3 | 0.0 | 10.0 |  6.973334 |      0.0 |      0.3 |  3.16895 | 2.852055 | 0.316895 | 0.142283 | 1.793361 |   0.1289 | 0.082511 | 0.729464 | 0.211411 | 0.940874 | 144.825078 | 44.257825 |  3.920309 |
    | 31.01. |  3.7 | 0.3 | 0.0 |  3.4 |  2.305017 |      0.0 |      0.3 | 1.248178 |  1.12336 | 0.124818 | 0.153195 | 2.409886 | 0.218607 | 0.090449 | 0.878946 | 0.309056 | 1.188002 |   146.9769 | 45.879214 |  4.950008 |
    | 01.02. | 15.3 | 0.5 | 0.0 | 14.8 |  9.640855 |      0.0 |      0.5 | 5.368374 | 4.831537 | 0.536837 | 0.209229 | 2.014047 | 0.252335 | 0.102587 |  0.99654 | 0.354923 | 1.351463 | 156.408526 | 46.999308 |  5.631095 |
    | 02.02. |  3.2 | 0.5 | 0.0 |  2.7 |  1.690954 |      0.0 |      0.5 | 1.228334 | 1.105501 | 0.122833 | 0.219288 | 3.504616 | 0.287945 | 0.111624 | 1.284427 | 0.399569 | 1.683996 | 157.880192 | 49.331121 |  7.016651 |
    | 03.02. |  2.7 | 0.3 | 0.0 |  2.4 |  1.487382 |      0.0 |      0.3 | 1.140817 | 1.026735 | 0.114082 | 0.228199 | 1.911124 | 0.308222 | 0.132239 | 1.378427 | 0.440462 | 1.818889 | 159.139375 | 49.996057 |  7.578702 |
    | 04.02. |  2.2 | 0.3 | 0.0 |  1.9 |   1.16747 |      0.0 |      0.3 | 0.967513 | 0.870762 | 0.096751 | 0.234983 | 1.022465 | 0.183223 | 0.138584 | 1.350994 | 0.321807 | 1.672801 | 160.071862 | 49.806111 |  6.970004 |
    | 05.02. |  8.0 | 0.4 | 0.0 |  7.6 |  4.571734 |      0.0 |      0.4 |  3.29669 | 2.967021 | 0.329669 | 0.268424 | 1.194307 | 0.128022 |  0.13675 | 1.348499 | 0.264772 |  1.61327 | 164.375172 | 49.788669 |   6.72196 |
    | 06.02. | 14.3 | 0.4 | 0.0 | 13.9 |  7.942363 |      0.0 |      0.4 | 6.294452 | 5.665006 | 0.629445 | 0.336815 |  2.88009 | 0.211302 | 0.136582 | 1.569491 | 0.347884 | 1.917375 |  171.98072 |  51.23585 |  7.989064 |
    | 07.02. |  6.3 | 0.3 | 0.0 |  6.0 |  3.266581 |      0.0 |      0.3 | 3.099733 | 2.789759 | 0.309973 | 0.366314 | 4.676893 | 0.386439 | 0.150989 | 2.076895 | 0.537429 | 2.614323 | 174.880987 | 53.986838 | 10.893014 |
    | 08.02. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.179455 | 0.179455 | 0.360668 | 0.324602 | 0.036067 | 0.360668 | 3.079531 | 0.434647 |  0.18132 | 2.287879 | 0.615967 | 2.903846 | 174.340864 |  54.95981 | 12.099357 |
    | 09.02. |  5.9 | 0.1 | 0.0 |  5.8 |  3.088152 |      0.0 |      0.1 | 3.101436 | 2.791292 | 0.310144 | 0.389587 | 1.205298 | 0.272248 | 0.193017 | 2.127981 | 0.465265 | 2.593245 | 177.039429 | 54.230144 | 10.805188 |
    | 10.02. |  9.2 | 0.1 | 0.0 |  9.1 |  4.673919 |      0.0 |      0.1 | 4.864791 | 4.378311 | 0.486479 |  0.43871 | 2.469831 | 0.202813 | 0.184196 | 2.221524 | 0.387009 | 2.608533 | 181.274638 | 54.662647 | 10.868888 |
    | 11.02. |  6.1 | 0.0 | 0.0 |  6.1 |  3.019732 |      0.0 |      0.0 | 3.550868 | 3.195781 | 0.355087 |   0.4706 | 3.867308 | 0.326898 | 0.189389 | 2.571137 | 0.516287 | 3.087424 |  183.82377 | 56.148207 | 12.864268 |
    | 12.02. |  0.1 | 0.1 | 0.0 |  0.0 |       0.0 |      0.0 |      0.1 | 0.464652 | 0.418187 | 0.046465 | 0.464652 | 3.071495 | 0.382728 | 0.208024 | 2.716044 | 0.590752 | 3.306796 | 183.359118 | 56.711683 | 13.778317 |
    | 13.02. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.091741 | 0.091741 | 0.457698 | 0.411928 |  0.04577 | 0.457698 | 1.025984 | 0.254821 | 0.215423 | 2.420694 | 0.470244 | 2.890938 | 182.809679 | 55.532396 | 12.045576 |
    | 14.02. |  2.8 | 0.0 | 0.0 |  2.8 |  1.375188 |      0.0 |      0.0 | 1.894022 |  1.70462 | 0.189402 | 0.469211 | 0.591742 | 0.107942 | 0.200147 | 2.122062 | 0.308089 | 2.430152 | 183.715656 | 54.202222 | 10.125632 |
    | 15.02. | 10.6 | 0.2 | 0.0 | 10.4 |   4.94975 |      0.0 |      0.2 | 5.979038 | 5.381134 | 0.597904 | 0.528788 | 1.928852 | 0.132535 | 0.183864 |  2.12043 |   0.3164 |  2.43683 | 188.136618 | 54.194509 | 10.153457 |
    | 16.02. |  8.8 | 0.9 | 0.0 |  7.9 |  3.592434 |      0.0 |      0.9 | 4.880438 | 4.392395 | 0.488044 | 0.572872 | 4.439006 | 0.317665 | 0.183773 | 2.590836 | 0.501438 | 3.092274 |  191.15618 | 56.226451 | 12.884474 |
    | 17.02. |  7.2 | 0.9 | 0.0 |  6.3 |  2.770092 |      0.0 |      0.9 | 4.136157 | 3.722541 | 0.413616 | 0.606248 | 4.516594 | 0.481497 |  0.20904 | 3.047331 | 0.690537 | 3.737868 | 193.320023 | 57.904754 | 15.574451 |
    | 18.02. |  4.9 | 0.5 | 0.0 |  4.4 |  1.890459 |      0.0 |      0.5 |    3.136 |   2.8224 |   0.3136 | 0.626459 | 3.745073 | 0.467026 | 0.231706 | 3.262692 | 0.698732 | 3.961424 | 194.584023 |  58.61884 | 16.505933 |
    | 19.02. |  1.8 | 0.9 | 0.0 |  0.9 |  0.384007 |      0.0 |      0.9 | 1.138596 | 1.024736 |  0.11386 | 0.622603 | 2.771502 | 0.373883 | 0.241862 | 3.203911 | 0.615745 | 3.819656 | 194.345427 | 58.428293 | 15.915234 |


.. _grxjland_gr4j_ex2:

Example 2
_____________

In the second example we start from empty storages:

>>> test.inits = ((states.s, 0),
...               (states.r, 0),
...               (logs.quh1, [0.0, 0.0, 0.0]),
...               (logs.quh2, [0.0, 0.0, 0.0, 0.0, 0.0]))

.. integration-test::

    >>> test("grxjland_gr4j_ex2")
    |   date |    p |   e |  en |   pn |        ps |       es |       ae |       pr |    pruh1 |    pruh2 |     perc |       q9 |       q1 |        f |       qr |       qd |       qt |          s |         r |   outlet |
    ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |  0.0 | 0.3 | 0.3 |  0.0 |       0.0 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |        0.0 |       0.0 |      0.0 |
    | 02.01. |  9.3 | 0.4 | 0.0 |  8.9 |   8.89645 |      0.0 |      0.4 |  0.00355 | 0.003195 | 0.000355 |      0.0 | 0.000441 | 0.000024 |      0.0 |      0.0 | 0.000024 | 0.000024 |    8.89645 |  0.000441 | 0.000102 |
    | 03.01. |  3.2 | 0.4 | 0.0 |  2.8 |  2.795488 |      0.0 |      0.4 | 0.004512 | 0.004061 | 0.000451 |      0.0 | 0.002614 | 0.000145 |      0.0 |      0.0 | 0.000145 | 0.000145 |  11.691938 |  0.003055 | 0.000605 |
    | 04.01. |  7.3 | 0.3 | 0.0 |  7.0 |   6.97519 |      0.0 |      0.3 | 0.024815 | 0.022333 | 0.002481 | 0.000005 | 0.006394 | 0.000474 |      0.0 |      0.0 | 0.000474 | 0.000474 |  18.667123 |  0.009449 | 0.001976 |
    | 05.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.013982 | 0.013982 | 0.000005 | 0.000005 | 0.000001 | 0.000005 | 0.015247 | 0.001054 |      0.0 |      0.0 | 0.001054 | 0.001054 |  18.653136 |  0.024696 | 0.004392 |
    | 06.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.013972 | 0.013972 | 0.000005 | 0.000005 | 0.000001 | 0.000005 | 0.004898 | 0.001178 |      0.0 |      0.0 | 0.001178 | 0.001178 |  18.639159 |  0.029593 | 0.004907 |
    | 07.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.013962 | 0.013962 | 0.000005 | 0.000004 |      0.0 | 0.000005 | 0.000005 | 0.000393 |      0.0 |      0.0 | 0.000393 | 0.000393 |  18.625193 |  0.029598 | 0.001639 |
    | 08.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.027893 | 0.027893 | 0.000005 | 0.000004 |      0.0 | 0.000005 | 0.000004 |  0.00002 |      0.0 |      0.0 |  0.00002 |  0.00002 |  18.597295 |  0.029602 | 0.000082 |
    | 09.01. |  0.1 | 0.2 | 0.1 |  0.0 |       0.0 | 0.013932 | 0.113932 | 0.000005 | 0.000004 |      0.0 | 0.000005 | 0.000004 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |  18.583358 |  0.029607 | 0.000002 |
    | 10.01. |  0.2 | 0.3 | 0.1 |  0.0 |       0.0 | 0.013921 | 0.213921 | 0.000005 | 0.000004 |      0.0 | 0.000005 | 0.000004 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |  18.569432 |  0.029611 | 0.000002 |
    | 11.01. |  2.9 | 0.3 | 0.0 |  2.6 |  2.584477 |      0.0 |      0.3 | 0.015532 | 0.013979 | 0.001553 | 0.000009 | 0.001933 | 0.000108 |      0.0 |      0.0 | 0.000108 | 0.000108 |    21.1539 |  0.031545 | 0.000449 |
    | 12.01. |  0.2 | 0.2 | 0.0 |  0.0 |       0.0 |      0.0 |      0.2 | 0.000009 | 0.000008 | 0.000001 | 0.000009 | 0.008988 |   0.0005 |      0.0 |      0.0 |   0.0005 |   0.0005 |   21.15389 |  0.040533 | 0.002082 |
    | 13.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.031519 | 0.031519 | 0.000009 | 0.000008 | 0.000001 | 0.000009 |  0.00307 | 0.000691 |      0.0 |      0.0 | 0.000691 | 0.000691 |  21.122362 |  0.043603 | 0.002881 |
    | 14.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.031474 | 0.031474 | 0.000009 | 0.000008 | 0.000001 | 0.000009 | 0.000008 | 0.000245 |      0.0 |      0.0 | 0.000245 | 0.000245 |  21.090879 |  0.043611 | 0.001019 |
    | 15.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.031429 | 0.031429 | 0.000009 | 0.000008 | 0.000001 | 0.000009 | 0.000008 | 0.000013 |      0.0 |      0.0 | 0.000013 | 0.000013 |  21.059441 |  0.043619 | 0.000054 |
    | 16.01. |  3.3 | 0.3 | 0.0 |  3.0 |  2.976916 |      0.0 |      0.3 | 0.023102 | 0.020792 |  0.00231 | 0.000018 | 0.002877 |  0.00016 |      0.0 |      0.0 |  0.00016 |  0.00016 |  24.036339 |  0.046497 | 0.000668 |
    | 17.01. |  4.6 | 0.3 | 0.0 |  4.3 |  4.255413 |      0.0 |      0.3 | 0.044627 | 0.040164 | 0.004463 |  0.00004 | 0.018912 | 0.001051 |      0.0 |      0.0 | 0.001051 | 0.001051 |  28.291712 |  0.065408 |  0.00438 |
    | 18.01. |  0.8 | 0.2 | 0.0 |  0.6 |  0.592589 |      0.0 |      0.2 | 0.007456 |  0.00671 | 0.000746 | 0.000045 | 0.031301 | 0.002514 |      0.0 |      0.0 | 0.002514 | 0.002514 |  28.884256 |  0.096709 | 0.010474 |
    | 19.01. |  1.8 | 0.2 | 0.0 |  1.6 |  1.578704 |      0.0 |      0.2 | 0.021354 | 0.019219 | 0.002135 | 0.000058 | 0.015768 | 0.002735 |      0.0 |      0.0 | 0.002735 | 0.002735 |  30.462902 |  0.112477 | 0.011396 |
    | 20.01. |  1.1 | 0.3 | 0.0 |  0.8 |  0.788488 |      0.0 |      0.3 | 0.011579 | 0.010421 | 0.001158 | 0.000066 | 0.015263 | 0.001816 |      0.0 |      0.0 | 0.001816 | 0.001816 |  31.251323 |   0.12774 | 0.007568 |
    | 21.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.045612 | 0.045612 | 0.000066 | 0.000059 | 0.000007 | 0.000066 | 0.010918 | 0.001474 |      0.0 |      0.0 | 0.001474 | 0.001474 |  31.205645 |  0.138659 | 0.006142 |
    | 22.01. |  5.0 | 0.2 | 0.0 |  4.8 |  4.718135 |      0.0 |      0.2 | 0.081999 | 0.073799 |   0.0082 | 0.000133 | 0.012509 | 0.001424 |      0.0 |      0.0 | 0.001424 | 0.001424 |  35.923646 |  0.151168 | 0.005934 |
    | 23.01. | 13.1 | 0.3 | 0.0 | 12.8 | 12.453552 |      0.0 |      0.3 | 0.347038 | 0.312335 | 0.034704 |  0.00059 | 0.090567 | 0.005232 |      0.0 |      0.0 | 0.005232 | 0.005232 |  48.376608 |  0.241735 |   0.0218 |
    | 24.01. | 14.6 | 0.6 | 0.0 | 14.0 | 13.354986 |      0.0 |      0.6 | 0.647011 |  0.58231 | 0.064701 | 0.001997 | 0.297331 | 0.019278 |      0.0 |      0.0 | 0.019278 | 0.019278 |  61.729597 |  0.539066 | 0.080325 |
    | 25.01. |  4.0 | 0.4 | 0.0 |  3.6 |  3.381115 |      0.0 |      0.4 | 0.221492 | 0.199343 | 0.022149 | 0.002607 | 0.470285 | 0.039051 |      0.0 |      0.0 | 0.039051 | 0.039051 |  65.108105 |  1.009351 | 0.162713 |
    | 26.01. |  0.8 | 0.4 | 0.0 |  0.4 |  0.374228 |      0.0 |      0.4 | 0.028454 | 0.025609 | 0.002845 | 0.002682 | 0.259281 | 0.041611 |      0.0 |      0.0 | 0.041611 | 0.041611 |  65.479651 |  1.268632 |  0.17338 |
    | 27.01. |  0.1 | 0.4 | 0.3 |  0.0 |       0.0 | 0.133175 | 0.233175 | 0.002654 | 0.002389 | 0.000265 | 0.002654 | 0.060474 |  0.02121 |      0.0 |      0.0 | 0.021211 | 0.021211 |  65.343822 |  1.329107 | 0.088378 |
    | 28.01. |  3.3 | 0.5 | 0.0 |  2.8 |     2.612 |      0.0 |      0.5 | 0.191228 | 0.172105 | 0.019123 | 0.003228 | 0.030905 | 0.006646 |      0.0 |      0.0 | 0.006647 | 0.006647 |  67.952594 |  1.360012 | 0.027695 |
    | 29.01. |  7.7 | 0.4 | 0.0 |  7.3 |  6.738271 |      0.0 |      0.4 | 0.566907 | 0.510216 | 0.056691 | 0.005178 | 0.181587 | 0.010794 |      0.0 |      0.0 | 0.010795 | 0.010795 |  74.685687 |  1.541599 | 0.044979 |
    | 30.01. | 10.3 | 0.3 | 0.0 | 10.0 |  9.050338 |      0.0 |      0.3 | 0.958831 | 0.862948 | 0.095883 | 0.009169 | 0.484816 |  0.03341 | 0.000001 |      0.0 | 0.033411 | 0.033411 |  83.726856 |  2.026416 | 0.139212 |
    | 31.01. |  3.7 | 0.3 | 0.0 |  3.4 |  3.026608 |      0.0 |      0.3 | 0.384336 | 0.345902 | 0.038434 | 0.010944 |  0.71428 | 0.061696 | 0.000002 | 0.000001 | 0.061698 | 0.061698 |   86.74252 |  2.740697 | 0.257076 |
    | 01.02. | 15.3 | 0.5 | 0.0 | 14.8 |  12.85356 |      0.0 |      0.5 |  1.96826 | 1.771434 | 0.196826 | 0.021819 | 0.655983 | 0.077642 | 0.000005 | 0.000002 | 0.077647 | 0.077649 |   99.57426 |  3.396684 | 0.323537 |
    | 02.02. |  3.2 | 0.5 | 0.0 |  2.7 |  2.286063 |      0.0 |      0.5 |  0.43835 | 0.394515 | 0.043835 | 0.024414 | 1.268985 | 0.098875 | 0.000011 | 0.000009 | 0.098886 | 0.098895 |  101.83591 |  4.665671 | 0.412063 |
    | 03.02. |  2.7 | 0.3 | 0.0 |  2.4 |   2.01636 |      0.0 |      0.3 | 0.410535 | 0.369482 | 0.041054 | 0.026895 | 0.692787 |  0.11126 | 0.000034 | 0.000018 | 0.111295 | 0.111313 | 103.825375 |  5.358474 | 0.463804 |
    | 04.02. |  2.2 | 0.3 | 0.0 |  1.9 |  1.585723 |      0.0 |      0.3 | 0.343251 | 0.308926 | 0.034325 | 0.028974 | 0.366608 | 0.066258 | 0.000056 | 0.000025 | 0.066314 |  0.06634 | 105.382124 |  5.725113 | 0.276415 |
    | 05.02. |  8.0 | 0.4 | 0.0 |  7.6 |   6.24708 |      0.0 |      0.4 | 1.391501 | 1.252351 |  0.13915 | 0.038582 | 0.452425 | 0.047298 |  0.00007 | 0.000037 | 0.047369 | 0.047406 | 111.590623 |  6.177571 | 0.197524 |
    | 06.02. | 14.3 | 0.4 | 0.0 | 13.9 | 11.015301 |      0.0 |      0.4 | 2.946341 | 2.651707 | 0.294634 | 0.061643 | 1.238782 | 0.087113 | 0.000092 | 0.000093 | 0.087205 | 0.087298 | 122.544282 |  7.416353 |  0.36374 |
    | 07.02. |  6.3 | 0.3 | 0.0 |  6.0 |   4.58655 |      0.0 |      0.3 | 1.487325 | 1.338592 | 0.148732 | 0.073874 | 2.163801 | 0.172576 | 0.000174 | 0.000333 |  0.17275 | 0.173083 | 127.056957 |  9.579996 | 0.721179 |
    | 08.02. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 |  0.14872 |  0.14872 |  0.07323 | 0.065907 | 0.007323 |  0.07323 | 1.450658 | 0.201497 | 0.000427 | 0.000674 | 0.201924 | 0.202598 | 126.835007 | 11.030407 | 0.844156 |
    | 09.02. |  5.9 | 0.1 | 0.0 |  5.8 |   4.34095 |      0.0 |      0.1 | 1.545432 | 1.390889 | 0.154543 | 0.086382 | 0.527693 | 0.126511 | 0.000699 | 0.000851 |  0.12721 | 0.128061 | 131.089575 | 11.557948 | 0.533588 |
    | 10.02. |  9.2 | 0.1 | 0.0 |  9.1 |  6.614754 |      0.0 |      0.1 | 2.595333 |   2.3358 | 0.259533 | 0.110088 | 1.230977 |  0.09646 | 0.000823 | 0.001411 | 0.097283 | 0.098694 | 137.594241 | 12.788338 | 0.411226 |
    | 11.02. |  6.1 | 0.0 | 0.0 |  6.1 |    4.2994 |      0.0 |      0.0 | 1.928451 | 1.735606 | 0.192845 | 0.127851 | 2.045889 | 0.167778 | 0.001173 | 0.002962 | 0.168951 | 0.171913 |  141.76579 | 14.832437 | 0.716305 |
    | 12.02. |  0.1 | 0.1 | 0.0 |  0.0 |       0.0 |      0.0 |      0.1 | 0.127277 |  0.11455 | 0.012728 | 0.127277 | 1.643359 | 0.202641 | 0.001971 | 0.005007 | 0.204612 | 0.209618 | 141.638513 |  16.47276 |  0.87341 |
    | 13.02. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.079791 | 0.079791 | 0.126352 | 0.113717 | 0.012635 | 0.126352 | 0.469661 | 0.132688 | 0.002845 | 0.005758 | 0.135533 | 0.141291 |  141.43237 | 16.939509 | 0.588712 |
    | 14.02. |  2.8 | 0.0 | 0.0 |  2.8 |  1.941883 |      0.0 |      0.0 | 0.992767 |  0.89349 | 0.099277 |  0.13465 | 0.221539 | 0.048846 | 0.003138 | 0.006139 | 0.051984 | 0.058123 | 143.239603 | 17.158046 | 0.242179 |
    | 15.02. | 10.6 | 0.2 | 0.0 | 10.4 |  7.013585 |      0.0 |      0.2 | 3.556536 | 3.200882 | 0.355654 | 0.170121 | 1.041127 | 0.065561 | 0.003282 | 0.008233 | 0.068842 | 0.077075 | 150.083067 | 18.194222 | 0.321145 |
    | 16.02. |  8.8 | 0.9 | 0.0 |  7.9 |  5.117514 |      0.0 |      0.9 | 2.982443 | 2.684199 | 0.298244 | 0.199957 | 2.623935 | 0.181145 | 0.004029 | 0.016113 | 0.185175 | 0.201287 | 155.000624 | 20.806073 | 0.838697 |
    | 17.02. |  7.2 | 0.9 | 0.0 |  6.3 |  3.953493 |      0.0 |      0.9 | 2.571769 | 2.314592 | 0.257177 | 0.225262 | 2.746401 | 0.287518 | 0.006443 | 0.029838 | 0.293961 |   0.3238 | 158.728855 | 23.529079 | 1.349165 |
    | 18.02. |  4.9 | 0.5 | 0.0 |  4.4 |  2.695976 |      0.0 |      0.5 | 1.947291 | 1.752562 | 0.194729 | 0.243267 | 2.318003 | 0.285379 |  0.00991 | 0.047454 | 0.295289 | 0.342742 | 161.181564 | 25.809537 | 1.428093 |
    | 19.02. |  1.8 | 0.9 | 0.0 |  0.9 |  0.545454 |      0.0 |      0.9 | 0.600092 | 0.540083 | 0.060009 | 0.245546 | 1.708351 | 0.230702 | 0.013698 | 0.064859 |   0.2444 | 0.309259 | 161.481472 | 27.466728 |  1.28858 |


.. _grxjland_gr4j_ex3:

Example 3
_____________

In the third we start from empty storages and use a negative groundwater exchange
coefficient X2:

>>> x2(-1.012)

Run Integration test

.. integration-test::

    >>> test("grxjland_gr4j_ex3")
    |   date |    p |   e |  en |   pn |        ps |       es |       ae |       pr |    pruh1 |    pruh2 |     perc |       q9 |       q1 |         f |       qr |       qd |       qt |          s |         r |   outlet |
    -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    | 01.01. |  0.0 | 0.3 | 0.3 |  0.0 |       0.0 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |      0.0 |       0.0 |      0.0 |      0.0 |      0.0 |        0.0 |       0.0 |      0.0 |
    | 02.01. |  9.3 | 0.4 | 0.0 |  8.9 |   8.89645 |      0.0 |      0.4 |  0.00355 | 0.003195 | 0.000355 |      0.0 | 0.000441 | 0.000024 |       0.0 |      0.0 | 0.000024 | 0.000024 |    8.89645 |  0.000441 | 0.000102 |
    | 03.01. |  3.2 | 0.4 | 0.0 |  2.8 |  2.795488 |      0.0 |      0.4 | 0.004512 | 0.004061 | 0.000451 |      0.0 | 0.002614 | 0.000145 |       0.0 |      0.0 | 0.000145 | 0.000145 |  11.691938 |  0.003055 | 0.000605 |
    | 04.01. |  7.3 | 0.3 | 0.0 |  7.0 |   6.97519 |      0.0 |      0.3 | 0.024815 | 0.022333 | 0.002481 | 0.000005 | 0.006394 | 0.000474 |       0.0 |      0.0 | 0.000474 | 0.000474 |  18.667123 |  0.009449 | 0.001976 |
    | 05.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.013982 | 0.013982 | 0.000005 | 0.000005 | 0.000001 | 0.000005 | 0.015247 | 0.001054 |       0.0 |      0.0 | 0.001054 | 0.001054 |  18.653136 |  0.024696 | 0.004392 |
    | 06.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.013972 | 0.013972 | 0.000005 | 0.000005 | 0.000001 | 0.000005 | 0.004898 | 0.001178 |       0.0 |      0.0 | 0.001178 | 0.001178 |  18.639159 |  0.029593 | 0.004907 |
    | 07.01. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.013962 | 0.013962 | 0.000005 | 0.000004 |      0.0 | 0.000005 | 0.000005 | 0.000393 |       0.0 |      0.0 | 0.000393 | 0.000393 |  18.625193 |  0.029598 | 0.001639 |
    | 08.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.027893 | 0.027893 | 0.000005 | 0.000004 |      0.0 | 0.000005 | 0.000004 |  0.00002 |       0.0 |      0.0 |  0.00002 |  0.00002 |  18.597295 |  0.029602 | 0.000082 |
    | 09.01. |  0.1 | 0.2 | 0.1 |  0.0 |       0.0 | 0.013932 | 0.113932 | 0.000005 | 0.000004 |      0.0 | 0.000005 | 0.000004 |      0.0 |       0.0 |      0.0 |      0.0 |      0.0 |  18.583358 |  0.029607 | 0.000002 |
    | 10.01. |  0.2 | 0.3 | 0.1 |  0.0 |       0.0 | 0.013921 | 0.213921 | 0.000005 | 0.000004 |      0.0 | 0.000005 | 0.000004 |      0.0 |       0.0 |      0.0 |      0.0 |      0.0 |  18.569432 |  0.029611 | 0.000002 |
    | 11.01. |  2.9 | 0.3 | 0.0 |  2.6 |  2.584477 |      0.0 |      0.3 | 0.015532 | 0.013979 | 0.001553 | 0.000009 | 0.001933 | 0.000108 |       0.0 |      0.0 | 0.000108 | 0.000108 |    21.1539 |  0.031545 | 0.000449 |
    | 12.01. |  0.2 | 0.2 | 0.0 |  0.0 |       0.0 |      0.0 |      0.2 | 0.000009 | 0.000008 | 0.000001 | 0.000009 | 0.008988 |   0.0005 |       0.0 |      0.0 |   0.0005 |   0.0005 |   21.15389 |  0.040533 | 0.002082 |
    | 13.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.031519 | 0.031519 | 0.000009 | 0.000008 | 0.000001 | 0.000009 |  0.00307 | 0.000691 |       0.0 |      0.0 | 0.000691 | 0.000691 |  21.122362 |  0.043603 | 0.002881 |
    | 14.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.031474 | 0.031474 | 0.000009 | 0.000008 | 0.000001 | 0.000009 | 0.000008 | 0.000245 |       0.0 |      0.0 | 0.000245 | 0.000245 |  21.090879 |  0.043611 | 0.001019 |
    | 15.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.031429 | 0.031429 | 0.000009 | 0.000008 | 0.000001 | 0.000009 | 0.000008 | 0.000013 |       0.0 |      0.0 | 0.000013 | 0.000013 |  21.059441 |  0.043619 | 0.000054 |
    | 16.01. |  3.3 | 0.3 | 0.0 |  3.0 |  2.976916 |      0.0 |      0.3 | 0.023102 | 0.020792 |  0.00231 | 0.000018 | 0.002877 |  0.00016 |       0.0 |      0.0 |  0.00016 |  0.00016 |  24.036339 |  0.046497 | 0.000668 |
    | 17.01. |  4.6 | 0.3 | 0.0 |  4.3 |  4.255413 |      0.0 |      0.3 | 0.044627 | 0.040164 | 0.004463 |  0.00004 | 0.018912 | 0.001051 |       0.0 |      0.0 | 0.001051 | 0.001051 |  28.291712 |  0.065408 |  0.00438 |
    | 18.01. |  0.8 | 0.2 | 0.0 |  0.6 |  0.592589 |      0.0 |      0.2 | 0.007456 |  0.00671 | 0.000746 | 0.000045 | 0.031301 | 0.002514 |       0.0 |      0.0 | 0.002514 | 0.002514 |  28.884256 |  0.096709 | 0.010474 |
    | 19.01. |  1.8 | 0.2 | 0.0 |  1.6 |  1.578704 |      0.0 |      0.2 | 0.021354 | 0.019219 | 0.002135 | 0.000058 | 0.015768 | 0.002735 |       0.0 |      0.0 | 0.002735 | 0.002735 |  30.462902 |  0.112477 | 0.011396 |
    | 20.01. |  1.1 | 0.3 | 0.0 |  0.8 |  0.788488 |      0.0 |      0.3 | 0.011579 | 0.010421 | 0.001158 | 0.000066 | 0.015263 | 0.001816 |       0.0 |      0.0 | 0.001816 | 0.001816 |  31.251323 |   0.12774 | 0.007568 |
    | 21.01. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 | 0.045612 | 0.045612 | 0.000066 | 0.000059 | 0.000007 | 0.000066 | 0.010918 | 0.001474 |       0.0 |      0.0 | 0.001474 | 0.001474 |  31.205645 |  0.138659 | 0.006142 |
    | 22.01. |  5.0 | 0.2 | 0.0 |  4.8 |  4.718135 |      0.0 |      0.2 | 0.081999 | 0.073799 |   0.0082 | 0.000133 | 0.012509 | 0.001424 |       0.0 |      0.0 | 0.001424 | 0.001424 |  35.923646 |  0.151168 | 0.005934 |
    | 23.01. | 13.1 | 0.3 | 0.0 | 12.8 | 12.453552 |      0.0 |      0.3 | 0.347038 | 0.312335 | 0.034704 |  0.00059 | 0.090567 | 0.005232 |       0.0 |      0.0 | 0.005232 | 0.005232 |  48.376608 |  0.241735 |   0.0218 |
    | 24.01. | 14.6 | 0.6 | 0.0 | 14.0 | 13.354986 |      0.0 |      0.6 | 0.647011 |  0.58231 | 0.064701 | 0.001997 | 0.297331 | 0.019278 |       0.0 |      0.0 | 0.019278 | 0.019278 |  61.729597 |  0.539066 | 0.080325 |
    | 25.01. |  4.0 | 0.4 | 0.0 |  3.6 |  3.381115 |      0.0 |      0.4 | 0.221492 | 0.199343 | 0.022149 | 0.002607 | 0.470285 | 0.039051 |       0.0 |      0.0 | 0.039051 | 0.039051 |  65.108105 |  1.009351 | 0.162713 |
    | 26.01. |  0.8 | 0.4 | 0.0 |  0.4 |  0.374228 |      0.0 |      0.4 | 0.028454 | 0.025609 | 0.002845 | 0.002682 | 0.259281 | 0.041611 |       0.0 |      0.0 | 0.041611 | 0.041611 |  65.479651 |  1.268632 | 0.173379 |
    | 27.01. |  0.1 | 0.4 | 0.3 |  0.0 |       0.0 | 0.133175 | 0.233175 | 0.002654 | 0.002389 | 0.000265 | 0.002654 | 0.060474 |  0.02121 |       0.0 |      0.0 |  0.02121 |  0.02121 |  65.343822 |  1.329106 | 0.088375 |
    | 28.01. |  3.3 | 0.5 | 0.0 |  2.8 |     2.612 |      0.0 |      0.5 | 0.191228 | 0.172105 | 0.019123 | 0.003228 | 0.030905 | 0.006646 |       0.0 |      0.0 | 0.006646 | 0.006646 |  67.952594 |   1.36001 | 0.027691 |
    | 29.01. |  7.7 | 0.4 | 0.0 |  7.3 |  6.738271 |      0.0 |      0.4 | 0.566907 | 0.510216 | 0.056691 | 0.005178 | 0.181587 | 0.010794 |       0.0 |      0.0 | 0.010794 | 0.010794 |  74.685687 |  1.541597 | 0.044975 |
    | 30.01. | 10.3 | 0.3 | 0.0 | 10.0 |  9.050338 |      0.0 |      0.3 | 0.958831 | 0.862948 | 0.095883 | 0.009169 | 0.484816 |  0.03341 | -0.000001 |      0.0 | 0.033409 |  0.03341 |  83.726856 |  2.026411 | 0.139206 |
    | 31.01. |  3.7 | 0.3 | 0.0 |  3.4 |  3.026608 |      0.0 |      0.3 | 0.384336 | 0.345902 | 0.038434 | 0.010944 |  0.71428 | 0.061696 | -0.000002 | 0.000001 | 0.061694 | 0.061695 |   86.74252 |  2.740689 | 0.257061 |
    | 01.02. | 15.3 | 0.5 | 0.0 | 14.8 |  12.85356 |      0.0 |      0.5 |  1.96826 | 1.771434 | 0.196826 | 0.021819 | 0.655983 | 0.077642 | -0.000005 | 0.000002 | 0.077636 | 0.077638 |   99.57426 |  3.396665 | 0.323492 |
    | 02.02. |  3.2 | 0.5 | 0.0 |  2.7 |  2.286063 |      0.0 |      0.5 |  0.43835 | 0.394515 | 0.043835 | 0.024414 | 1.268985 | 0.098875 | -0.000011 | 0.000009 | 0.098863 | 0.098872 |  101.83591 |  4.665629 | 0.411968 |
    | 03.02. |  2.7 | 0.3 | 0.0 |  2.4 |   2.01636 |      0.0 |      0.3 | 0.410535 | 0.369482 | 0.041054 | 0.026895 | 0.692787 |  0.11126 | -0.000034 | 0.000018 | 0.111226 | 0.111244 | 103.825375 |  5.358364 | 0.463517 |
    | 04.02. |  2.2 | 0.3 | 0.0 |  1.9 |  1.585723 |      0.0 |      0.3 | 0.343251 | 0.308926 | 0.034325 | 0.028974 | 0.366608 | 0.066258 | -0.000056 | 0.000025 | 0.066203 | 0.066228 | 105.382124 |  5.724891 | 0.275949 |
    | 05.02. |  8.0 | 0.4 | 0.0 |  7.6 |   6.24708 |      0.0 |      0.4 | 1.391501 | 1.252351 |  0.13915 | 0.038582 | 0.452425 | 0.047298 |  -0.00007 | 0.000037 | 0.047228 | 0.047265 | 111.590623 |  6.177209 | 0.196937 |
    | 06.02. | 14.3 | 0.4 | 0.0 | 13.9 | 11.015301 |      0.0 |      0.4 | 2.946341 | 2.651707 | 0.294634 | 0.061643 | 1.238782 | 0.087113 | -0.000092 | 0.000093 | 0.087021 | 0.087114 | 122.544282 |  7.415806 | 0.362974 |
    | 07.02. |  6.3 | 0.3 | 0.0 |  6.0 |   4.58655 |      0.0 |      0.3 | 1.487325 | 1.338592 | 0.148732 | 0.073874 | 2.163801 | 0.172576 | -0.000174 | 0.000333 | 0.172402 | 0.172734 | 127.056957 |  9.579101 | 0.719727 |
    | 08.02. |  0.0 | 0.2 | 0.2 |  0.0 |       0.0 |  0.14872 |  0.14872 |  0.07323 | 0.065907 | 0.007323 |  0.07323 | 1.450658 | 0.201497 | -0.000427 | 0.000673 |  0.20107 | 0.201744 | 126.835007 | 11.028659 | 0.840598 |
    | 09.02. |  5.9 | 0.1 | 0.0 |  5.8 |   4.34095 |      0.0 |      0.1 | 1.545432 | 1.390889 | 0.154543 | 0.086382 | 0.527693 | 0.126511 | -0.000699 |  0.00085 | 0.125813 | 0.126662 | 131.089575 | 11.554804 | 0.527759 |
    | 10.02. |  9.2 | 0.1 | 0.0 |  9.1 |  6.614754 |      0.0 |      0.1 | 2.595333 |   2.3358 | 0.259533 | 0.110088 | 1.230977 |  0.09646 | -0.000822 | 0.001408 | 0.095637 | 0.097046 | 137.594241 |  12.78355 | 0.404358 |
    | 11.02. |  6.1 | 0.0 | 0.0 |  6.1 |    4.2994 |      0.0 |      0.0 | 1.928451 | 1.735606 | 0.192845 | 0.127851 | 2.045889 | 0.167778 | -0.001171 | 0.002955 | 0.166606 | 0.169562 |  141.76579 | 14.825313 | 0.706508 |
    | 12.02. |  0.1 | 0.1 | 0.0 |  0.0 |       0.0 |      0.0 |      0.1 | 0.127277 |  0.11455 | 0.012728 | 0.127277 | 1.643359 | 0.202641 | -0.001968 |  0.00499 | 0.200673 | 0.205663 | 141.638513 | 16.461714 | 0.856929 |
    | 13.02. |  0.0 | 0.1 | 0.1 |  0.0 |       0.0 | 0.079791 | 0.079791 | 0.126352 | 0.113717 | 0.012635 | 0.126352 | 0.469661 | 0.132688 | -0.002839 | 0.005729 | 0.129849 | 0.135579 |  141.43237 | 16.922807 | 0.564911 |
    | 14.02. |  2.8 | 0.0 | 0.0 |  2.8 |  1.941883 |      0.0 |      0.0 | 0.992767 |  0.89349 | 0.099277 |  0.13465 | 0.221539 | 0.048846 | -0.003127 | 0.006098 |  0.04572 | 0.051818 | 143.239603 | 17.135121 | 0.215907 |
    | 15.02. | 10.6 | 0.2 | 0.0 | 10.4 |  7.013585 |      0.0 |      0.2 | 3.556536 | 3.200882 | 0.355654 | 0.170121 | 1.041127 | 0.065561 | -0.003266 | 0.008166 | 0.062295 | 0.070461 | 150.083067 | 18.164815 | 0.293587 |
    | 16.02. |  8.8 | 0.9 | 0.0 |  7.9 |  5.117514 |      0.0 |      0.9 | 2.982443 | 2.684199 | 0.298244 | 0.199957 | 2.623935 | 0.181145 | -0.004006 | 0.015969 | 0.177139 | 0.193108 | 155.000624 | 20.768775 | 0.804615 |
    | 17.02. |  7.2 | 0.9 | 0.0 |  6.3 |  3.953493 |      0.0 |      0.9 | 2.571769 | 2.314592 | 0.257177 | 0.225262 | 2.746401 | 0.287518 | -0.006403 | 0.029523 | 0.281115 | 0.310638 | 158.728855 |  23.47925 | 1.294326 |
    | 18.02. |  4.9 | 0.5 | 0.0 |  4.4 |  2.695976 |      0.0 |      0.5 | 1.947291 | 1.752562 | 0.194729 | 0.243267 | 2.318003 | 0.285379 | -0.009836 | 0.046821 | 0.275543 | 0.322364 | 161.181564 | 25.740595 | 1.343182 |
    | 19.02. |  1.8 | 0.9 | 0.0 |  0.9 |  0.545454 |      0.0 |      0.9 | 0.600092 | 0.540083 | 0.060009 | 0.245546 | 1.708351 | 0.230702 | -0.013571 | 0.063739 | 0.217131 |  0.28087 | 161.481472 | 27.371637 | 1.170292 |
"""

# import...
# ...from HydPy
from hydpy.exe.modelimports import *
from hydpy.core import modeltools

# ...from  grxjland
from hydpy.models.grxjland import grxjland_model


class Model(modeltools.AdHocModel):
    """GR4J version of GRxJ-Land (|grxjland_gr4j|)."""

    INLET_METHODS = ()
    RECEIVER_METHODS = ()
    RUN_METHODS = (
        grxjland_model.Calc_Pn_En_V1,
        grxjland_model.Calc_PS_V1,
        grxjland_model.Calc_Es_V1,
        grxjland_model.Update_S_V1,
        grxjland_model.Calc_Perc_V1,
        grxjland_model.Update_S_V2,
        grxjland_model.Calc_AE_V1,
        grxjland_model.Calc_Pr_V1,
        grxjland_model.Calc_PrUH1_PrUH2_V1,
        grxjland_model.Calc_Q9_V1,
        grxjland_model.Calc_Q1_V1,
        grxjland_model.Calc_F_V1,
        grxjland_model.Update_R_V1,
        grxjland_model.Calc_Qr_V1,
        grxjland_model.Update_R_V3,
        grxjland_model.Calc_Qd_V1,
        grxjland_model.Calc_Qt_V1,
    )
    ADD_METHODS = ()
    OUTLET_METHODS = (grxjland_model.Pass_Q_V1,)
    SENDER_METHODS = ()
    SUBMODELINTERFACES = ()
    SUBMODELS = ()


tester = Tester()
cythonizer = Cythonizer()
