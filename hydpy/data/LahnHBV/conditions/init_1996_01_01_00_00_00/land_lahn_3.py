# -*- coding: utf-8 -*-

from hydpy.models.hland_v1 import *

controlcheck(projectdir="lahnHBV", controldir="default")

ic(0.96064000000000005, 1.4211100000000001, 0.96121000000000001,
   1.4612099999999999, 0.96175999999999995, 1.4617599999999999,
   0.96231999999999995, 1.4623200000000001, 0.96286000000000005, 1.46286,
   0.96338999999999997, 1.46339, 1.4639200000000001, 1.46444)
sp(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
wc(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
sm(101.31247999999999, 97.224999999999994, 111.3861, 107.64977, 120.59559,
   117.26499, 129.01711, 126.04649999999999, 136.66663, 134.01408000000001,
   143.59799000000001, 141.24428, 147.75785999999999, 153.54052999999999)
uz(4.07665)
lz(7.52648)
quh(0.025239999999999999, 0.024240000000000001, 0.022669999999999999,
    0.020559999999999998, 0.01789, 0.014659999999999999,
    0.010970000000000001, 0.0076899999999999998, 0.0049899999999999996,
    0.0028700000000000002, 0.00134, 0.00038000000000000002,
    1.0000000000000001e-05, 0.0)
